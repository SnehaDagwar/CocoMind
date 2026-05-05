"""Custom Presidio EntityRecognizer subclasses for Indian PII.

Each recogniser uses regex + validation (e.g. Verhoeff checksum for Aadhaar)
to minimise false positives. These are registered into the Presidio Analyzer.
"""

from __future__ import annotations

import re

from presidio_analyzer import (
    EntityRecognizer,
    RecognizerResult,
)

# ─── Verhoeff checksum for Aadhaar ───────────────────────────────────────────

_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

_VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def _verhoeff_checksum(number: str) -> bool:
    """Validate a number string using the Verhoeff algorithm."""
    c = 0
    digits = [int(d) for d in reversed(number)]
    for i, digit in enumerate(digits):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][digit]]
    return c == 0


# ─── Recognisers ─────────────────────────────────────────────────────────────

class AadhaarRecognizer(EntityRecognizer):
    """Detect Indian Aadhaar numbers (12 digits with Verhoeff checksum)."""

    PATTERN = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
    ENTITIES = ["AADHAAR"]

    def __init__(self) -> None:
        super().__init__(
            supported_entities=self.ENTITIES,
            supported_language="en",
            name="AadhaarRecognizer",
        )

    def load(self) -> None:  # type: ignore[override]
        pass

    def analyze(  # type: ignore[override]
        self, text: str, entities: list[str], nlp_artifacts: object | None = None, **kwargs: object
    ) -> list[RecognizerResult]:
        results: list[RecognizerResult] = []
        for match in self.PATTERN.finditer(text):
            digits_only = re.sub(r"\s", "", match.group())
            if len(digits_only) == 12 and _verhoeff_checksum(digits_only):
                results.append(
                    RecognizerResult(
                        entity_type="AADHAAR",
                        start=match.start(),
                        end=match.end(),
                        score=0.95,
                    )
                )
        return results


class PANRecognizer(EntityRecognizer):
    """Detect Indian PAN (Permanent Account Number): ABCDE1234F."""

    PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
    ENTITIES = ["IN_PAN"]

    def __init__(self) -> None:
        super().__init__(
            supported_entities=self.ENTITIES,
            supported_language="en",
            name="PANRecognizer",
        )

    def load(self) -> None:  # type: ignore[override]
        pass

    def analyze(  # type: ignore[override]
        self, text: str, entities: list[str], nlp_artifacts: object | None = None, **kwargs: object
    ) -> list[RecognizerResult]:
        results: list[RecognizerResult] = []
        for match in self.PATTERN.finditer(text):
            results.append(
                RecognizerResult(
                    entity_type="IN_PAN",
                    start=match.start(),
                    end=match.end(),
                    score=0.90,
                )
            )
        return results


class GSTINRecognizer(EntityRecognizer):
    """Detect GSTIN: 2-digit state code + PAN + entity code + check digit."""

    PATTERN = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z\d][A-Z]\b")
    ENTITIES = ["IN_GSTIN"]

    def __init__(self) -> None:
        super().__init__(
            supported_entities=self.ENTITIES,
            supported_language="en",
            name="GSTINRecognizer",
        )

    def load(self) -> None:  # type: ignore[override]
        pass

    def analyze(  # type: ignore[override]
        self, text: str, entities: list[str], nlp_artifacts: object | None = None, **kwargs: object
    ) -> list[RecognizerResult]:
        results: list[RecognizerResult] = []
        for match in self.PATTERN.finditer(text):
            gstin = match.group()
            state_code = int(gstin[:2])
            if 1 <= state_code <= 37:
                results.append(
                    RecognizerResult(
                        entity_type="IN_GSTIN",
                        start=match.start(),
                        end=match.end(),
                        score=0.92,
                    )
                )
        return results


class EPFORecognizer(EntityRecognizer):
    """Detect EPFO establishment codes: XX/XXX/NNNNNNN/NNN/NNNN."""

    PATTERN = re.compile(r"\b[A-Z]{2}/[A-Z]{3}/\d{7}/\d{3}/\d{4}\b")
    ENTITIES = ["IN_EPFO"]

    def __init__(self) -> None:
        super().__init__(
            supported_entities=self.ENTITIES,
            supported_language="en",
            name="EPFORecognizer",
        )

    def load(self) -> None:  # type: ignore[override]
        pass

    def analyze(  # type: ignore[override]
        self, text: str, entities: list[str], nlp_artifacts: object | None = None, **kwargs: object
    ) -> list[RecognizerResult]:
        return [
            RecognizerResult(
                entity_type="IN_EPFO",
                start=m.start(),
                end=m.end(),
                score=0.88,
            )
            for m in self.PATTERN.finditer(text)
        ]


class ESICRecognizer(EntityRecognizer):
    """Detect ESIC registration numbers (17-digit)."""

    PATTERN = re.compile(r"\b\d{17}\b")
    ENTITIES = ["IN_ESIC"]

    def __init__(self) -> None:
        super().__init__(
            supported_entities=self.ENTITIES,
            supported_language="en",
            name="ESICRecognizer",
        )

    def load(self) -> None:  # type: ignore[override]
        pass

    def analyze(  # type: ignore[override]
        self, text: str, entities: list[str], nlp_artifacts: object | None = None, **kwargs: object
    ) -> list[RecognizerResult]:
        return [
            RecognizerResult(
                entity_type="IN_ESIC",
                start=m.start(),
                end=m.end(),
                score=0.75,
            )
            for m in self.PATTERN.finditer(text)
        ]


class IFSCRecognizer(EntityRecognizer):
    """Detect IFSC codes: 4 alpha + 0 + 6 alphanumeric."""

    PATTERN = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
    ENTITIES = ["IN_IFSC"]

    def __init__(self) -> None:
        super().__init__(
            supported_entities=self.ENTITIES,
            supported_language="en",
            name="IFSCRecognizer",
        )

    def load(self) -> None:  # type: ignore[override]
        pass

    def analyze(  # type: ignore[override]
        self, text: str, entities: list[str], nlp_artifacts: object | None = None, **kwargs: object
    ) -> list[RecognizerResult]:
        return [
            RecognizerResult(
                entity_type="IN_IFSC",
                start=m.start(),
                end=m.end(),
                score=0.85,
            )
            for m in self.PATTERN.finditer(text)
        ]
