"""Criterion model — extracted from a NIT by the criterion extractor."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.models.documents import BBox


class Criterion(BaseModel):
    """A single eligibility criterion extracted from a NIT.

    This is the contract between the criterion extractor and the rule engine.
    """

    id: str = Field(description="Unique ID, e.g. 'C001'")
    name: str = Field(description="Human-readable name, e.g. 'Average Annual Turnover'")
    category: Literal["financial", "technical", "compliance", "document", "declaration"]
    mandatory: bool = True
    data_type: Literal["currency_INR", "percentage", "years", "boolean", "text", "date"]
    threshold_value: float | bool | str | None = None
    threshold_operator: Literal["gte", "lte", "eq", "between", "contains", "valid_on_date"]
    threshold_upper: float | None = None
    source_section: str = Field(
        default="", description="e.g. 'Section 3.2, page 14'"
    )
    source_bbox: BBox | None = None
    citation: str = Field(default="", description="e.g. 'GFR 2017 Rule 162'")
