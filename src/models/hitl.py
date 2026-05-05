"""HITL (Human-in-the-Loop) models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.models.documents import BBox


class HITLReason(StrEnum):
    """Why a cell was routed to HITL."""

    LOW_OCR_CONFIDENCE = "low_ocr_confidence"
    LOW_RETRIEVAL_SCORE = "low_retrieval_score"
    LOW_LLM_CONFIDENCE = "low_llm_confidence"
    CONFLICT_UNRESOLVED = "conflict_unresolved"
    VALUE_NOT_EXTRACTED = "value_not_extracted"
    BLACKLIST_FUZZY_MATCH = "blacklist_fuzzy_match"
    NEAR_RELATIONS_AMBIGUOUS = "near_relations_ambiguous"
    LARGE_VALUE_ANOMALY = "large_value_anomaly"


class HITLDecision(StrEnum):
    """Officer's decision on an HITL item."""

    CONFIRM = "CONFIRM"
    OVERRIDE = "OVERRIDE"
    NOT_PROVIDED = "NOT_PROVIDED"


class HITLItem(BaseModel):
    """An item in the HITL review queue."""

    item_id: str
    bid_id: str
    criterion_id: str
    reason: HITLReason
    reason_detail: str = ""

    # Context for the reviewer
    source_doc_id: str = ""
    page_num: int = 0
    bbox: BBox | None = None
    ocr_text: str = ""
    extracted_value: float | bool | str | None = None
    confidence: float = 0.0

    # State
    resolved: bool = False
    created_at: datetime | None = None


class OfficerDecision(BaseModel):
    """An officer's resolution of an HITL item — signed and audit-logged."""

    hitl_item_id: str
    decision: HITLDecision
    override_value: float | bool | str | None = None
    justification: str = Field(
        min_length=1, description="Officer must provide a reason"
    )
    officer_id: str
    officer_name: str = ""
    decided_at: datetime
    signature_id: str | None = None
    audit_record_id: str = ""
