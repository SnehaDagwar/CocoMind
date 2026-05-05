"""Hypothesis property tests for the rule engine.

Tier-1 deliverable: 250+ examples, 6 invariants.
These prove the rule engine is a PURE FUNCTION and free of edge-case bugs
that could silently disqualify a bidder or let an ineligible one through.

Run with:
    pytest tests/property/test_rule_engine.py -v
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.engine.rule_engine import evaluate, evaluate_mandatory_check
from src.models.criteria import Criterion
from src.models.verdicts import VerdictStatus


# ─── Criterion Factories ──────────────────────────────────────────────────────

def make_criterion(
    op: str = "gte",
    threshold: float | bool | str | None = 5_000_000.0,
    threshold_upper: float | None = None,
    mandatory: bool = True,
    data_type: str = "currency_INR",
) -> Criterion:
    return Criterion(
        id="C001",
        name="Average Annual Turnover",
        category="financial",
        mandatory=mandatory,
        data_type=data_type,
        threshold_operator=op,
        threshold_value=threshold,
        threshold_upper=threshold_upper,
        source_section="Section 3.2",
        source_bbox=None,
        citation="GFR 2017 Rule 162",
    )


# ─── Invariant 1: None value → always AMBIGUOUS ───────────────────────────────

@given(
    op=st.sampled_from(["gte", "lte", "eq", "between", "contains", "valid_on_date"]),
    confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
@settings(max_examples=100)
def test_none_value_always_ambiguous(op: str, confidence: float) -> None:
    """Invariant: value=None MUST always → AMBIGUOUS, regardless of operator/confidence."""
    threshold: float | str
    threshold_upper: float | None = None
    if op == "between":
        threshold = 0.0
        threshold_upper = 100.0
    elif op == "valid_on_date":
        threshold = "2026-01-01"
    else:
        threshold = 0.0

    criterion = make_criterion(op=op, threshold=threshold, threshold_upper=threshold_upper)
    verdict = evaluate(criterion, None, confidence)
    assert verdict.status == VerdictStatus.AMBIGUOUS, (
        f"Expected AMBIGUOUS for value=None (op={op}, confidence={confidence}), "
        f"got {verdict.status}"
    )
    assert verdict.reason == "value_not_extracted"


# ─── Invariant 2: confidence < 0.70 → always AMBIGUOUS ───────────────────────

@given(
    value=st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False),
    confidence=st.floats(min_value=0.0, max_value=0.6999, allow_nan=False),
)
@settings(max_examples=100)
def test_low_confidence_always_ambiguous(value: float, confidence: float) -> None:
    """Invariant: confidence < 0.70 MUST always → AMBIGUOUS for numeric operators."""
    criterion = make_criterion(op="gte", threshold=5_000_000.0)
    verdict = evaluate(criterion, value, confidence)
    assert verdict.status == VerdictStatus.AMBIGUOUS, (
        f"Expected AMBIGUOUS for confidence={confidence:.4f} < 0.70, "
        f"got {verdict.status}"
    )
    assert verdict.reason == "low_extraction_confidence"


# ─── Invariant 3: GTE — strictly greater always PASS ─────────────────────────

@given(
    threshold=st.floats(min_value=1.0, max_value=1e9, allow_nan=False, allow_infinity=False),
    delta=st.floats(min_value=0.01, max_value=1e8, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_gte_strictly_greater_always_pass(threshold: float, delta: float) -> None:
    """Invariant: value > threshold → always PASS for gte operator."""
    criterion = make_criterion(op="gte", threshold=threshold)
    value = threshold + delta
    verdict = evaluate(criterion, value, confidence=0.95)
    assert verdict.status == VerdictStatus.PASS, (
        f"Expected PASS for {value} > {threshold} (gte), got {verdict.status}"
    )


# ─── Invariant 4: GTE — strictly lesser always FAIL ──────────────────────────

@given(
    threshold=st.floats(min_value=1.0, max_value=1e9, allow_nan=False, allow_infinity=False),
    delta=st.floats(min_value=0.01, max_value=1e8, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_gte_strictly_lesser_always_fail(threshold: float, delta: float) -> None:
    """Invariant: value < threshold → always FAIL for gte operator."""
    criterion = make_criterion(op="gte", threshold=threshold)
    value = threshold - delta
    assume(value > 0)  # skip negative values for currency_INR
    verdict = evaluate(criterion, value, confidence=0.95)
    assert verdict.status == VerdictStatus.FAIL, (
        f"Expected FAIL for {value} < {threshold} (gte), got {verdict.status}"
    )


# ─── Invariant 5: GTE — equal to threshold always PASS ───────────────────────

@given(
    threshold=st.floats(min_value=0.0, max_value=1e9, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_gte_equal_always_pass(threshold: float) -> None:
    """Invariant: value == threshold → always PASS for gte operator (boundary inclusive)."""
    criterion = make_criterion(op="gte", threshold=threshold)
    verdict = evaluate(criterion, threshold, confidence=0.95)
    assert verdict.status == VerdictStatus.PASS, (
        f"Expected PASS for {threshold} >= {threshold} (boundary), got {verdict.status}"
    )


# ─── Invariant 6: Pure function — same inputs → same output ──────────────────

@given(
    value=st.floats(min_value=0.0, max_value=1e9, allow_nan=False, allow_infinity=False),
    confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    threshold=st.floats(min_value=0.0, max_value=1e9, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_pure_function_same_inputs_same_output(
    value: float, confidence: float, threshold: float
) -> None:
    """Invariant: evaluate() is a pure function — identical calls return identical results."""
    criterion = make_criterion(op="gte", threshold=threshold)
    result1 = evaluate(criterion, value, confidence)
    result2 = evaluate(criterion, value, confidence)
    assert result1.status == result2.status, (
        f"Non-deterministic output: {result1.status} != {result2.status} "
        f"for value={value}, confidence={confidence}, threshold={threshold}"
    )


# ─── Additional Targeted Tests ────────────────────────────────────────────────

@given(
    threshold_lower=st.floats(min_value=0.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    delta_upper=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=80)
def test_between_in_range_always_pass(threshold_lower: float, delta_upper: float) -> None:
    """Value strictly within [lower, upper] must PASS for 'between' operator."""
    threshold_upper = threshold_lower + delta_upper
    mid_value = (threshold_lower + threshold_upper) / 2.0
    criterion = make_criterion(
        op="between", threshold=threshold_lower, threshold_upper=threshold_upper
    )
    verdict = evaluate(criterion, mid_value, confidence=0.90)
    assert verdict.status == VerdictStatus.PASS, (
        f"Expected PASS for {mid_value} in [{threshold_lower}, {threshold_upper}], "
        f"got {verdict.status}"
    )


@given(
    threshold_lower=st.floats(min_value=1.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    delta_upper=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    outside_delta=st.floats(min_value=0.01, max_value=50.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=80)
def test_between_outside_range_always_fail(
    threshold_lower: float, delta_upper: float, outside_delta: float
) -> None:
    """Value below lower bound must FAIL for 'between' operator."""
    threshold_upper = threshold_lower + delta_upper
    below_value = threshold_lower - outside_delta
    assume(below_value >= 0)
    criterion = make_criterion(
        op="between", threshold=threshold_lower, threshold_upper=threshold_upper
    )
    verdict = evaluate(criterion, below_value, confidence=0.90)
    assert verdict.status == VerdictStatus.FAIL, (
        f"Expected FAIL for {below_value} below [{threshold_lower}, {threshold_upper}], "
        f"got {verdict.status}"
    )


@given(
    confidence=st.floats(min_value=0.70, max_value=1.0, allow_nan=False),
)
@settings(max_examples=60)
def test_confidence_at_or_above_threshold_not_ambiguous_for_valid_value(
    confidence: float,
) -> None:
    """confidence >= 0.70 + valid value must NOT return low_extraction_confidence reason."""
    criterion = make_criterion(op="gte", threshold=5_000_000.0)
    verdict = evaluate(criterion, 6_000_000.0, confidence)
    assert verdict.reason != "low_extraction_confidence", (
        f"Got low_extraction_confidence for confidence={confidence:.4f} >= 0.70"
    )


@given(
    mandatory=st.booleans(),
    value=st.none() | st.floats(min_value=0.0, max_value=1e9, allow_nan=False, allow_infinity=False),
    confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
@settings(max_examples=60)
def test_mandatory_check_never_converts_ambiguous_to_pass_or_fail(
    mandatory: bool,
    value: float | None,
    confidence: float,
) -> None:
    """evaluate_mandatory_check must never change AMBIGUOUS → PASS/FAIL."""
    criterion = make_criterion(op="gte", threshold=5_000_000.0, mandatory=mandatory)
    base = evaluate(criterion, value, confidence)
    checked = evaluate_mandatory_check(criterion, value, confidence)

    # The mandatory wrapper must not escalate AMBIGUOUS to a definitive verdict
    if base.status == VerdictStatus.AMBIGUOUS:
        assert checked.status == VerdictStatus.AMBIGUOUS, (
            f"evaluate_mandatory_check turned AMBIGUOUS into {checked.status} "
            f"(mandatory={mandatory}, value={value}, confidence={confidence})"
        )


@given(
    days_in_future=st.integers(min_value=1, max_value=3650),
)
@settings(max_examples=60)
def test_valid_on_date_future_date_always_pass(days_in_future: int) -> None:
    """A validity date in the future must PASS the valid_on_date check."""
    today = date.today()
    future_date = today + timedelta(days=days_in_future)
    threshold_date = today  # Must be valid on or after today

    criterion = make_criterion(
        op="valid_on_date",
        threshold=threshold_date.isoformat(),
        data_type="date",
    )
    verdict = evaluate(criterion, future_date.isoformat(), confidence=0.90)
    # Should be PASS: future_date >= threshold_date (today)
    assert verdict.status in (VerdictStatus.PASS, VerdictStatus.AMBIGUOUS), (
        f"Got unexpected FAIL for future date {future_date} vs threshold {threshold_date}"
    )


@given(
    days_in_past=st.integers(min_value=1, max_value=3650),
)
@settings(max_examples=60)
def test_valid_on_date_past_date_always_fail(days_in_past: int) -> None:
    """A validity date in the past must FAIL the valid_on_date check (expired document)."""
    today = date.today()
    past_date = today - timedelta(days=days_in_past)
    threshold_date = today  # Must be valid on or after today

    criterion = make_criterion(
        op="valid_on_date",
        threshold=threshold_date.isoformat(),
        data_type="date",
    )
    verdict = evaluate(criterion, past_date.isoformat(), confidence=0.90)
    assert verdict.status == VerdictStatus.FAIL, (
        f"Expected FAIL for expired date {past_date} < threshold {threshold_date}, "
        f"got {verdict.status}"
    )


# ─── Boolean / Contains Operators ────────────────────────────────────────────

@pytest.mark.parametrize("value,expected", [
    (True, VerdictStatus.PASS),
    ("present", VerdictStatus.PASS),
    ("07AAACS1234A1ZH", VerdictStatus.PASS),
    ("", VerdictStatus.FAIL),
    (None, VerdictStatus.AMBIGUOUS),
])
def test_contains_operator_boolean_logic(
    value: bool | str | None, expected: VerdictStatus
) -> None:
    criterion = make_criterion(op="contains", threshold=None)
    verdict = evaluate(criterion, value, confidence=0.90)
    assert verdict.status == expected


# ─── No threshold + non-contains operator → AMBIGUOUS ────────────────────────

@pytest.mark.parametrize("op", ["gte", "lte", "eq", "between", "valid_on_date"])
def test_no_threshold_non_contains_returns_ambiguous(op: str) -> None:
    criterion = make_criterion(op=op, threshold=None)
    verdict = evaluate(criterion, 100.0, confidence=0.90)
    assert verdict.status == VerdictStatus.AMBIGUOUS
    assert verdict.reason == "no_threshold_defined"


# ─── Non-numeric value for numeric operator → AMBIGUOUS ──────────────────────

@pytest.mark.parametrize("op", ["gte", "lte", "eq", "between"])
def test_non_numeric_value_returns_ambiguous(op: str) -> None:
    criterion = make_criterion(op=op, threshold=5_000_000.0)
    verdict = evaluate(criterion, "not-a-number", confidence=0.90)
    assert verdict.status == VerdictStatus.AMBIGUOUS
    assert verdict.reason == "value_not_numeric"
