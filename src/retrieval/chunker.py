"""Spatial-proximity chunker for OCR words.

Groups words by bbox neighbourhood on the same page.
Each chunk stores text, page, bbox, source_doc_id, avg_confidence, doc_type.
"""

from __future__ import annotations

import uuid

from src.models.documents import BBox, DocType, OCRChunk, OCRWord


def _words_are_close(w1: OCRWord, w2: OCRWord, x_gap: float = 0.05, y_gap: float = 0.02) -> bool:
    """Check if two words are spatially close enough to be in the same chunk."""
    if w1.page_num != w2.page_num:
        return False

    # Horizontal proximity
    h_close = abs(w1.bbox.x_max - w2.bbox.x_min) < x_gap or abs(w2.bbox.x_max - w1.bbox.x_min) < x_gap
    # Vertical proximity (same line or adjacent line)
    v_close = abs(w1.bbox.y_min - w2.bbox.y_min) < y_gap or abs(w1.bbox.y_max - w2.bbox.y_max) < y_gap

    return h_close and v_close


def _merge_bboxes(bboxes: list[BBox]) -> BBox:
    """Compute the bounding box enclosing all input bboxes."""
    return BBox(
        x_min=min(b.x_min for b in bboxes),
        y_min=min(b.y_min for b in bboxes),
        x_max=max(b.x_max for b in bboxes),
        y_max=max(b.y_max for b in bboxes),
    )


def chunk_words(
    words: list[OCRWord],
    source_doc_id: str = "",
    source_doc_type: DocType = DocType.UNKNOWN,
    max_chunk_words: int = 200,
    x_gap: float = 0.05,
    y_gap: float = 0.015,
) -> list[OCRChunk]:
    """Group OCR words into spatial-proximity chunks.

    Uses a simple greedy line-based grouping:
    1. Sort words by (page, y_min, x_min).
    2. Group words on the same line (y proximity).
    3. Merge adjacent lines within y_gap into a chunk.
    4. Split chunks that exceed max_chunk_words.
    """
    if not words:
        return []

    # Sort by page, then top-to-bottom, then left-to-right
    sorted_words = sorted(words, key=lambda w: (w.page_num, w.bbox.y_min, w.bbox.x_min))

    chunks: list[OCRChunk] = []
    current_group: list[OCRWord] = [sorted_words[0]]

    for word in sorted_words[1:]:
        prev = current_group[-1]

        # Same page and vertically close → same chunk
        same_page = word.page_num == prev.page_num
        v_close = abs(word.bbox.y_min - prev.bbox.y_min) < y_gap

        if same_page and v_close and len(current_group) < max_chunk_words:
            current_group.append(word)
        else:
            # Finalise current chunk
            chunks.append(_create_chunk(current_group, source_doc_id, source_doc_type))
            current_group = [word]

    # Finalise last group
    if current_group:
        chunks.append(_create_chunk(current_group, source_doc_id, source_doc_type))

    return chunks


def _create_chunk(
    words: list[OCRWord],
    source_doc_id: str,
    source_doc_type: DocType,
) -> OCRChunk:
    """Create an OCRChunk from a group of words."""
    text = " ".join(w.text for w in words)
    bboxes = [w.bbox for w in words]
    merged_bbox = _merge_bboxes(bboxes)
    avg_conf = sum(w.confidence for w in words) / len(words) if words else 0.0

    return OCRChunk(
        chunk_id=uuid.uuid4().hex,
        text=text,
        page_num=words[0].page_num,
        bbox=merged_bbox,
        source_doc_id=source_doc_id,
        source_doc_type=source_doc_type,
        avg_confidence=round(avg_conf, 4),
        word_count=len(words),
    )
