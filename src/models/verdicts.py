"""Verdict, VTM row, and conflict resolution models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.models.documents import BBox, DocType


class VerdictStatus(StrEnum):
    """Possible verdict outcomes."""

    PASS = "PASS"
    FAIL = "FAIL"
    AMBIGUOUS = "AMBIGUOUS"


class ConflictStatus(StrEnum):
    """Conflict resolution status."""

    NONE = "NONE"
    AUTO_RESOLVED = "AUTO_RESOLVED"
    CONFLICT_UNRESOLVED = "CONFLICT_UNRESOLVED"


class Verdict(BaseModel):
    """Output of the rule engine for a single criterion × bid cell."""

    status: VerdictStatus
    reason: str = ""
    expression: str = Field(default="", description="e.g. '60000000 gte 50000000'")


class ConflictResolution(BaseModel):
    """Result of the conflict detector when multiple chunks disagree."""

    conflict_status: ConflictStatus = ConflictStatus.NONE
    winning_doc_type: DocType | None = None
    winning_chunk_id: str = ""
    losing_chunk_ids: list[str] = []
    reason: str = ""
    value_delta_pct: float = 0.0


class VTMRow(BaseModel):
    """A single cell in the Verdict Traceability Matrix.

    This is the single most important output of the system — every field
    must be defensible under RTI, CAG, and CVC scrutiny.
    """

    bid_id: str
    bid_name: str = ""
    criterion_id: str
    criterion_name: str = ""

    # Verdict
    verdict: Verdict

    # Provenance
    source_doc_id: str = ""
    source_doc_type: DocType = DocType.UNKNOWN
    page_num: int = 0
    bbox: BBox | None = None
    raw_text: str = ""
    redacted_text: str = ""
    normalised_value: float | bool | str | None = None

    # Confidence
    ocr_confidence: float = 0.0
    llm_confidence: float = 0.0
    retrieval_score: float = 0.0

    # Conflict
    conflict: ConflictResolution = ConflictResolution()

    # HITL
    hitl_decision: str | None = None
    signed_by: str | None = None
    signature_timestamp: datetime | None = None

    # Audit
    audit_record_id: str = ""
    rule_expression: str = ""
    prompt_version: str = ""
