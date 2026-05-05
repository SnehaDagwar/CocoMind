"""Document-related data models — pages, OCR words, and chunks."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class DocType(StrEnum):
    """Heuristic document type classification."""

    NIT = "nit"
    CA_CERTIFICATE = "ca_certificate"
    AUDITED_FINANCIAL_STATEMENT = "audited_financial_statement"
    ITR = "itr"
    GST_CERT = "gst_cert"
    PAN_CARD = "pan_card"
    COMPANY_PROFILE = "company_profile"
    COVER_LETTER = "cover_letter"
    SELF_DECLARATION = "self_declaration"
    EMD_DOCUMENT = "emd_document"
    INTEGRITY_PACT = "integrity_pact"
    EXPERIENCE_CERT = "experience_cert"
    ISO_CERT = "iso_cert"
    BID_SUBMISSION = "bid_submission"
    UNKNOWN = "unknown"


class BBox(BaseModel):
    """Bounding box on a page (normalised 0-1 or pixel coords)."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def area(self) -> float:
        return max(0, self.x_max - self.x_min) * max(0, self.y_max - self.y_min)


class DocumentPage(BaseModel):
    """A single page from an uploaded document after rasterisation."""

    page_num: int
    source_path: str
    doc_hash: str = Field(description="SHA-256 of original file bytes")
    doc_type: DocType = DocType.UNKNOWN
    image_path: str | None = None


class OCRWord(BaseModel):
    """A single word extracted by OCR with its bounding box."""

    text: str
    bbox: BBox
    confidence: float = Field(ge=0.0, le=1.0)
    page_num: int
    is_handwritten: bool = False


class OCRPage(BaseModel):
    """All OCR results for a single page."""

    page_num: int
    words: list[OCRWord]
    avg_confidence: float = Field(ge=0.0, le=1.0)
    is_handwritten: bool = False
    source_doc_id: str = ""
    route_to_fallback: bool = False


class OCRChunk(BaseModel):
    """A spatial-proximity chunk of OCR words."""

    chunk_id: str
    text: str
    page_num: int
    bbox: BBox
    source_doc_id: str
    source_doc_type: DocType = DocType.UNKNOWN
    avg_confidence: float = Field(ge=0.0, le=1.0)
    word_count: int = 0
