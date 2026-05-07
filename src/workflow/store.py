"""SQLite-backed workflow store for the integrated MVP."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from src.models.criteria import Criterion
from src.models.hitl import HITLItem, OfficerDecision
from src.models.verdicts import VTMRow, VerdictStatus
from src.models.workflow import (
    Bidder,
    BidderCreate,
    EvaluationJob,
    JobStatus,
    Report,
    Tender,
    TenderCreate,
    UploadedDocument,
    WorkflowStatus,
)

T = TypeVar("T", bound=BaseModel)

DATA_DIR = Path("data")
WORKFLOW_DIR = DATA_DIR / "workflow"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = WORKFLOW_DIR / "workflow.db"


def now_utc() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def init_workflow_db() -> None:
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS objects (
                kind TEXT NOT NULL,
                id TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (kind, id)
            );
            """
        )


def create_tender(payload: TenderCreate, user_id: str) -> Tender:
    tender = Tender(
        **payload.model_dump(),
        tender_id=new_id("TDR"),
        created_by=user_id,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    _put("tender", tender.tender_id, tender)
    return tender


def list_tenders() -> list[Tender]:
    return _list("tender", Tender)


def get_tender(tender_id: str) -> Tender:
    return _get("tender", tender_id, Tender)


def save_tender(tender: Tender) -> Tender:
    tender.updated_at = now_utc()
    _put("tender", tender.tender_id, tender)
    return tender


def add_document(document: UploadedDocument) -> UploadedDocument:
    _put("document", document.document_id, document)
    return document


def list_documents(tender_id: str, bid_id: str | None = None) -> list[UploadedDocument]:
    docs = _list("document", UploadedDocument)
    return [
        doc for doc in docs
        if doc.tender_id == tender_id and (bid_id is None or doc.bid_id == bid_id)
    ]


def create_bidder(tender_id: str, payload: BidderCreate) -> Bidder:
    bidder = Bidder(
        **payload.model_dump(),
        tender_id=tender_id,
        created_at=now_utc(),
        documents=[],
    )
    _put("bidder", f"{tender_id}:{bidder.bid_id}", bidder)
    return bidder


def save_bidder(bidder: Bidder) -> Bidder:
    _put("bidder", f"{bidder.tender_id}:{bidder.bid_id}", bidder)
    return bidder


def list_bidders(tender_id: str) -> list[Bidder]:
    bidders = [b for b in _list("bidder", Bidder) if b.tender_id == tender_id]
    docs = list_documents(tender_id)
    for bidder in bidders:
        bidder.documents = [doc for doc in docs if doc.bid_id == bidder.bid_id]
    return bidders


def save_criteria(tender_id: str, criteria: list[Criterion]) -> None:
    _put_raw("criteria", tender_id, [c.model_dump(mode="json") for c in criteria])


def get_criteria(tender_id: str) -> list[Criterion]:
    return [Criterion.model_validate(item) for item in _get_raw("criteria", tender_id, [])]


def update_criterion(tender_id: str, criterion_id: str, patch: dict[str, Any]) -> Criterion:
    criteria = get_criteria(tender_id)
    for idx, criterion in enumerate(criteria):
        if criterion.id == criterion_id:
            updated = criterion.model_copy(update=patch)
            criteria[idx] = updated
            save_criteria(tender_id, criteria)
            return updated
    raise KeyError(criterion_id)


def create_job(tender_id: str) -> EvaluationJob:
    job = EvaluationJob(
        job_id=new_id("JOB"),
        tender_id=tender_id,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    save_job(job)
    return job


def get_job(job_id: str) -> EvaluationJob:
    return _get("job", job_id, EvaluationJob)


def save_job(job: EvaluationJob) -> EvaluationJob:
    job.updated_at = now_utc()
    _put("job", job.job_id, job)
    return job


def set_job_state(job_id: str, status: JobStatus, progress: int, message: str) -> EvaluationJob:
    job = get_job(job_id)
    job.status = status
    job.progress = progress
    job.message = message
    return save_job(job)


def save_vtm(tender_id: str, vtms: dict[str, list[VTMRow]]) -> None:
    _put_raw(
        "vtm",
        tender_id,
        {bid_id: [row.model_dump(mode="json") for row in rows] for bid_id, rows in vtms.items()},
    )


def get_vtm(tender_id: str) -> dict[str, list[VTMRow]]:
    payload = _get_raw("vtm", tender_id, {})
    return {
        bid_id: [VTMRow.model_validate(item) for item in rows]
        for bid_id, rows in payload.items()
    }


def save_hitl_items(tender_id: str, items: list[HITLItem]) -> None:
    _put_raw("hitl", tender_id, [item.model_dump(mode="json") for item in items])


def get_hitl_items(tender_id: str) -> list[HITLItem]:
    return [HITLItem.model_validate(item) for item in _get_raw("hitl", tender_id, [])]


def resolve_hitl_item(item_id: str, decision: OfficerDecision) -> tuple[str, HITLItem]:
    tender_id = item_id.split(":", 1)[0]
    items = get_hitl_items(tender_id)
    for idx, item in enumerate(items):
        if item.item_id == item_id:
            item.resolved = True
            items[idx] = item
            save_hitl_items(tender_id, items)
            _put("decision", item_id, decision)
            _apply_hitl_decision_to_vtm(tender_id, item, decision)
            return tender_id, item
    raise KeyError(item_id)


def list_decisions(tender_id: str) -> list[OfficerDecision]:
    return [
        decision for key, decision in _list_with_ids("decision", OfficerDecision)
        if key.startswith(f"{tender_id}:")
    ]


def save_report(report: Report) -> Report:
    _put("report", report.report_id, report)
    return report


def get_report(report_id: str) -> Report:
    return _get("report", report_id, Report)


def _apply_hitl_decision_to_vtm(
    tender_id: str,
    item: HITLItem,
    decision: OfficerDecision,
) -> None:
    vtms = get_vtm(tender_id)
    for rows in vtms.values():
        for row in rows:
            if row.bid_id == item.bid_id and row.criterion_id == item.criterion_id:
                row.hitl_decision = decision.decision.value
                row.signed_by = decision.officer_id
                row.signature_timestamp = decision.decided_at
                if decision.decision.value == "CONFIRM":
                    row.verdict.status = VerdictStatus.PASS
                    row.verdict.reason = "hitl_confirmed"
                elif decision.decision.value == "OVERRIDE":
                    row.normalised_value = decision.override_value
                    row.verdict.status = VerdictStatus.PASS
                    row.verdict.reason = "hitl_override"
                else:
                    row.verdict.status = VerdictStatus.FAIL
                    row.verdict.reason = "hitl_not_provided"
                row.verdict.expression = f"HITL {decision.decision.value}: {decision.justification}"
                row.rule_expression = row.verdict.expression
    save_vtm(tender_id, vtms)


def _conn() -> sqlite3.Connection:
    init_parent = not DB_PATH.parent.exists()
    if init_parent:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def _put(kind: str, object_id: str, model: BaseModel) -> None:
    _put_raw(kind, object_id, model.model_dump(mode="json"))


def _put_raw(kind: str, object_id: str, payload: Any) -> None:
    init_workflow_db()
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO objects(kind, id, payload) VALUES (?, ?, ?)",
            (kind, object_id, json.dumps(payload, sort_keys=True, default=str)),
        )


def _get(kind: str, object_id: str, model: type[T]) -> T:
    payload = _get_raw(kind, object_id, None)
    if payload is None:
        raise KeyError(f"{kind}:{object_id}")
    return model.model_validate(payload)


def _get_raw(kind: str, object_id: str, default: Any) -> Any:
    init_workflow_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT payload FROM objects WHERE kind = ? AND id = ?",
            (kind, object_id),
        ).fetchone()
    return json.loads(row[0]) if row else default


def _list(kind: str, model: type[T]) -> list[T]:
    return [item for _id, item in _list_with_ids(kind, model)]


def _list_with_ids(kind: str, model: type[T]) -> list[tuple[str, T]]:
    init_workflow_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, payload FROM objects WHERE kind = ? ORDER BY rowid DESC",
            (kind,),
        ).fetchall()
    return [(row[0], model.model_validate(json.loads(row[1]))) for row in rows]
