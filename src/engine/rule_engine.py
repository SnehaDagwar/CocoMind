"""Rule engine — the legal defensibility core.

Pure Python. Zero LLM imports. Property-tested with Hypothesis.
CI enforces this via import-linter: src.engine cannot import anthropic/openai/langchain.

The LLM extracts + normalises text → numbers/booleans.
This module decides PASS / FAIL / AMBIGUOUS from deterministic rules.
"""

from __future__ import annotations

from datetime import date, datetime

from src.models.criteria import Criterion
from src.models.verdicts import Verdict, VerdictStatus


def evaluate(
    criterion: Criterion,
    value: float | bool | str | None,
    confidence: float,
) -> Verdict:
    """Evaluate a single criterion against an extracted value.

    Decision rules (in priority order):
    1. value is None → AMBIGUOUS (value_not_extracted)
    2. confidence < 0.70 → AMBIGUOUS (low_extraction_confidence)
    3. Apply threshold_operator to determine PASS/FAIL

    This function is a PURE FUNCTION: same inputs → same output.
    It imports nothing from any LLM SDK.

    Args:
        criterion: The eligibility criterion from the NIT.
        value: The normalised value extracted from the bid.
        confidence: The extraction confidence (0.0–1.0).

    Returns:
        Verdict with status and a human-readable expression.
    """
    # Rule 1: No value extracted
    if value is None:
        return Verdict(
            status=VerdictStatus.AMBIGUOUS,
            reason="value_not_extracted",
            expression="value=None",
        )

    # Rule 2: Low confidence
    if confidence < 0.70:
        return Verdict(
            status=VerdictStatus.AMBIGUOUS,
            reason="low_extraction_confidence",
            expression=f"confidence={confidence:.2f} < 0.70",
        )

    op = criterion.threshold_operator
    threshold = criterion.threshold_value

    # If no threshold is set, we can only check presence
    if threshold is None:
        if op == "contains":
            passed = bool(value)
            return Verdict(
                status=VerdictStatus.PASS if passed else VerdictStatus.FAIL,
                expression=f"bool({value!r}) = {passed}",
            )
        return Verdict(
            status=VerdictStatus.AMBIGUOUS,
            reason="no_threshold_defined",
            expression=f"threshold=None, op={op}",
        )

    # Numeric operators
    if op == "gte":
        try:
            v = float(value)  # type: ignore[arg-type]
            t = float(threshold)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            return Verdict(
                status=VerdictStatus.AMBIGUOUS,
                reason="value_not_numeric",
                expression=f"cannot compare {value!r} gte {threshold!r}",
            )
        passed = v >= t
        return Verdict(
            status=VerdictStatus.PASS if passed else VerdictStatus.FAIL,
            expression=f"{v} >= {t}",
        )

    if op == "lte":
        try:
            v = float(value)  # type: ignore[arg-type]
            t = float(threshold)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            return Verdict(
                status=VerdictStatus.AMBIGUOUS,
                reason="value_not_numeric",
                expression=f"cannot compare {value!r} lte {threshold!r}",
            )
        passed = v <= t
        return Verdict(
            status=VerdictStatus.PASS if passed else VerdictStatus.FAIL,
            expression=f"{v} <= {t}",
        )

    if op == "eq":
        try:
            v = float(value)  # type: ignore[arg-type]
            t = float(threshold)  # type: ignore[arg-type]
            passed = v == t
        except (ValueError, TypeError):
            # Fall back to string equality
            passed = str(value) == str(threshold)
        return Verdict(
            status=VerdictStatus.PASS if passed else VerdictStatus.FAIL,
            expression=f"{value!r} == {threshold!r}",
        )

    if op == "between":
        try:
            v = float(value)  # type: ignore[arg-type]
            t_lower = float(threshold)  # type: ignore[arg-type]
            t_upper = float(criterion.threshold_upper) if criterion.threshold_upper is not None else t_lower
        except (ValueError, TypeError):
            return Verdict(
                status=VerdictStatus.AMBIGUOUS,
                reason="value_not_numeric",
                expression=f"cannot compare {value!r} between {threshold!r} and {criterion.threshold_upper!r}",
            )
        passed = t_lower <= v <= t_upper
        return Verdict(
            status=VerdictStatus.PASS if passed else VerdictStatus.FAIL,
            expression=f"{t_lower} <= {v} <= {t_upper}",
        )

    if op == "contains":
        passed = bool(value)
        return Verdict(
            status=VerdictStatus.PASS if passed else VerdictStatus.FAIL,
            expression=f"bool({value!r}) = {passed}",
        )

    if op == "valid_on_date":
        try:
            # Parse date strings
            v_date = _parse_date(value) if isinstance(value, str) else None

            t_date = _parse_date(threshold) if isinstance(threshold, str) else None

            if v_date is None or t_date is None:
                return Verdict(
                    status=VerdictStatus.AMBIGUOUS,
                    reason="date_parse_error",
                    expression=f"cannot parse dates: {value!r} vs {threshold!r}",
                )

            passed = v_date >= t_date
            return Verdict(
                status=VerdictStatus.PASS if passed else VerdictStatus.FAIL,
                expression=f"{v_date.isoformat()} >= {t_date.isoformat()}",
            )
        except Exception:
            return Verdict(
                status=VerdictStatus.AMBIGUOUS,
                reason="date_comparison_error",
                expression=f"error comparing {value!r} vs {threshold!r}",
            )

    # Unknown operator
    return Verdict(
        status=VerdictStatus.AMBIGUOUS,
        reason=f"unknown_operator_{op}",
        expression=f"unknown op={op}",
    )


def _parse_date(value: str) -> date | None:
    """Try to parse a date string in common formats."""
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def evaluate_mandatory_check(
    criterion: Criterion,
    value: float | bool | str | None,
    confidence: float,
) -> Verdict:
    """Evaluate with mandatory flag awareness.

    If a mandatory criterion gets AMBIGUOUS → it stays AMBIGUOUS (routes to HITL).
    If an optional criterion gets AMBIGUOUS → still AMBIGUOUS but with different reason.
    """
    verdict = evaluate(criterion, value, confidence)

    if verdict.status == VerdictStatus.AMBIGUOUS and not criterion.mandatory:
        verdict.reason = f"optional_criterion_ambiguous: {verdict.reason}"

    return verdict
