"""Criterion extractor — uses Claude tool-use to parse NIT criteria.

Runs ONCE per NIT. Extracts structured Criterion objects from the NIT text.
Few-shot examples from 3 NIT types (vehicles, IT, uniforms).
"""

from __future__ import annotations

from src.config.settings import get_settings
from src.models.criteria import Criterion

# The structured tool definition for Claude
_CRITERION_TOOL = {
    "name": "extract_criteria",
    "description": "Extract eligibility criteria from a tender (NIT) document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "criteria": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Unique ID e.g. C001"},
                        "name": {"type": "string", "description": "Human-readable criterion name"},
                        "category": {
                            "type": "string",
                            "enum": ["financial", "technical", "compliance", "document", "declaration"],
                        },
                        "mandatory": {"type": "boolean"},
                        "data_type": {
                            "type": "string",
                            "enum": ["currency_INR", "percentage", "years", "boolean", "text", "date"],
                        },
                        "threshold_value": {
                            "description": "Number, boolean, or string threshold",
                        },
                        "threshold_operator": {
                            "type": "string",
                            "enum": ["gte", "lte", "eq", "between", "contains", "valid_on_date"],
                        },
                        "threshold_upper": {
                            "type": "number",
                            "description": "Upper bound for 'between' operator",
                        },
                        "source_section": {"type": "string"},
                        "citation": {"type": "string"},
                    },
                    "required": ["id", "name", "category", "mandatory", "data_type", "threshold_operator"],
                },
            },
        },
        "required": ["criteria"],
    },
}

_SYSTEM_PROMPT = """You are a government procurement expert. Extract ALL eligibility criteria from the tender (NIT) document.

For each criterion, identify:
- A unique ID (C001, C002, etc.)
- The exact criterion name
- Category: financial, technical, compliance, document, or declaration
- Whether it is mandatory or optional
- Data type: currency_INR, percentage, years, boolean, text, or date
- Threshold value and operator (gte = greater than or equal, lte = less than or equal, etc.)
- Source section reference
- Legal citation if applicable (e.g., GFR 2017 Rule 162)

CRITICAL: Mark mandatory vs optional correctly. Most teams miss this and silently disqualify bidders who only missed an optional criterion.

Few-shot examples:

1. "Annual Average Turnover of at least Rs. 5 Crore in last 3 financial years" →
   {id: "C001", name: "Average Annual Turnover", category: "financial", mandatory: true,
    data_type: "currency_INR", threshold_value: 50000000, threshold_operator: "gte",
    source_section: "Section 3.2(a)"}

2. "Valid GST Registration" →
   {id: "C002", name: "GST Registration", category: "compliance", mandatory: true,
    data_type: "boolean", threshold_value: true, threshold_operator: "eq"}

3. "ISO 9001:2015 certification (preferred but not mandatory)" →
   {id: "C003", name: "ISO 9001 Certification", category: "document", mandatory: false,
    data_type: "boolean", threshold_value: true, threshold_operator: "contains"}
"""


def extract_criteria_from_text(nit_text: str) -> list[Criterion]:
    """Extract eligibility criteria from NIT text using Claude.

    Args:
        nit_text: The redacted NIT text (PII already removed).

    Returns:
        List of Criterion objects.
    """
    import anthropic

    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        tools=[_CRITERION_TOOL],
        messages=[
            {
                "role": "user",
                "content": f"Extract all eligibility criteria from the following tender document:\n\n{nit_text}",
            }
        ],
    )

    # Parse tool-use response
    criteria: list[Criterion] = []
    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_criteria":
            raw_criteria = block.input.get("criteria", [])
            for raw in raw_criteria:
                try:
                    criteria.append(Criterion(**raw))
                except Exception:
                    continue  # Skip malformed criteria

    return criteria
