"""EMD (Earnest Money Deposit) validator.

Checks: BG validity ≥ 45 days post-opening, amount ≥ 2% of NIT value.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from src.config.settings import get_settings
from src.models.verdicts import Verdict, VerdictStatus


def validate_emd(
    bg_amount: float | None,
    nit_value: float | None,
    bg_validity_date: str | None,
    tender_opening_date: str | None,
    bg_number: str = "",
) -> Verdict:
    """Validate EMD / Bank Guarantee.

    Rules:
    - Amount ≥ 2% of NIT estimated value
    - Validity ≥ 45 days after tender opening date

    Args:
        bg_amount: Bank guarantee amount in INR.
        nit_value: NIT estimated tender value in INR.
        bg_validity_date: BG expiry date (YYYY-MM-DD).
        tender_opening_date: Tender opening date (YYYY-MM-DD).

    Returns:
        Verdict (PASS / FAIL / AMBIGUOUS).
    """
    settings = get_settings()

    if bg_amount is None:
        return Verdict(
            status=VerdictStatus.AMBIGUOUS,
            reason="emd_amount_not_found",
            expression="BG amount not extracted",
        )

    if nit_value is None:
        return Verdict(
            status=VerdictStatus.AMBIGUOUS,
            reason="nit_value_not_found",
            expression="NIT estimated value not available",
        )

    # Check amount
    min_amount = nit_value * (settings.emd_min_percentage / 100.0)
    if bg_amount < min_amount:
        return Verdict(
            status=VerdictStatus.FAIL,
            reason="emd_amount_insufficient",
            expression=f"BG ₹{bg_amount:,.0f} < required ₹{min_amount:,.0f} ({settings.emd_min_percentage}% of ₹{nit_value:,.0f})",
        )

    # Check validity date
    if bg_validity_date and tender_opening_date:
        try:
            validity = datetime.strptime(bg_validity_date, "%Y-%m-%d").date()
            opening = datetime.strptime(tender_opening_date, "%Y-%m-%d").date()
            min_validity = opening + timedelta(days=settings.emd_min_validity_days)

            if validity < min_validity:
                return Verdict(
                    status=VerdictStatus.FAIL,
                    reason="emd_validity_insufficient",
                    expression=(
                        f"BG valid until {validity.isoformat()} < "
                        f"required {min_validity.isoformat()} "
                        f"({settings.emd_min_validity_days} days after opening {opening.isoformat()})"
                    ),
                )
        except ValueError:
            return Verdict(
                status=VerdictStatus.AMBIGUOUS,
                reason="emd_date_parse_error",
                expression=f"Cannot parse dates: validity={bg_validity_date}, opening={tender_opening_date}",
            )
    elif not bg_validity_date:
        return Verdict(
            status=VerdictStatus.AMBIGUOUS,
            reason="emd_validity_not_found",
            expression="BG validity date not extracted",
        )

    return Verdict(
        status=VerdictStatus.PASS,
        reason="emd_valid",
        expression=f"BG ₹{bg_amount:,.0f} ≥ ₹{min_amount:,.0f} and validity OK",
    )
