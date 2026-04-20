"""Pipeline orchestrator — connects all stages end-to-end.

Input: NIT path + bid paths.
Output: VTM (Verdict Traceability Matrix) per bid.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from src.audit.chain import write_record
from src.config.settings import get_settings
from src.conflict.resolver import detect_conflict
from src.engine.rule_engine import evaluate
from src.ingestion.service import ingest_file
from src.models.criteria import Criterion
from src.models.documents import DocType
from src.models.extraction import ExtractionResult
from src.models.verdicts import (
    ConflictStatus,
    Verdict,
    VerdictStatus,
    VTMRow,
)
from src.redaction.presidio_pipeline import create_redaction_map, redact_text
from src.retrieval.hybrid_retriever import hybrid_retrieve


def run_pipeline(
    nit_path: str,
    bid_paths: list[dict],
    criteria: list[Criterion] | None = None,
) -> dict[str, list[VTMRow]]:
    """Run the full evaluation pipeline.

    Args:
        nit_path: Path to the NIT document.
        bid_paths: List of dicts with keys: bid_id, bid_name, path.
        criteria: Pre-extracted criteria (if None, will extract from NIT).

    Returns:
        Dict mapping bid_id → list of VTMRow.
    """
    get_settings()

    # Log pipeline start
    pipeline_run_id = uuid.uuid4().hex
    write_record("PIPELINE_START", {
        "pipeline_run_id": pipeline_run_id,
        "nit_path": nit_path,
        "bid_count": len(bid_paths),
    })

    # Step 1: Extract criteria from NIT (if not provided)
    if criteria is None:
        from src.extraction.criterion_extractor import extract_criteria_from_text
        nit_bytes = Path(nit_path).read_bytes()
        ingest_file(nit_bytes, nit_path)
        # For now, just use the text from ingestion
        nit_text = ""  # Would come from OCR in full pipeline
        criteria = extract_criteria_from_text(nit_text)

    # Step 2: Process each bid
    all_vtms: dict[str, list[VTMRow]] = {}

    for bid_info in bid_paths:
        bid_id = bid_info["bid_id"]
        bid_name = bid_info.get("bid_name", bid_id)
        bid_path = bid_info["path"]

        vtm_rows = _process_bid(
            bid_id=bid_id,
            bid_name=bid_name,
            bid_path=bid_path,
            criteria=criteria,
            pipeline_run_id=pipeline_run_id,
        )
        all_vtms[bid_id] = vtm_rows

    # Log pipeline completion
    write_record("PIPELINE_COMPLETE", {
        "pipeline_run_id": pipeline_run_id,
        "bid_results": {
            bid_id: {
                "total": len(rows),
                "pass": sum(1 for r in rows if r.verdict.status == VerdictStatus.PASS),
                "fail": sum(1 for r in rows if r.verdict.status == VerdictStatus.FAIL),
                "ambiguous": sum(1 for r in rows if r.verdict.status == VerdictStatus.AMBIGUOUS),
            }
            for bid_id, rows in all_vtms.items()
        },
    })

    return all_vtms


def _process_bid(
    bid_id: str,
    bid_name: str,
    bid_path: str,
    criteria: list[Criterion],
    pipeline_run_id: str,
) -> list[VTMRow]:
    """Process a single bid against all criteria."""
    get_settings()
    redaction_map = create_redaction_map()
    vtm_rows: list[VTMRow] = []

    # Ingest bid documents
    bid_bytes = Path(bid_path).read_bytes()
    ingest_file(bid_bytes, bid_path)

    # OCR each page (would call azure_service in full pipeline)
    # For now, we'll work with the chunks from retrieval

    # Evaluate each criterion
    for criterion in criteria:
        # Retrieve relevant chunks
        retrieved = hybrid_retrieve(criterion.name, bid_id, top_k=3)

        if not retrieved or all(r.get("not_found", False) for r in retrieved):
            # No relevant chunks found
            verdict = Verdict(
                status=VerdictStatus.AMBIGUOUS,
                reason="not_found_in_bid",
                expression=f"No relevant content found for '{criterion.name}'",
            )
            vtm_row = VTMRow(
                bid_id=bid_id,
                bid_name=bid_name,
                criterion_id=criterion.id,
                criterion_name=criterion.name,
                verdict=verdict,
            )
            vtm_rows.append(vtm_row)
            continue

        # Extract values from top chunks
        extraction_results: list[tuple[str, ExtractionResult]] = []
        for chunk_result in retrieved:
            chunk_text = chunk_result.get("text", "")
            chunk_id = chunk_result.get("chunk_id", "")
            metadata = chunk_result.get("metadata", {})

            # Redact PII before LLM call
            redacted = redact_text(chunk_text, redaction_map)

            from src.extraction.value_extractor import extract_value_from_chunk
            extraction = extract_value_from_chunk(
                chunk_text=chunk_text,
                criterion_name=criterion.name,
                criterion_data_type=criterion.data_type,
                redacted_text=redacted,
                chunk_id=chunk_id,
                source_doc_type=DocType(metadata.get("doc_type", "unknown")),
                page_num=metadata.get("page_num", 0),
                ocr_confidence=metadata.get("avg_confidence", 0.0),
                redaction_map_id=redaction_map.map_id,
            )
            extraction_results.append((chunk_id, extraction))

        # Conflict detection
        conflict_input = [
            (chunk_id, ext.normalised_value, ext.source_doc_type)
            for chunk_id, ext in extraction_results
            if ext.normalised_value is not None
        ]
        conflict_resolution = detect_conflict(conflict_input)

        # Select the winning extraction
        if conflict_resolution.conflict_status == ConflictStatus.AUTO_RESOLVED:
            winning = next(
                (ext for cid, ext in extraction_results if cid == conflict_resolution.winning_chunk_id),
                extraction_results[0][1] if extraction_results else None,
            )
        elif extraction_results:
            winning = extraction_results[0][1]
        else:
            winning = None

        # Rule engine evaluation
        if winning is not None:
            verdict = evaluate(criterion, winning.normalised_value, winning.confidence)
        else:
            verdict = Verdict(
                status=VerdictStatus.AMBIGUOUS,
                reason="no_extraction",
                expression="No value could be extracted",
            )

        # Route unresolved conflicts to HITL
        if conflict_resolution.conflict_status == ConflictStatus.CONFLICT_UNRESOLVED:
            verdict = Verdict(
                status=VerdictStatus.AMBIGUOUS,
                reason="conflict_unresolved_hitl",
                expression=conflict_resolution.reason,
            )

        # Build VTM row
        vtm_row = VTMRow(
            bid_id=bid_id,
            bid_name=bid_name,
            criterion_id=criterion.id,
            criterion_name=criterion.name,
            verdict=verdict,
            source_doc_id=winning.source_doc_id if winning else "",
            source_doc_type=winning.source_doc_type if winning else DocType.UNKNOWN,
            page_num=winning.page_num if winning else 0,
            bbox=winning.source_bbox,
            raw_text=winning.raw_text if winning else "",
            redacted_text=winning.redacted_text if winning else "",
            normalised_value=winning.normalised_value if winning else None,
            ocr_confidence=winning.ocr_confidence if winning else 0.0,
            llm_confidence=winning.llm_confidence if winning else 0.0,
            conflict=conflict_resolution,
            rule_expression=verdict.expression,
            prompt_version=winning.prompt_version if winning else "",
        )

        # Write to audit chain
        audit_id = write_record("VERDICT_COMPUTED", {
            "pipeline_run_id": pipeline_run_id,
            "bid_id": bid_id,
            "criterion_id": criterion.id,
            "verdict": verdict.status.value,
            "expression": verdict.expression,
            "confidence": winning.confidence if winning else 0.0,
        })
        vtm_row.audit_record_id = audit_id

        vtm_rows.append(vtm_row)

    return vtm_rows
