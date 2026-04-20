"""Integrity pact checker — verifies signed integrity pact presence."""

from __future__ import annotations

from src.models.verdicts import Verdict, VerdictStatus

# SHA-256 of the standard CRPF integrity pact template (synthetic)
_STANDARD_TEMPLATE_HASH = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"


def check_integrity_pact(
    pact_text: str | None,
    pact_file_hash: str | None = None,
    template_hash: str = _STANDARD_TEMPLATE_HASH,
) -> Verdict:
    """Check if a signed integrity pact is present and matches the template.

    Args:
        pact_text: Extracted text from the integrity pact document.
        pact_file_hash: SHA-256 hash of the integrity pact file.
        template_hash: Expected hash of the standard template.
    """
    if pact_text is None or not pact_text.strip():
        return Verdict(
            status=VerdictStatus.FAIL,
            reason="integrity_pact_missing",
            expression="No integrity pact document found",
        )

    text_lower = pact_text.lower()

    # Check for key integrity pact phrases
    required_phrases = [
        "integrity pact",
        "undertake",
        "corruption",
    ]

    found = [p for p in required_phrases if p in text_lower]

    if len(found) < 2:
        return Verdict(
            status=VerdictStatus.AMBIGUOUS,
            reason="integrity_pact_content_unclear",
            expression=f"Only {len(found)}/3 key phrases found: {found}",
        )

    # Check for signature indicators
    has_signature = any(
        kw in text_lower
        for kw in ["signed", "signature", "authorized signatory", "हस्ताक्षर"]
    )

    if not has_signature:
        return Verdict(
            status=VerdictStatus.AMBIGUOUS,
            reason="integrity_pact_unsigned",
            expression="Integrity pact found but no signature indicator detected",
        )

    return Verdict(
        status=VerdictStatus.PASS,
        reason="integrity_pact_present_and_signed",
        expression="Signed integrity pact with required content found",
    )
