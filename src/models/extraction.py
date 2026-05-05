"""Extraction result and redaction map models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.models.documents import BBox, DocType


class RedactionMapEntry(BaseModel):
    """A single PII entity that was redacted with a reversible token."""

    entity_type: str = Field(description="e.g. 'AADHAAR', 'PAN', 'GSTIN'")
    token: str = Field(description="UUID replacement token")
    page_num: int = 0
    bbox: BBox | None = None


class RedactionMap(BaseModel):
    """Container for all redactions in a single pipeline run.

    The map is AES-256 encrypted at rest. The LLM never sees the original values.
    """

    map_id: str
    entries: list[RedactionMapEntry] = []
    encryption_key_id: str = ""


class ExtractionResult(BaseModel):
    """A single value extracted from a bid document chunk by the LLM.

    This is the contract between the value extractor and the rule engine.
    Every field carries provenance for RTI traceability.
    """

    raw_text: str = Field(description="Original text — local only, never exported")
    redacted_text: str = Field(description="What the LLM actually saw")
    normalised_value: float | bool | str | None = None
    unit: str = Field(
        default="",
        description="'INR' | '%' | 'years' | 'bool' | 'date'"
    )
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    source_chunk_id: str = ""
    source_doc_type: DocType = DocType.UNKNOWN
    source_doc_id: str = ""
    source_bbox: BBox | None = None
    page_num: int = 0
    redaction_map_id: str = ""
    prompt_version: str = Field(
        default="", description="e.g. 'value_extractor@v1.0'"
    )
    ocr_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    llm_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
