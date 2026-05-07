"""Deterministic fixture-backed workflow data for the MVP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models.criteria import Criterion
from src.models.documents import BBox, DocType
from src.models.hitl import HITLItem, HITLReason
from src.models.verdicts import ConflictResolution, ConflictStatus, Verdict, VerdictStatus, VTMRow

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = PROJECT_ROOT / "data" / "synthetic"


def _read_json(filename: str) -> dict[str, Any]:
    return json.loads((SYNTHETIC_DIR / filename).read_text(encoding="utf-8"))


def load_fixture_criteria() -> list[Criterion]:
    nit = _read_json("nit_sample.json")
    criteria: list[Criterion] = []
    for item in nit["criteria"]:
        criteria.append(
            Criterion(
                id=item["id"],
                name=item["name"],
                category=item["category"],
                mandatory=item["mandatory"],
                data_type=item["data_type"],
                threshold_operator=item["threshold_operator"],
                threshold_value=item.get("threshold_value"),
                threshold_upper=item.get("threshold_upper"),
                source_section=item.get("source_section", ""),
                citation=item.get("citation", ""),
            )
        )
    return criteria


def default_fixture_bidders() -> list[dict[str, str]]:
    return [
        {"bid_id": "BID-A", "bid_name": "M/s Sharma Industrial Pvt Ltd"},
        {"bid_id": "BID-B", "bid_name": "M/s Verma Tech Solutions"},
        {"bid_id": "BID-C", "bid_name": "M/s Gupta Equipment Co"},
    ]


def build_fixture_vtm(tender_id: str) -> dict[str, list[VTMRow]]:
    criteria = {criterion.id: criterion for criterion in load_fixture_criteria()}
    bid_files = {
        "BID-A": "bid_a_pass.json",
        "BID-B": "bid_b_fail.json",
        "BID-C": "bid_c_hitl.json",
    }
    return {
        bid_id: _build_bid_rows(tender_id, bid_id, filename, criteria)
        for bid_id, filename in bid_files.items()
    }


def build_hitl_items(tender_id: str, vtms: dict[str, list[VTMRow]]) -> list[HITLItem]:
    items: list[HITLItem] = []
    for bid_id, rows in vtms.items():
        for row in rows:
            if row.verdict.status != VerdictStatus.AMBIGUOUS:
                continue
            reason = HITLReason.CONFLICT_UNRESOLVED
            if row.verdict.reason in {"low_extraction_confidence", "value_not_extracted"}:
                reason = HITLReason.LOW_LLM_CONFIDENCE
            items.append(
                HITLItem(
                    item_id=f"{tender_id}:{bid_id}:{row.criterion_id}",
                    bid_id=bid_id,
                    criterion_id=row.criterion_id,
                    reason=reason,
                    reason_detail=row.verdict.reason or row.verdict.expression,
                    source_doc_id=row.source_doc_id,
                    page_num=row.page_num,
                    bbox=row.bbox,
                    ocr_text=row.raw_text,
                    extracted_value=row.normalised_value,
                    confidence=max(row.ocr_confidence, row.llm_confidence),
                    resolved=False,
                )
            )
    return items


def _build_bid_rows(
    tender_id: str,
    bid_id: str,
    filename: str,
    criteria: dict[str, Criterion],
) -> list[VTMRow]:
    bid = _read_json(filename)
    expected = bid["expected_vtm"]
    rows: list[VTMRow] = []

    for criterion_id, item in expected.items():
        criterion = criteria[criterion_id]

        status = VerdictStatus(item["verdict"])
        value = item.get("value")
        confidence = float(item.get("confidence", 0.0))
        reason = item.get("reason", "")
        source_doc = _source_for_criterion(bid, criterion_id)
        expression = _expression_for(criterion, value, status, reason)
        conflict = ConflictResolution()
        if reason == "conflict_unresolved_hitl":
            conflict = ConflictResolution(
                conflict_status=ConflictStatus.CONFLICT_UNRESOLVED,
                reason="CA certificate and cover letter disagree on turnover.",
                value_delta_pct=8.3,
            )

        rows.append(
            VTMRow(
                bid_id=bid_id,
                bid_name=bid["bid_name"],
                criterion_id=criterion_id,
                criterion_name=criterion.name,
                verdict=Verdict(status=status, reason=reason, expression=expression),
                source_doc_id=source_doc["doc_id"],
                source_doc_type=DocType(source_doc["doc_type"]),
                page_num=source_doc["page_num"],
                bbox=BBox(x_min=0.16, y_min=0.28, x_max=0.78, y_max=0.36),
                raw_text=source_doc["raw_text"],
                redacted_text=source_doc["redacted_text"],
                normalised_value=value,
                ocr_confidence=confidence,
                llm_confidence=confidence,
                retrieval_score=0.92 if status != VerdictStatus.AMBIGUOUS else 0.42,
                conflict=conflict,
                rule_expression=expression,
                prompt_version="fixture@v1",
                audit_record_id=f"fixture:{tender_id}:{bid_id}:{criterion_id}",
            )
        )
    return rows


def _source_for_criterion(bid: dict[str, Any], criterion_id: str) -> dict[str, Any]:
    preferred = {
        "C001": {"ca_certificate", "audited_financial_statement", "cover_letter"},
        "C002": {"experience_cert"},
        "C003": {"gst_cert"},
        "C004": {"emd_document"},
        "C005": {"self_declaration"},
        "C006": {"integrity_pact"},
    }[criterion_id]
    doc = next(
        (d for d in bid["documents"] if d["doc_type"] in preferred),
        bid["documents"][0],
    )
    raw = json.dumps(doc.get("synthetic_content", {}), ensure_ascii=False)
    return {
        "doc_id": doc["doc_id"],
        "doc_type": doc["doc_type"],
        "page_num": 1,
        "raw_text": raw,
        "redacted_text": raw.replace("4567 8901 2345", "<IN_AADHAAR:demo-token>"),
    }


def _expression_for(
    criterion: Criterion,
    value: float | bool | str | None,
    status: VerdictStatus,
    reason: str,
) -> str:
    if status == VerdictStatus.AMBIGUOUS:
        return reason or "Requires manual review"
    if criterion.threshold_operator == "contains":
        return f"bool({value}) == True"
    return f"{value} {criterion.threshold_operator} {criterion.threshold_value}"
