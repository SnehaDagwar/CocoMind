"""Near-relations checker — mandatory self-declaration affidavit parsing.

Bidders must declare they have no near-relations in CRPF.
Missing or inconsistent declaration → HITL.
"""

from __future__ import annotations

from src.models.verdicts import Verdict, VerdictStatus

_DECLARATION_KEYWORDS = [
    "no near relation",
    "no relative",
    "not related",
    "no near relations",
    "declare that none",
    "hereby declare",
    "निकट संबंधी नहीं",
]


def check_near_relations(
    declaration_text: str,
    bidder_name: str = "",
) -> Verdict:
    """Check the near-relations self-declaration.

    Looks for explicit declaration keywords.
    Missing or ambiguous declaration → HITL.
    """
    if not declaration_text or not declaration_text.strip():
        return Verdict(
            status=VerdictStatus.AMBIGUOUS,
            reason="near_relations_declaration_missing",
            expression="No near-relations declaration text found",
        )

    text_lower = declaration_text.lower()

    # Check for declaration keywords
    found_keywords = [kw for kw in _DECLARATION_KEYWORDS if kw in text_lower]

    if found_keywords:
        return Verdict(
            status=VerdictStatus.PASS,
            reason="near_relations_declared_none",
            expression=f"Declaration found: '{found_keywords[0]}'",
        )

    # Check for contradictory statements
    has_relation_mention = any(
        word in text_lower
        for word in ["son of", "daughter of", "spouse of", "brother of", "sister of"]
    )

    if has_relation_mention:
        return Verdict(
            status=VerdictStatus.AMBIGUOUS,
            reason="near_relations_possible_relation_mentioned",
            expression="Possible relation mentioned in declaration — needs HITL review",
        )

    return Verdict(
        status=VerdictStatus.AMBIGUOUS,
        reason="near_relations_declaration_unclear",
        expression="Declaration text present but keywords not found — needs HITL review",
    )
