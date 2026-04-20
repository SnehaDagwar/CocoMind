"""Conflict detection and resolution via doc-type hierarchy.

When top-3 retrieved chunks disagree on a value (>5% delta),
the doc-type hierarchy resolves the conflict automatically.
If the hierarchy can't resolve (e.g. two CA certs disagree) → HITL.
Conservative default (lower value) when forced.
"""

from __future__ import annotations

from src.models.documents import DocType
from src.models.verdicts import ConflictResolution, ConflictStatus

# Doc-type hierarchy: higher rank = more authoritative
_DOC_TYPE_RANK: dict[DocType, int] = {
    DocType.CA_CERTIFICATE: 5,
    DocType.AUDITED_FINANCIAL_STATEMENT: 4,
    DocType.ITR: 3,
    DocType.COVER_LETTER: 2,
    DocType.COMPANY_PROFILE: 2,
    DocType.SELF_DECLARATION: 1,
    DocType.BID_SUBMISSION: 1,
}


def _get_rank(doc_type: DocType) -> int:
    return _DOC_TYPE_RANK.get(doc_type, 0)


def detect_conflict(
    values: list[tuple[str, float, DocType]],
    delta_threshold: float = 0.05,
) -> ConflictResolution:
    """Detect and resolve conflicts among extracted values from multiple chunks.

    Args:
        values: list of (chunk_id, normalised_value, doc_type) tuples.
        delta_threshold: maximum fractional difference before considering a conflict.

    Returns:
        ConflictResolution with status and winning chunk info.
    """
    if len(values) <= 1:
        return ConflictResolution(conflict_status=ConflictStatus.NONE)

    # Check if values agree (within threshold)
    numeric_values = []
    for chunk_id, val, doc_type in values:
        try:
            numeric_values.append((chunk_id, float(val), doc_type))
        except (ValueError, TypeError):
            continue

    if len(numeric_values) <= 1:
        return ConflictResolution(conflict_status=ConflictStatus.NONE)

    # Calculate max delta as percentage
    vals_only = [v[1] for v in numeric_values]
    max_val = max(vals_only)
    min_val = min(vals_only)
    base = max(abs(max_val), 1.0)  # avoid division by zero
    delta_pct = (max_val - min_val) / base

    if delta_pct <= delta_threshold:
        return ConflictResolution(
            conflict_status=ConflictStatus.NONE,
            value_delta_pct=round(delta_pct * 100, 2),
        )

    # Conflict detected — apply doc-type hierarchy
    ranked = sorted(numeric_values, key=lambda x: _get_rank(x[2]), reverse=True)

    top_rank = _get_rank(ranked[0][2])
    top_ranked_items = [item for item in ranked if _get_rank(item[2]) == top_rank]

    if len(top_ranked_items) == 1:
        # Hierarchy resolves: single winner
        winner = top_ranked_items[0]
        losers = [item[0] for item in ranked if item[0] != winner[0]]
        return ConflictResolution(
            conflict_status=ConflictStatus.AUTO_RESOLVED,
            winning_doc_type=winner[2],
            winning_chunk_id=winner[0],
            losing_chunk_ids=losers,
            reason=f"Doc-type hierarchy: {winner[2].value} (rank {top_rank}) wins",
            value_delta_pct=round(delta_pct * 100, 2),
        )

    # Multiple items at same rank — check if they agree
    top_vals = [item[1] for item in top_ranked_items]
    top_base = max(abs(max(top_vals)), 1.0)
    top_delta = (max(top_vals) - min(top_vals)) / top_base

    if top_delta <= delta_threshold:
        # Same-rank items agree
        winner = top_ranked_items[0]
        losers = [item[0] for item in ranked if item[0] != winner[0]]
        return ConflictResolution(
            conflict_status=ConflictStatus.AUTO_RESOLVED,
            winning_doc_type=winner[2],
            winning_chunk_id=winner[0],
            losing_chunk_ids=losers,
            reason=f"Same-rank docs agree (delta {top_delta:.2%})",
            value_delta_pct=round(delta_pct * 100, 2),
        )

    # Same-rank items disagree — HITL with conservative lower value
    conservative = min(top_ranked_items, key=lambda x: x[1])
    others = [item[0] for item in top_ranked_items if item[0] != conservative[0]]

    return ConflictResolution(
        conflict_status=ConflictStatus.CONFLICT_UNRESOLVED,
        winning_doc_type=conservative[2],
        winning_chunk_id=conservative[0],
        losing_chunk_ids=others,
        reason=(
            f"Unresolved: {len(top_ranked_items)} docs at rank {top_rank} disagree "
            f"(delta {top_delta:.2%}). Conservative lower value used pending HITL."
        ),
        value_delta_pct=round(delta_pct * 100, 2),
    )
