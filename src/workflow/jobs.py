"""In-process async job orchestration for the MVP workflow."""

from __future__ import annotations

import time

from src.audit.chain import verify_chain, write_record
from src.models.workflow import BidderCreate, JobStatus, Report, WorkflowStatus
from src.workflow.fixtures import build_fixture_vtm, build_hitl_items, default_fixture_bidders
from src.workflow.store import (
    create_bidder,
    get_criteria,
    get_hitl_items,
    get_tender,
    get_vtm,
    list_bidders,
    list_decisions,
    new_id,
    now_utc,
    save_hitl_items,
    save_job,
    save_report,
    save_tender,
    save_vtm,
    set_job_state,
)


def run_evaluation_job(job_id: str) -> None:
    """Run a deterministic fixture-backed evaluation job."""
    job = set_job_state(job_id, JobStatus.INGESTING_NIT, 10, "Ingesting tender document")
    tender = get_tender(job.tender_id)
    tender.status = WorkflowStatus.EVALUATING
    tender.latest_job_id = job.job_id
    save_tender(tender)
    write_record("EVALUATION_STARTED", {"tender_id": tender.tender_id, "job_id": job_id})

    try:
        _sleep()
        set_job_state(job_id, JobStatus.EXTRACTING_CRITERIA, 28, "Using reviewed NIT criteria")
        if not get_criteria(tender.tender_id):
            raise RuntimeError("No criteria available for evaluation")

        _sleep()
        set_job_state(job_id, JobStatus.INGESTING_BIDS, 45, "Preparing bidder document bundles")
        if not list_bidders(tender.tender_id):
            for bidder in default_fixture_bidders():
                create_bidder(tender.tender_id, BidderCreate.model_validate(bidder))

        _sleep()
        set_job_state(job_id, JobStatus.PARSING_DOCUMENTS, 62, "Parsing documents with fixture fallback")

        _sleep()
        set_job_state(job_id, JobStatus.EVALUATING, 80, "Running deterministic eligibility rules")
        vtms = build_fixture_vtm(tender.tender_id)
        save_vtm(tender.tender_id, vtms)

        _sleep()
        set_job_state(job_id, JobStatus.ROUTING_HITL, 92, "Routing ambiguous cells to manual review")
        hitl_items = build_hitl_items(tender.tender_id, vtms)
        save_hitl_items(tender.tender_id, hitl_items)

        tender = get_tender(tender.tender_id)
        tender.status = WorkflowStatus.HITL_PENDING if hitl_items else WorkflowStatus.REPORT_READY
        save_tender(tender)
        set_job_state(job_id, JobStatus.COMPLETED, 100, "Evaluation completed")
        write_record(
            "EVALUATION_COMPLETED",
            {
                "tender_id": tender.tender_id,
                "job_id": job_id,
                "hitl_count": len(hitl_items),
                "demo_backed": True,
            },
        )
    except Exception as exc:  # pragma: no cover - defensive job guard
        job = set_job_state(job_id, JobStatus.FAILED, 100, "Evaluation failed")
        job.error = str(exc)
        save_job(job)
        write_record("EVALUATION_FAILED", {"tender_id": tender.tender_id, "job_id": job_id, "error": str(exc)})


def generate_report_for_tender(tender_id: str) -> Report:
    tender = get_tender(tender_id)
    vtms = get_vtm(tender_id)
    hitl_items = get_hitl_items(tender_id)
    decisions = list_decisions(tender_id)
    summary = _summary(vtms)
    report = Report(
        report_id=new_id("RPT"),
        tender_id=tender_id,
        generated_at=now_utc(),
        chain_verified=verify_chain(),
        summary=summary,
        export={
            "tender": tender.model_dump(mode="json"),
            "summary": summary,
            "vtm": {
                bid_id: [row.model_dump(mode="json") for row in rows]
                for bid_id, rows in vtms.items()
            },
            "hitl_items": [item.model_dump(mode="json") for item in hitl_items],
            "hitl_decisions": [decision.model_dump(mode="json") for decision in decisions],
        },
    )
    save_report(report)
    tender.report_id = report.report_id
    tender.status = WorkflowStatus.REPORT_READY
    save_tender(tender)
    write_record("REPORT_GENERATED", {"tender_id": tender_id, "report_id": report.report_id})
    return report


def _summary(vtms: dict) -> dict:
    result = {}
    for bid_id, rows in vtms.items():
        verdicts = [row.verdict.status.value for row in rows]
        if "FAIL" in verdicts:
            overall = "INELIGIBLE"
        elif "AMBIGUOUS" in verdicts:
            overall = "PENDING HITL"
        else:
            overall = "ELIGIBLE"
        result[bid_id] = {
            "overall": overall,
            "total": len(rows),
            "pass": verdicts.count("PASS"),
            "fail": verdicts.count("FAIL"),
            "ambiguous": verdicts.count("AMBIGUOUS"),
        }
    return result


def _sleep() -> None:
    time.sleep(0.15)
