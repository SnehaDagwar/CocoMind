"""Tests for the rule engine — pure Python, LLM-free.

Uses Hypothesis for property-based testing.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from src.engine.rule_engine import _parse_date, evaluate, evaluate_mandatory_check
from src.models.criteria import Criterion
from src.models.verdicts import VerdictStatus

# ─── Unit tests ──────────────────────────────────────────────────────────────

class TestEvaluateGte:
    """Tests for gte (greater-than-or-equal) operator."""

    def _criterion(self, threshold: float) -> Criterion:
        return Criterion(
            id="C001",
            name="Annual Turnover",
            category="financial",
            mandatory=True,
            data_type="currency_INR",
            threshold_value=threshold,
            threshold_operator="gte",
        )

    def test_pass_above_threshold(self) -> None:
        v = evaluate(self._criterion(50_000_000), 60_000_000, confidence=0.95)
        assert v.status == VerdictStatus.PASS

    def test_pass_at_threshold(self) -> None:
        v = evaluate(self._criterion(50_000_000), 50_000_000, confidence=0.95)
        assert v.status == VerdictStatus.PASS

    def test_fail_below_threshold(self) -> None:
        v = evaluate(self._criterion(50_000_000), 40_000_000, confidence=0.95)
        assert v.status == VerdictStatus.FAIL

    def test_ambiguous_none_value(self) -> None:
        v = evaluate(self._criterion(50_000_000), None, confidence=0.95)
        assert v.status == VerdictStatus.AMBIGUOUS
        assert v.reason == "value_not_extracted"

    def test_ambiguous_low_confidence(self) -> None:
        v = evaluate(self._criterion(50_000_000), 60_000_000, confidence=0.55)
        assert v.status == VerdictStatus.AMBIGUOUS
        assert v.reason == "low_extraction_confidence"

    def test_ambiguous_non_numeric(self) -> None:
        v = evaluate(self._criterion(50_000_000), "not a number", confidence=0.95)
        assert v.status == VerdictStatus.AMBIGUOUS


class TestEvaluateLte:
    """Tests for lte (less-than-or-equal) operator."""

    def _criterion(self, threshold: float) -> Criterion:
        return Criterion(
            id="C002",
            name="Max Price",
            category="financial",
            mandatory=True,
            data_type="currency_INR",
            threshold_value=threshold,
            threshold_operator="lte",
        )

    def test_pass_below(self) -> None:
        v = evaluate(self._criterion(100), 80, confidence=0.95)
        assert v.status == VerdictStatus.PASS

    def test_fail_above(self) -> None:
        v = evaluate(self._criterion(100), 120, confidence=0.95)
        assert v.status == VerdictStatus.FAIL


class TestEvaluateContains:
    """Tests for contains (boolean presence) operator."""

    def _criterion(self) -> Criterion:
        return Criterion(
            id="C003",
            name="GST Registration",
            category="compliance",
            mandatory=True,
            data_type="boolean",
            threshold_operator="contains",
        )

    def test_pass_truthy(self) -> None:
        v = evaluate(self._criterion(), True, confidence=0.95)
        assert v.status == VerdictStatus.PASS

    def test_fail_falsy(self) -> None:
        v = evaluate(self._criterion(), False, confidence=0.95)
        assert v.status == VerdictStatus.FAIL

    def test_pass_nonempty_string(self) -> None:
        v = evaluate(self._criterion(), "07AAACS1234A1ZH", confidence=0.95)
        assert v.status == VerdictStatus.PASS


class TestEvaluateDate:
    """Tests for valid_on_date operator."""

    def test_valid_date(self) -> None:
        criterion = Criterion(
            id="C004",
            name="Certificate Validity",
            category="document",
            mandatory=True,
            data_type="date",
            threshold_value="2025-01-01",
            threshold_operator="valid_on_date",
        )
        v = evaluate(criterion, "2026-06-15", confidence=0.90)
        assert v.status == VerdictStatus.PASS

    def test_expired_date(self) -> None:
        criterion = Criterion(
            id="C004",
            name="Certificate Validity",
            category="document",
            mandatory=True,
            data_type="date",
            threshold_value="2025-01-01",
            threshold_operator="valid_on_date",
        )
        v = evaluate(criterion, "2024-06-15", confidence=0.90)
        assert v.status == VerdictStatus.FAIL


class TestParseDateFormats:
    """Test date parsing across common Indian formats."""

    def test_iso_format(self) -> None:
        assert _parse_date("2025-06-15") is not None

    def test_indian_format(self) -> None:
        assert _parse_date("15-06-2025") is not None

    def test_slash_format(self) -> None:
        assert _parse_date("15/06/2025") is not None

    def test_dot_format(self) -> None:
        assert _parse_date("15.06.2025") is not None

    def test_invalid_format(self) -> None:
        assert _parse_date("June 15, 2025") is None


class TestMandatoryCheck:
    """Test mandatory vs optional criterion handling."""

    def test_mandatory_ambiguous_stays_ambiguous(self) -> None:
        c = Criterion(
            id="C010",
            name="Turnover",
            category="financial",
            mandatory=True,
            data_type="currency_INR",
            threshold_value=50_000_000,
            threshold_operator="gte",
        )
        v = evaluate_mandatory_check(c, None, confidence=0.95)
        assert v.status == VerdictStatus.AMBIGUOUS
        assert "optional" not in v.reason

    def test_optional_ambiguous_has_optional_reason(self) -> None:
        c = Criterion(
            id="C011",
            name="ISO Cert",
            category="document",
            mandatory=False,
            data_type="boolean",
            threshold_value=True,
            threshold_operator="contains",
        )
        v = evaluate_mandatory_check(c, None, confidence=0.95)
        assert v.status == VerdictStatus.AMBIGUOUS
        assert "optional" in v.reason


# ─── Property-based tests (Hypothesis) ──────────────────────────────────────

class TestPropertyBased:
    """Property-based tests for the rule engine using Hypothesis."""

    @given(value=st.floats(min_value=50_000_000, max_value=1e15))
    @settings(max_examples=100)
    def test_gte_always_passes_above_threshold(self, value: float) -> None:
        """Any value ≥ threshold with high confidence → PASS."""
        criterion = Criterion(
            id="PROP_GTE",
            name="Turnover",
            category="financial",
            mandatory=True,
            data_type="currency_INR",
            threshold_value=50_000_000,
            threshold_operator="gte",
        )
        v = evaluate(criterion, value, confidence=0.95)
        assert v.status == VerdictStatus.PASS

    @given(value=st.floats(min_value=0, max_value=49_999_999))
    @settings(max_examples=100)
    def test_gte_always_fails_below_threshold(self, value: float) -> None:
        """Any value < threshold with high confidence → FAIL."""
        criterion = Criterion(
            id="PROP_GTE_FAIL",
            name="Turnover",
            category="financial",
            mandatory=True,
            data_type="currency_INR",
            threshold_value=50_000_000,
            threshold_operator="gte",
        )
        v = evaluate(criterion, value, confidence=0.95)
        assert v.status == VerdictStatus.FAIL

    @given(confidence=st.floats(min_value=0.0, max_value=0.69))
    @settings(max_examples=50)
    def test_low_confidence_always_ambiguous(self, confidence: float) -> None:
        """Low confidence always → AMBIGUOUS regardless of value."""
        criterion = Criterion(
            id="PROP_CONF",
            name="Turnover",
            category="financial",
            mandatory=True,
            data_type="currency_INR",
            threshold_value=50_000_000,
            threshold_operator="gte",
        )
        v = evaluate(criterion, 100_000_000, confidence=confidence)
        assert v.status == VerdictStatus.AMBIGUOUS

    def test_none_value_always_ambiguous(self) -> None:
        """None value → always AMBIGUOUS, never PASS/FAIL."""
        criterion = Criterion(
            id="PROP_NONE",
            name="Turnover",
            category="financial",
            mandatory=True,
            data_type="currency_INR",
            threshold_value=50_000_000,
            threshold_operator="gte",
        )
        v = evaluate(criterion, None, confidence=0.99)
        assert v.status == VerdictStatus.AMBIGUOUS
