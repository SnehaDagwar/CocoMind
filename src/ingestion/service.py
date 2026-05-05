"""Document ingestion service.

Accepts PDF, DOCX, JPEG, PNG, ZIP uploads → list of DocumentPage.
SHA-256 hash of original bytes is the primary key for all downstream records.
Doc-type heuristic runs before any LLM classification.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path
from typing import BinaryIO

from PIL import Image

from src.models.documents import DocType, DocumentPage

# Keyword heuristics for doc-type classification (page 1 only)
_DOC_TYPE_KEYWORDS: dict[str, DocType] = {
    "notice inviting tender": DocType.NIT,
    "nit": DocType.NIT,
    "chartered accountant": DocType.CA_CERTIFICATE,
    "ca certificate": DocType.CA_CERTIFICATE,
    "audited financial": DocType.AUDITED_FINANCIAL_STATEMENT,
    "balance sheet": DocType.AUDITED_FINANCIAL_STATEMENT,
    "income tax return": DocType.ITR,
    "itr": DocType.ITR,
    "gstin": DocType.GST_CERT,
    "gst registration": DocType.GST_CERT,
    "goods and services tax": DocType.GST_CERT,
    "permanent account number": DocType.PAN_CARD,
    "pan card": DocType.PAN_CARD,
    "company profile": DocType.COMPANY_PROFILE,
    "integrity pact": DocType.INTEGRITY_PACT,
    "earnest money deposit": DocType.EMD_DOCUMENT,
    "bank guarantee": DocType.EMD_DOCUMENT,
    "self declaration": DocType.SELF_DECLARATION,
    "self-declaration": DocType.SELF_DECLARATION,
    "experience certificate": DocType.EXPERIENCE_CERT,
    "work order": DocType.EXPERIENCE_CERT,
    "completion certificate": DocType.EXPERIENCE_CERT,
    "iso 9001": DocType.ISO_CERT,
    "quality management": DocType.ISO_CERT,
    "near relation": DocType.SELF_DECLARATION,
    "not blacklisted": DocType.SELF_DECLARATION,
}


def compute_file_hash(data: bytes) -> str:
    """SHA-256 hash of file bytes — primary key for downstream records."""
    return hashlib.sha256(data).hexdigest()


def detect_doc_type(text: str) -> DocType:
    """Heuristic doc-type classification from page-1 text.

    Cheap; runs before any LLM. Feeds the conflict resolver's hierarchy.
    """
    text_lower = text.lower()
    for keyword, doc_type in _DOC_TYPE_KEYWORDS.items():
        if keyword in text_lower:
            return doc_type
    return DocType.BID_SUBMISSION


def _sniff_content_type(data: bytes) -> str:
    """Detect file content type from magic bytes."""
    if data[:4] == b"%PDF":
        return "application/pdf"
    if data[:2] in (b"\xff\xd8",):
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"PK\x03\x04":
        # Could be DOCX or ZIP
        if b"word/" in data[:2000]:
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return "application/zip"
    return "application/octet-stream"


def ingest_pdf(file_bytes: bytes, source_path: str) -> list[DocumentPage]:
    """Convert a PDF into per-page DocumentPage objects.

    Uses PyMuPDF (fitz) to rasterise each page to a PNG image.
    """
    import fitz  # type: ignore[import-untyped]

    doc_hash = compute_file_hash(file_bytes)
    pages: list[DocumentPage] = []

    pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]

        # Extract text for doc-type heuristic on first page
        page_text = page.get_text()
        doc_type = detect_doc_type(page_text) if page_num == 0 else DocType.UNKNOWN

        # Rasterise to image
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")

        # Save image to temp path
        img_dir = Path("data/uploads/images")
        img_dir.mkdir(parents=True, exist_ok=True)
        img_path = img_dir / f"{doc_hash}_page_{page_num + 1}.png"
        img_path.write_bytes(img_bytes)

        pages.append(
            DocumentPage(
                page_num=page_num + 1,
                source_path=source_path,
                doc_hash=doc_hash,
                doc_type=doc_type,
                image_path=str(img_path),
            )
        )

    pdf_doc.close()
    return pages


def ingest_image(file_bytes: bytes, source_path: str) -> list[DocumentPage]:
    """Convert an image (JPEG/PNG) into a single DocumentPage."""
    doc_hash = compute_file_hash(file_bytes)

    img_dir = Path("data/uploads/images")
    img_dir.mkdir(parents=True, exist_ok=True)
    img_path = img_dir / f"{doc_hash}_page_1.png"

    # Normalise to PNG
    img = Image.open(io.BytesIO(file_bytes))
    img.save(str(img_path), format="PNG")

    return [
        DocumentPage(
            page_num=1,
            source_path=source_path,
            doc_hash=doc_hash,
            doc_type=DocType.UNKNOWN,
            image_path=str(img_path),
        )
    ]


def ingest_docx(file_bytes: bytes, source_path: str) -> list[DocumentPage]:
    """Convert a DOCX into DocumentPage objects.

    Extracts text for doc-type heuristic; rasterisation handled downstream.
    """
    from docx import Document as DocxDocument  # type: ignore[import-untyped]

    doc_hash = compute_file_hash(file_bytes)
    docx_doc = DocxDocument(io.BytesIO(file_bytes))

    full_text = "\n".join(p.text for p in docx_doc.paragraphs)
    doc_type = detect_doc_type(full_text)

    # DOCX is treated as a single page for simplicity in Tier-1
    return [
        DocumentPage(
            page_num=1,
            source_path=source_path,
            doc_hash=doc_hash,
            doc_type=doc_type,
            image_path=None,  # no rasterisation for DOCX in Tier-1
        )
    ]


def ingest_file(file_data: BinaryIO | bytes, source_path: str) -> list[DocumentPage]:
    """Route a file to the correct ingestion handler based on content type.

    Uses magic-byte sniffing, not extension trust.
    """
    data = file_data if isinstance(file_data, bytes) else file_data.read()

    content_type = _sniff_content_type(data)

    if content_type == "application/pdf":
        return ingest_pdf(data, source_path)
    if content_type in ("image/jpeg", "image/png"):
        return ingest_image(data, source_path)
    if content_type.endswith("wordprocessingml.document"):
        return ingest_docx(data, source_path)
    if content_type == "application/zip":
        return _ingest_zip(data, source_path)
    # Treat unknown as single-page bid submission
    doc_hash = compute_file_hash(data)
    return [
        DocumentPage(
            page_num=1,
            source_path=source_path,
            doc_hash=doc_hash,
            doc_type=DocType.UNKNOWN,
        )
    ]


def _ingest_zip(data: bytes, source_path: str) -> list[DocumentPage]:
    """Extract a ZIP and recursively ingest each file inside."""
    all_pages: list[DocumentPage] = []

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue  # skip directories
            member_data = zf.read(name)
            member_path = f"{source_path}!{name}"
            all_pages.extend(ingest_file(member_data, member_path))

    return all_pages
