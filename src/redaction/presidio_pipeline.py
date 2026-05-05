"""PII redaction pipeline using Microsoft Presidio + custom Indian recognisers.

Runs AFTER OCR and BEFORE any LLM call. No exceptions.
Reversible tokenisation with UUID tokens mapped in an encrypted RedactionMap.
"""

from __future__ import annotations

import uuid

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from src.models.documents import BBox
from src.models.extraction import RedactionMap, RedactionMapEntry
from src.redaction.indian_recognizers import (
    AadhaarRecognizer,
    EPFORecognizer,
    ESICRecognizer,
    GSTINRecognizer,
    IFSCRecognizer,
    PANRecognizer,
)

# Singleton engines (thread-safe in Presidio)
_analyzer: AnalyzerEngine | None = None
_anonymizer: AnonymizerEngine | None = None


def _get_analyzer() -> AnalyzerEngine:
    """Lazy-init Presidio Analyzer with custom Indian recognisers."""
    global _analyzer
    if _analyzer is None:
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()

        # Register custom Indian PII recognisers
        registry.add_recognizer(AadhaarRecognizer())
        registry.add_recognizer(PANRecognizer())
        registry.add_recognizer(GSTINRecognizer())
        registry.add_recognizer(EPFORecognizer())
        registry.add_recognizer(ESICRecognizer())
        registry.add_recognizer(IFSCRecognizer())

        _analyzer = AnalyzerEngine(registry=registry)
    return _analyzer


def _get_anonymizer() -> AnonymizerEngine:
    """Lazy-init Presidio Anonymizer."""
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
    return _anonymizer


def redact_text(
    text: str,
    redaction_map: RedactionMap,
    page_num: int = 0,
    bbox: BBox | None = None,
    language: str = "en",
) -> str:
    """Redact PII from text using Presidio + custom recognisers.

    Returns the redacted text with UUID replacement tokens.
    Updates the redaction_map in-place with each replaced entity.
    """
    analyzer = _get_analyzer()
    anonymizer = _get_anonymizer()

    # Analyse text for PII entities
    results = analyzer.analyze(
        text=text,
        language=language,
        entities=[
            "AADHAAR",
            "IN_PAN",
            "IN_GSTIN",
            "IN_EPFO",
            "IN_ESIC",
            "IN_IFSC",
            "PERSON",
            "PHONE_NUMBER",
            "EMAIL_ADDRESS",
        ],
    )

    if not results:
        return text

    # Build replacement operators — one UUID per entity found
    operators: dict[str, OperatorConfig] = {}
    for result in results:
        token = f"<REDACTED_{uuid.uuid4().hex[:12]}>"

        redaction_map.entries.append(
            RedactionMapEntry(
                entity_type=result.entity_type,
                token=token,
                page_num=page_num,
                bbox=bbox,
            )
        )

        # Use replace operator with the UUID token
        operators[result.entity_type] = OperatorConfig(
            "replace", {"new_value": token}
        )

    # If any entity type wasn't given an operator, use a generic one
    operators["DEFAULT"] = OperatorConfig(
        "replace", {"new_value": "<REDACTED>"}
    )

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators,
    )

    return anonymized.text


def create_redaction_map() -> RedactionMap:
    """Create a fresh RedactionMap for a pipeline run."""
    return RedactionMap(
        map_id=uuid.uuid4().hex,
        entries=[],
        encryption_key_id="",  # Set when encrypting at rest
    )
