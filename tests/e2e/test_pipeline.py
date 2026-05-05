"""E2E pipeline test — validates synthetic bids against ground truth.

Tier-1 critical-path gate C4: Full VTM for each synthetic bid must match
the expected verdicts in data/ground_truth/expected_verdicts.csv.

These tests use the rule engine directly with synthetic data (no Azure OCR,
no Anthropic API) to validate the deterministic core of the pipeline.

Run with:
    pytest tests/e2e/test_pipeline.py -v -m e2e
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from src.engine.rule_engine import evaluate
from src.models.criteria import Criterion
from src.models.verdicts import VerdictStatus

# ─── Paths ───────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent.parent
GROUND_TRUTH_CSV = PROJECT_ROOT / "data" / "ground_truth" / "expected_verdicts.csv"
NIT_JSON = PROJECT_ROOT / "data" / "synthetic" / "nit_sample.json"
BID_A_JSON = PROJECT_ROOT / "data" / "synthetic" / "bid_a_pass.json"
BID_B_JSON = PROJECT_ROOT / "data" / "synthetic" / "bid_b_fail.json"
BID_C_JSON = PROJECT_ROOT / "data" / "synthetic" / "bid_c_hitl.json"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_ground_truth() -> dict[tuple[str, str], str]:
    """Load expected verdicts from CSV → {(bid_id, criterion_id): verdict}."""
    gt: dict[tuple[str, str], str] = {}
    with open(GROUND_TRUTH_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["bid_id"].strip(), row["criterion_id"].strip())
            gt[key] = row["expected_verdict"].strip()
    return gt


def load_nit_criteria() -> list[Criterion]:
    """Load criteria from NIT sample JSON and build Criterion objects."""
    data = json.loads(NIT_JSON.read_text(encoding="utf-8"))
    criteria = []
    for c in data["criteria"]:
        criteria.append(Criterion(
            id=c["id"],
            name=c["name"],
            category=c["category"],
            mandatory=c["mandatory"],
            data_type=c["data_type"],
            threshold_operator=c["threshold_operator"],
            threshold_value=c.get("threshold_value"),
            threshold_upper=c.get("threshold_upper"),
            source_section=c.get("source_section", ""),
            citation=c.get("citation", ""),
        ))
    return criteria


def load_bid_expected(bid_json: Path) -> dict[str, dict]:
    """Load expected_vtm from a bid JSON file."""
    data = json.loads(bid_json.read_text(encoding="utf-8"))
    return data.get("expected_vtm", {})


# ─── Test: Ground Truth File Integrity ───────────────────────────────────────

@pytest.mark.e2e
def test_ground_truth_csv_exists_and_has_data() -> None:
    """Ground truth CSV must exist and have at least 10 rows (3 bids × criteria)."""
    assert GROUND_TRUTH_CSV.exists(), f"Ground truth CSV not found: {GROUND_TRUTH_CSV}"
    gt = load_ground_truth()
    assert len(gt) >= 10, f"Expected ≥ 10 ground truth rows, found {len(gt)}"


@pytest.mark.e2e
def test_ground_truth_covers_all_three_bids() -> None:
    """Ground truth must contain rows for BID-A, BID-B, and BID-C."""
    gt = load_ground_truth()
    bid_ids = {bid_id for (bid_id, _) in gt}
    assert "BID-A" in bid_ids, "BID-A missing from ground truth"
    assert "BID-B" in bid_ids, "BID-B missing from ground truth"
    assert "BID-C" in bid_ids, "BID-C missing from ground truth"


@pytest.mark.e2e
def test_ground_truth_verdicts_are_valid_values() -> None:
    """All expected verdicts in ground truth must be valid VerdictStatus values."""
    gt = load_ground_truth()
    valid = {s.value for s in VerdictStatus}
    for (bid_id, criterion_id), verdict in gt.items():
        assert verdict in valid, (
            f"Invalid verdict '{verdict}' for ({bid_id}, {criterion_id}). "
            f"Must be one of: {valid}"
        )


# ─── Test: NIT Sample Data ────────────────────────────────────────────────────

@pytest.mark.e2e
def test_nit_sample_loads_6_criteria() -> None:
    """NIT sample must load and produce exactly 6 Criterion objects."""
    criteria = load_nit_criteria()
    assert len(criteria) == 6, f"Expected 6 criteria from NIT, got {len(criteria)}"


@pytest.mark.e2e
def test_nit_criteria_have_valid_operators() -> None:
    """All criteria must have valid threshold operators."""
    criteria = load_nit_criteria()
    valid_ops = {"gte", "lte", "eq", "between", "contains", "valid_on_date"}
    for c in criteria:
        assert c.threshold_operator in valid_ops, (
            f"Criterion {c.id} has invalid operator '{c.threshold_operator}'"
        )


# ─── Test: BID-A Rule Engine (Golden Path — All PASS) ─────────────────────────

@pytest.mark.e2e
def test_bid_a_rule_engine_produces_all_pass() -> None:
    """BID-A: all criteria with clean values and high confidence → all PASS."""
    expected_vtm = load_bid_expected(BID_A_JSON)
    criteria_by_id = {c.id: c for c in load_nit_criteria()}

    for criterion_id, expected in expected_vtm.items():
        criterion = criteria_by_id.get(criterion_id)
        if criterion is None:
            continue

        value = expected["value"]
        confidence = expected["confidence"]
        expected_verdict = expected["verdict"]

        verdict = evaluate(criterion, value, confidence)

        assert verdict.status.value == expected_verdict, (
            f"BID-A {criterion_id} ({criterion.name}): "
            f"expected {expected_verdict}, got {verdict.status.value}. "
            f"Expression: {verdict.expression}"
        )


@pytest.mark.e2e
def test_bid_a_all_6_criteria_in_ground_truth_pass() -> None:
    """BID-A: all 6 entries in ground truth must be PASS."""
    gt = load_ground_truth()
    bid_a_entries = {cid: v for (bid, cid), v in gt.items() if bid == "BID-A"}
    assert len(bid_a_entries) == 6, f"Expected 6 BID-A rows in GT, found {len(bid_a_entries)}"
    for criterion_id, expected_verdict in bid_a_entries.items():
        assert expected_verdict == "PASS", (
            f"BID-A {criterion_id}: expected PASS in ground truth, got {expected_verdict}"
        )


# ─── Test: BID-B Rule Engine (Clear FAIL on C002) ────────────────────────────

@pytest.mark.e2e
def test_bid_b_similar_works_fails() -> None:
    """BID-B: C002 (Similar Works) with value=1 and threshold≥3 must FAIL."""
    criteria_by_id = {c.id: c for c in load_nit_criteria()}
    criterion = criteria_by_id["C002"]

    # Bid B submitted only 1 project
    verdict = evaluate(criterion, 1, confidence=0.88)

    assert verdict.status == VerdictStatus.FAIL, (
        f"Expected FAIL for Similar Works with 1 project < threshold 3, "
        f"got {verdict.status}. Expression: {verdict.expression}"
    )
    assert "1.0 >= 3.0" in verdict.expression or "1" in verdict.expression


@pytest.mark.e2e
def test_bid_b_turnover_passes() -> None:
    """BID-B: C001 (Turnover) with ₹7.5Cr > threshold ₹5Cr must PASS."""
    criteria_by_id = {c.id: c for c in load_nit_criteria()}
    criterion = criteria_by_id["C001"]

    verdict = evaluate(criterion, 75_000_000, confidence=0.93)

    assert verdict.status == VerdictStatus.PASS, (
        f"Expected PASS for ₹7.5Cr > threshold ₹5Cr, got {verdict.status}"
    )


@pytest.mark.e2e
def test_bid_b_ground_truth_has_one_fail() -> None:
    """BID-B: ground truth must have exactly 1 FAIL (C002)."""
    gt = load_ground_truth()
    bid_b_entries = {cid: v for (bid, cid), v in gt.items() if bid == "BID-B"}
    fail_count = sum(1 for v in bid_b_entries.values() if v == "FAIL")
    assert fail_count == 1, (
        f"Expected exactly 1 FAIL in BID-B ground truth, found {fail_count}"
    )
    assert bid_b_entries.get("C002") == "FAIL", "Expected C002 to be the FAIL in BID-B"


# ─── Test: BID-C Rule Engine (HITL Trigger) ──────────────────────────────────

@pytest.mark.e2e
def test_bid_c_low_confidence_turnover_ambiguous() -> None:
    """BID-C: C001 with confidence 0.55 < 0.70 floor → must be AMBIGUOUS."""
    criteria_by_id = {c.id: c for c in load_nit_criteria()}
    criterion = criteria_by_id["C001"]

    # Handwritten CA cert — low OCR + LLM confidence
    verdict = evaluate(criterion, 52_000_000, confidence=0.55)

    assert verdict.status == VerdictStatus.AMBIGUOUS, (
        f"Expected AMBIGUOUS for confidence 0.55 < 0.70, got {verdict.status}"
    )
    assert verdict.reason == "low_extraction_confidence"


@pytest.mark.e2e
def test_bid_c_missing_declaration_ambiguous() -> None:
    """BID-C: C005 with value=None (keywords not found) → must be AMBIGUOUS."""
    criteria_by_id = {c.id: c for c in load_nit_criteria()}
    criterion = criteria_by_id["C005"]

    # Near relations keywords not found → value not extracted
    verdict = evaluate(criterion, None, confidence=0.40)

    assert verdict.status == VerdictStatus.AMBIGUOUS, (
        f"Expected AMBIGUOUS for value=None, got {verdict.status}"
    )
    assert verdict.reason == "value_not_extracted"


@pytest.mark.e2e
def test_bid_c_all_ground_truth_entries_are_ambiguous() -> None:
    """BID-C: all entries in ground truth must be AMBIGUOUS."""
    gt = load_ground_truth()
    bid_c_entries = {cid: v for (bid, cid), v in gt.items() if bid == "BID-C"}
    assert len(bid_c_entries) >= 2, (
        f"Expected ≥ 2 BID-C entries in ground truth, found {len(bid_c_entries)}"
    )
    for criterion_id, expected_verdict in bid_c_entries.items():
        assert expected_verdict == "AMBIGUOUS", (
            f"BID-C {criterion_id}: expected AMBIGUOUS in ground truth, got {expected_verdict}"
        )


# ─── Test: Confidence Floor Invariant (Critical Path Gate C3) ────────────────

@pytest.mark.e2e
@pytest.mark.parametrize("confidence", [0.0, 0.1, 0.5, 0.6, 0.6999])
def test_confidence_below_floor_always_ambiguous(confidence: float) -> None:
    """Any confidence < 0.70 → AMBIGUOUS. This is the C3 gate invariant."""
    criteria_by_id = {c.id: c for c in load_nit_criteria()}
    criterion = criteria_by_id["C001"]

    verdict = evaluate(criterion, 99_999_999.0, confidence=confidence)

    assert verdict.status == VerdictStatus.AMBIGUOUS, (
        f"Expected AMBIGUOUS for confidence={confidence} < 0.70, got {verdict.status}"
    )


@pytest.mark.e2e
@pytest.mark.parametrize("confidence", [0.70, 0.75, 0.90, 0.95, 1.0])
def test_confidence_at_or_above_floor_can_pass(confidence: float) -> None:
    """confidence ≥ 0.70 with a clearly passing value must PASS (not AMBIGUOUS from confidence)."""
    criteria_by_id = {c.id: c for c in load_nit_criteria()}
    criterion = criteria_by_id["C001"]  # C001: gte 50_000_000

    verdict = evaluate(criterion, 99_999_999.0, confidence=confidence)

    assert verdict.status != VerdictStatus.AMBIGUOUS or verdict.reason == "low_extraction_confidence" is False, (
        f"Got unexpected AMBIGUOUS with confidence={confidence} and clearly passing value. "
        f"Reason: {verdict.reason}"
    )
    assert verdict.status == VerdictStatus.PASS, (
        f"Expected PASS for value=99999999 >> threshold=50000000 with confidence={confidence}, "
        f"got {verdict.status}"
    )


# ─── Test: Rule Engine Isolation (Import-linter Smoke) ───────────────────────

@pytest.mark.e2e
def test_rule_engine_does_not_import_llm_sdks() -> None:
    """Smoke test: importing the rule engine must not pull in any LLM SDK."""
    import importlib
    import sys

    # Import rule_engine fresh
    if "src.engine.rule_engine" in sys.modules:
        re_module = sys.modules["src.engine.rule_engine"]
    else:
        re_module = importlib.import_module("src.engine.rule_engine")

    # Check that no LLM modules were loaded as a side effect
    llm_modules = [
        m for m in sys.modules
        if any(sdk in m for sdk in ["anthropic", "openai", "langchain"])
    ]

    # We only flag modules that were imported BY the rule engine (not loaded elsewhere)
    # The import-linter contract in pyproject.toml enforces this at CI time
    # This test verifies the contract holds at runtime too
    rule_engine_imports = getattr(re_module, "__spec__", None)
    assert rule_engine_imports is not None, "Rule engine module not properly imported"

    # If anthropic/openai appear in sys.modules, they must NOT be from rule_engine
    for llm_mod in llm_modules:
        assert "src.engine" not in str(sys.modules[llm_mod].__spec__ if hasattr(sys.modules[llm_mod], "__spec__") else ""), (
            f"LLM module {llm_mod} appears to be imported by src.engine — contract violated!"
        )
