"""Blacklist checker — CVC debarment list fuzzy matching.

Compares bidder name + GSTIN + PAN against a snapshot of the CVC debarment list.
Fuzzy Jaro-Winkler ≥ 0.92 → flag for HITL, never auto-fail (false-positive risk).
"""

from __future__ import annotations

import csv
from pathlib import Path

import jellyfish

from src.config.settings import get_settings
from src.models.verdicts import Verdict, VerdictStatus


def _load_blacklist(path: str | None = None) -> list[dict]:
    """Load CVC debarment list from CSV."""
    if path is None:
        path = "data/blacklist/cvc_debarment.csv"
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    with open(p, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def check_blacklist(
    bidder_name: str,
    bidder_gstin: str = "",
    bidder_pan: str = "",
    blacklist_path: str | None = None,
) -> Verdict:
    """Check a bidder against the CVC debarment list.

    Uses Jaro-Winkler for fuzzy name matching.
    GSTIN/PAN are exact-matched.
    Match → HITL (never auto-FAIL due to false-positive risk on common names).
    """
    settings = get_settings()
    threshold = settings.blacklist_jaro_winkler_threshold
    blacklist = _load_blacklist(blacklist_path)

    if not blacklist:
        return Verdict(
            status=VerdictStatus.PASS,
            reason="blacklist_empty_or_not_found",
            expression="no blacklist entries to check",
        )

    for entry in blacklist:
        entry_name = entry.get("company_name", "")
        entry_gstin = entry.get("gstin", "")
        entry_pan = entry.get("pan", "")

        # Exact match on GSTIN or PAN
        if bidder_gstin and entry_gstin and bidder_gstin.upper() == entry_gstin.upper():
            return Verdict(
                status=VerdictStatus.AMBIGUOUS,
                reason="blacklist_gstin_exact_match",
                expression=f"GSTIN {bidder_gstin} matches debarred entity",
            )

        if bidder_pan and entry_pan and bidder_pan.upper() == entry_pan.upper():
            return Verdict(
                status=VerdictStatus.AMBIGUOUS,
                reason="blacklist_pan_exact_match",
                expression=f"PAN {bidder_pan} matches debarred entity",
            )

        # Fuzzy name match
        if bidder_name and entry_name:
            similarity = jellyfish.jaro_winkler_similarity(
                bidder_name.lower(), entry_name.lower()
            )
            if similarity >= threshold:
                return Verdict(
                    status=VerdictStatus.AMBIGUOUS,
                    reason="blacklist_fuzzy_name_match",
                    expression=(
                        f"'{bidder_name}' matches '{entry_name}' "
                        f"(Jaro-Winkler={similarity:.4f} ≥ {threshold})"
                    ),
                )

    return Verdict(
        status=VerdictStatus.PASS,
        reason="no_blacklist_match",
        expression="bidder not found in CVC debarment list",
    )
