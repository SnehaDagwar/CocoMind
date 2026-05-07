"""FastAPI routes for the CocoMind integrated MVP workflow."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, Body, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from src.audit.chain import export_for_rti, get_all_records, verify_chain, write_record
from src.models.auth import Role, User
from src.models.hitl import HITLDecision, OfficerDecision
from src.models.workflow import (
    BidderCreate,
    TenderCreate,
    UploadedDocument,
    WorkflowStatus,
)
from src.rbac.middleware import require_role
from src.workflow.fixtures import load_fixture_criteria
from src.workflow.jobs import generate_report_for_tender, run_evaluation_job
from src.workflow.store import (
    UPLOAD_DIR,
    add_document,
    create_bidder,
    create_job,
    create_tender,
    get_criteria,
    get_hitl_items,
    get_job,
    get_report,
    get_tender,
    get_vtm,
    list_bidders,
    list_documents,
    list_tenders,
    new_id,
    now_utc,
    resolve_hitl_item,
    save_bidder,
    save_criteria,
    save_tender,
    update_criterion,
)

app = FastAPI(
    title="CocoMind - CRPF Tender Evaluation Platform",
    description="AI-assisted tender evaluation with formal verification",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "version": "0.1.0"}


@app.post("/api/demo/login")
async def demo_login(role: Role = Body(..., embed=True)) -> dict[str, Any]:
    user = _demo_user(role)
    write_record("DEMO_LOGIN", {"user_id": user.user_id, "role": user.role.value})
    return {"user": user.model_dump(mode="json")}


@app.get("/api/me")
async def me(user: User = require_role(*list(Role))) -> dict[str, Any]:
    return {"user": user.model_dump(mode="json")}


@app.post("/api/tenders")
async def post_tender(
    payload: TenderCreate,
    user: User = require_role(Role.PROCUREMENT_OFFICER),
) -> dict[str, Any]:
    tender = create_tender(payload, user.user_id)
    write_record("TENDER_CREATED", {"tender_id": tender.tender_id, "user_id": user.user_id})
    return {"tender": tender.model_dump(mode="json")}


@app.get("/api/tenders")
async def get_tenders(user: User = require_role(*list(Role))) -> dict[str, Any]:
    return {"tenders": [tender.model_dump(mode="json") for tender in list_tenders()]}


@app.get("/api/tenders/{tender_id}")
async def get_tender_detail(tender_id: str, user: User = require_role(*list(Role))) -> dict[str, Any]:
    tender = _or_404(lambda: get_tender(tender_id), "Tender not found")
    return {
        "tender": tender.model_dump(mode="json"),
        "criteria": [criterion.model_dump(mode="json") for criterion in get_criteria(tender_id)],
        "bidders": [bidder.model_dump(mode="json") for bidder in list_bidders(tender_id)],
        "documents": [doc.model_dump(mode="json") for doc in list_documents(tender_id)],
    }


@app.post("/api/tenders/{tender_id}/nit")
async def upload_tender_document(
    tender_id: str,
    file: UploadFile = File(...),
    user: User = require_role(Role.PROCUREMENT_OFFICER),
) -> dict[str, Any]:
    tender = _or_404(lambda: get_tender(tender_id), "Tender not found")
    document = await _save_upload(tender_id, None, file)
    tender.nit_document_id = document.document_id
    tender.status = WorkflowStatus.TENDER_UPLOADED
    save_tender(tender)
    write_record(
        "NIT_UPLOADED",
        {"tender_id": tender_id, "document_id": document.document_id, "filename": file.filename},
    )
    return {"document": document.model_dump(mode="json"), "tender": tender.model_dump(mode="json")}


@app.post("/api/tenders/{tender_id}/criteria/extract")
async def extract_criteria(
    tender_id: str,
    user: User = require_role(Role.PROCUREMENT_OFFICER, Role.EVALUATOR),
) -> dict[str, Any]:
    tender = _or_404(lambda: get_tender(tender_id), "Tender not found")
    criteria = load_fixture_criteria()
    save_criteria(tender_id, criteria)
    tender.status = WorkflowStatus.CRITERIA_EXTRACTED
    save_tender(tender)
    write_record("CRITERIA_EXTRACTED", {"tender_id": tender_id, "count": len(criteria), "demo_backed": True})
    return {"criteria": [criterion.model_dump(mode="json") for criterion in criteria], "demo_backed": True}


@app.get("/api/tenders/{tender_id}/criteria")
async def list_criteria(tender_id: str, user: User = require_role(*list(Role))) -> dict[str, Any]:
    return {"criteria": [criterion.model_dump(mode="json") for criterion in get_criteria(tender_id)]}


@app.patch("/api/tenders/{tender_id}/criteria/{criterion_id}")
async def patch_criterion(
    tender_id: str,
    criterion_id: str,
    patch: dict[str, Any],
    user: User = require_role(Role.PROCUREMENT_OFFICER, Role.EVALUATOR),
) -> dict[str, Any]:
    criterion = _or_404(lambda: update_criterion(tender_id, criterion_id, patch), "Criterion not found")
    write_record("CRITERION_UPDATED", {"tender_id": tender_id, "criterion_id": criterion_id, "patch": patch})
    return {"criterion": criterion.model_dump(mode="json")}


@app.post("/api/tenders/{tender_id}/bids")
async def post_bidder(
    tender_id: str,
    payload: BidderCreate,
    user: User = require_role(Role.PROCUREMENT_OFFICER),
) -> dict[str, Any]:
    _or_404(lambda: get_tender(tender_id), "Tender not found")
    bidder = create_bidder(tender_id, payload)
    write_record("BIDDER_CREATED", {"tender_id": tender_id, "bid_id": bidder.bid_id})
    return {"bidder": bidder.model_dump(mode="json")}


@app.post("/api/tenders/{tender_id}/bids/{bid_id}/documents")
async def upload_bid_document(
    tender_id: str,
    bid_id: str,
    file: UploadFile = File(...),
    user: User = require_role(Role.PROCUREMENT_OFFICER),
) -> dict[str, Any]:
    tender = _or_404(lambda: get_tender(tender_id), "Tender not found")
    bidder = next((b for b in list_bidders(tender_id) if b.bid_id == bid_id), None)
    if bidder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bidder not found")
    document = await _save_upload(tender_id, bid_id, file)
    bidder.documents.append(document)
    save_bidder(bidder)
    tender.status = WorkflowStatus.BIDS_UPLOADED
    save_tender(tender)
    write_record("BID_DOCUMENT_UPLOADED", {"tender_id": tender_id, "bid_id": bid_id, "document_id": document.document_id})
    return {"document": document.model_dump(mode="json"), "tender": tender.model_dump(mode="json")}


@app.post("/api/tenders/{tender_id}/evaluation-jobs")
async def start_evaluation(
    tender_id: str,
    background_tasks: BackgroundTasks,
    user: User = require_role(Role.PROCUREMENT_OFFICER, Role.EVALUATOR),
) -> dict[str, Any]:
    _or_404(lambda: get_tender(tender_id), "Tender not found")
    if not get_criteria(tender_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Extract criteria before evaluation")
    job = create_job(tender_id)
    tender = get_tender(tender_id)
    tender.latest_job_id = job.job_id
    tender.status = WorkflowStatus.EVALUATING
    save_tender(tender)
    background_tasks.add_task(run_evaluation_job, job.job_id)
    return {"job": job.model_dump(mode="json")}


@app.get("/api/jobs/{job_id}")
async def get_evaluation_job(job_id: str, user: User = require_role(*list(Role))) -> dict[str, Any]:
    job = _or_404(lambda: get_job(job_id), "Job not found")
    return {"job": job.model_dump(mode="json")}


@app.get("/api/tenders/{tender_id}/vtm")
async def get_tender_vtm(tender_id: str, user: User = require_role(*list(Role))) -> dict[str, Any]:
    vtms = get_vtm(tender_id)
    return {
        "vtm": {bid_id: [row.model_dump(mode="json") for row in rows] for bid_id, rows in vtms.items()},
        "summary": _summary(vtms),
    }


@app.get("/api/tenders/{tender_id}/hitl")
async def get_tender_hitl(tender_id: str, user: User = require_role(Role.HITL_REVIEWER, Role.EVALUATOR, Role.AUDITOR)) -> dict[str, Any]:
    items = get_hitl_items(tender_id)
    return {"items": [item.model_dump(mode="json") for item in items]}


@app.post("/api/hitl/{item_id}/decision")
async def submit_hitl_decision(
    item_id: str,
    payload: dict[str, Any],
    user: User = require_role(Role.HITL_REVIEWER),
) -> dict[str, Any]:
    decision = OfficerDecision(
        hitl_item_id=item_id,
        decision=HITLDecision(payload["decision"]),
        override_value=payload.get("override_value"),
        justification=payload["justification"],
        officer_id=user.user_id,
        officer_name=user.name,
        decided_at=now_utc(),
    )
    tender_id, item = _or_404(lambda: resolve_hitl_item(item_id, decision), "HITL item not found")
    audit_id = write_record(
        "HITL_DECISION_SUBMITTED",
        {
            "tender_id": tender_id,
            "hitl_item_id": item_id,
            "bid_id": item.bid_id,
            "criterion_id": item.criterion_id,
            "decision": decision.decision.value,
            "officer_id": user.user_id,
        },
    )
    decision.audit_record_id = audit_id
    unresolved = [i for i in get_hitl_items(tender_id) if not i.resolved]
    return {
        "decision": decision.model_dump(mode="json"),
        "unresolved_count": len(unresolved),
    }


@app.post("/api/tenders/{tender_id}/reports")
async def create_report(
    tender_id: str,
    user: User = require_role(Role.PROCUREMENT_OFFICER, Role.EVALUATOR, Role.AUDITOR),
) -> dict[str, Any]:
    unresolved = [item for item in get_hitl_items(tender_id) if not item.resolved]
    if unresolved:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resolve HITL items before final report")
    report = generate_report_for_tender(tender_id)
    return {"report": report.model_dump(mode="json")}


@app.get("/api/reports/{report_id}")
async def get_report_by_id(report_id: str, user: User = require_role(*list(Role))) -> dict[str, Any]:
    report = _or_404(lambda: get_report(report_id), "Report not found")
    return {"report": report.model_dump(mode="json")}


@app.get("/api/audit/verify")
async def verify_audit_chain(user: User = require_role(Role.AUDITOR, Role.PROCUREMENT_OFFICER, Role.EVALUATOR)) -> dict[str, Any]:
    is_valid = verify_chain()
    return {"chain_valid": is_valid, "status": "INTACT" if is_valid else "TAMPERED"}


@app.get("/api/audit/records")
async def list_audit_records(user: User = require_role(Role.AUDITOR)) -> dict[str, Any]:
    records = get_all_records()
    return {"count": len(records), "records": records}


@app.get("/api/rti/export/{bid_id}")
async def rti_export(bid_id: str, user: User = require_role(Role.AUDITOR)) -> dict[str, Any]:
    payload = export_for_rti(bid_id)
    write_record("RTI_EXPORT_DOWNLOADED", {"bid_id": bid_id, "user_id": user.user_id})
    return payload


async def _save_upload(tender_id: str, bid_id: str | None, file: UploadFile) -> UploadedDocument:
    content = await file.read()
    doc_hash = hashlib.sha256(content).hexdigest()
    folder = UPLOAD_DIR / tender_id / (bid_id or "nit")
    folder.mkdir(parents=True, exist_ok=True)
    filename = Path(file.filename or "upload.bin").name
    document_id = new_id("DOC")
    path = folder / f"{document_id}-{filename}"
    path.write_bytes(content)
    return add_document(
        UploadedDocument(
            document_id=document_id,
            tender_id=tender_id,
            bid_id=bid_id,
            filename=filename,
            path=str(path),
            size_bytes=len(content),
            doc_hash=doc_hash,
            uploaded_at=now_utc(),
        )
    )


def _demo_user(role: Role) -> User:
    labels = {
        Role.PROCUREMENT_OFFICER: "Procurement Officer",
        Role.EVALUATOR: "Evaluator",
        Role.HITL_REVIEWER: "HITL Reviewer",
        Role.AUDITOR: "Auditor",
    }
    return User(
        user_id=f"demo-{role.value.lower()}",
        name=labels.get(role, "Demo User"),
        email=f"{role.value.lower()}@cocomind.demo",
        role=role,
    )


def _or_404(fn, message: str):
    try:
        return fn()
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc


def _summary(vtms: dict) -> dict[str, Any]:
    summary = {}
    for bid_id, rows in vtms.items():
        verdicts = [row.verdict.status.value for row in rows]
        if "FAIL" in verdicts:
            overall = "INELIGIBLE"
        elif "AMBIGUOUS" in verdicts:
            overall = "PENDING HITL"
        else:
            overall = "ELIGIBLE"
        summary[bid_id] = {
            "overall": overall,
            "total": len(rows),
            "pass": verdicts.count("PASS"),
            "fail": verdicts.count("FAIL"),
            "ambiguous": verdicts.count("AMBIGUOUS"),
        }
    return summary
