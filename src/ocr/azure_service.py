"""Azure Document Intelligence OCR adapter.

Extracts word-level bounding boxes, confidence scores, and handwriting flags.
Confidence floor (default 0.72) triggers HITL or fallback routing.
"""

from __future__ import annotations

from src.config.settings import get_settings
from src.models.documents import BBox, OCRPage, OCRWord


def _azure_client():  # type: ignore[no-untyped-def]
    """Lazy-init Azure client to avoid import cost at module level."""
    from azure.ai.formrecognizer import DocumentAnalysisClient  # type: ignore[import-untyped]
    from azure.core.credentials import AzureKeyCredential  # type: ignore[import-untyped]

    settings = get_settings()
    return DocumentAnalysisClient(
        endpoint=settings.azure_docint_endpoint,
        credential=AzureKeyCredential(settings.azure_docint_key),
    )


def ocr_page_azure(
    image_bytes: bytes,
    page_num: int,
    source_doc_id: str = "",
    confidence_floor: float | None = None,
) -> OCRPage:
    """Send a page image to Azure Document Intelligence and parse results.

    Returns an OCRPage with all words, bboxes, and confidence.
    If avg confidence < floor, sets route_to_fallback = True.
    """
    settings = get_settings()
    floor = confidence_floor or settings.ocr_confidence_floor

    client = _azure_client()
    poller = client.begin_analyze_document(
        "prebuilt-read",
        document=image_bytes,
    )
    result = poller.result()

    words: list[OCRWord] = []
    total_confidence = 0.0
    has_handwriting = False

    for page in result.pages:
        if page.words:
            for word in page.words:
                # Azure returns polygon as list of points
                polygon = word.polygon if word.polygon else []
                if len(polygon) >= 4:
                    xs = [p.x for p in polygon]
                    ys = [p.y for p in polygon]
                    bbox = BBox(
                        x_min=min(xs),
                        y_min=min(ys),
                        x_max=max(xs),
                        y_max=max(ys),
                    )
                else:
                    bbox = BBox(x_min=0, y_min=0, x_max=0, y_max=0)

                conf = word.confidence if word.confidence is not None else 0.5
                total_confidence += conf

                words.append(
                    OCRWord(
                        text=word.content,
                        bbox=bbox,
                        confidence=conf,
                        page_num=page_num,
                        is_handwritten=False,  # Azure marks in styles
                    )
                )

        # Check for handwriting style
        if hasattr(page, "spans") and result.styles:
            for style in result.styles:
                if style.is_handwritten:
                    has_handwriting = True
                    break

    avg_confidence = total_confidence / len(words) if words else 0.0

    return OCRPage(
        page_num=page_num,
        words=words,
        avg_confidence=round(avg_confidence, 4),
        is_handwritten=has_handwriting,
        source_doc_id=source_doc_id,
        route_to_fallback=avg_confidence < floor,
    )


def ocr_document_pages(
    pages_image_bytes: list[tuple[int, bytes]],
    source_doc_id: str = "",
) -> list[OCRPage]:
    """OCR multiple pages in sequence.

    Args:
        pages_image_bytes: list of (page_num, image_bytes) tuples.
        source_doc_id: SHA-256 hash of the source document.

    Returns:
        list of OCRPage, one per input page.
    """
    return [
        ocr_page_azure(img_bytes, page_num, source_doc_id)
        for page_num, img_bytes in pages_image_bytes
    ]
