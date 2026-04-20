"""Value extractor — uses Claude tool-use to normalise bid values.

Single highest-leverage prompt-engineering file.
Handles: Indian notation (lakh/crore), Hindi/Marathi numerals,
written-out amounts, percentages, year counts, boolean certs, ISO dates.
"""

from __future__ import annotations

from src.config.settings import get_settings
from src.models.documents import BBox, DocType
from src.models.extraction import ExtractionResult

_VALUE_TOOL = {
    "name": "extract_value",
    "description": "Extract and normalise a typed value from a bid document chunk.",
    "input_schema": {
        "type": "object",
        "properties": {
            "normalised_value": {
                "description": "The normalised value (number, boolean, or date string)",
            },
            "unit": {
                "type": "string",
                "enum": ["INR", "%", "years", "bool", "date", "text"],
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Your confidence in the extraction (0.0-1.0)",
            },
            "reasoning": {
                "type": "string",
                "description": "Brief explanation of how you derived the value",
            },
        },
        "required": ["normalised_value", "unit", "confidence", "reasoning"],
    },
}

_SYSTEM_PROMPT = """You are a government procurement document analyst specialising in Indian financial documents.

Your job: extract a SINGLE normalised value from the given text chunk, for the given criterion.

CRITICAL NORMALISATION RULES:
- "Rs. 12.8 Lakh" → 1280000 (1 Lakh = 100,000)
- "Rs. Six Crores" → 60000000 (1 Crore = 10,000,000)
- "₹1,28,00,000" → 12800000 (Indian comma notation)
- "12,800,000" → 12800000 (Western comma notation)
- "5.5 Crore" → 55000000
- "Three Hundred Lakhs" → 30000000
- Hindi numerals: ١२३ → 123
- "3 years" → 3
- "true" / "valid" / "registered" → true
- Dates: normalise to YYYY-MM-DD

CONFIDENCE RULES:
- Clear typed text with unambiguous value → 0.90-0.99
- Slightly ambiguous but likely correct → 0.70-0.89
- Unclear, multiple possible interpretations → 0.50-0.69
- Contradictory or very hard to read → 0.30-0.49

If you cannot find the relevant value in the text, return normalised_value as null with confidence 0.0.

Few-shot examples:

Text: "The Annual Turnover of M/s ABC Ltd for FY 2022-23 is Rs. Six Crores as per audited financial statement"
Criterion: "Average Annual Turnover" (currency_INR, gte 50000000)
→ {normalised_value: 60000000, unit: "INR", confidence: 0.95, reasoning: "Six Crores = 6 × 10^7 = 60,000,000 INR from audited FS"}

Text: "The firm was established in 1998 and has been operational since then"
Criterion: "Years in Operation" (years, gte 10)
→ {normalised_value: 28, unit: "years", confidence: 0.85, reasoning: "Established 1998, current year 2026, 28 years"}

Text: "GSTIN: 07AAACR1234A1ZH"
Criterion: "GST Registration" (boolean, eq true)
→ {normalised_value: true, unit: "bool", confidence: 0.95, reasoning: "Valid GSTIN format found"}
"""


def extract_value_from_chunk(
    chunk_text: str,
    criterion_name: str,
    criterion_data_type: str,
    criterion_description: str = "",
    redacted_text: str | None = None,
    chunk_id: str = "",
    source_doc_type: DocType = DocType.UNKNOWN,
    page_num: int = 0,
    bbox: BBox | None = None,
    ocr_confidence: float = 0.0,
    redaction_map_id: str = "",
) -> ExtractionResult:
    """Extract a normalised value from a bid document chunk.

    Args:
        chunk_text: The raw text (local only).
        criterion_name: What we're looking for.
        criterion_data_type: Expected data type.
        redacted_text: What the LLM will see (PII removed).

    Returns:
        ExtractionResult with full provenance.
    """
    import anthropic

    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # LLM sees ONLY redacted text
    llm_input = redacted_text or chunk_text

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        tools=[_VALUE_TOOL],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Extract the value for criterion '{criterion_name}' "
                    f"(type: {criterion_data_type}) from this text:\n\n{llm_input}"
                ),
            }
        ],
    )

    # Parse tool-use response
    normalised_value = None
    unit = ""
    llm_confidence = 0.0

    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_value":
            normalised_value = block.input.get("normalised_value")
            unit = block.input.get("unit", "")
            llm_confidence = block.input.get("confidence", 0.0)
            break

    return ExtractionResult(
        raw_text=chunk_text,
        redacted_text=llm_input,
        normalised_value=normalised_value,
        unit=unit,
        confidence=llm_confidence,
        source_chunk_id=chunk_id,
        source_doc_type=source_doc_type,
        source_bbox=bbox,
        page_num=page_num,
        redaction_map_id=redaction_map_id,
        prompt_version="value_extractor@v1.0",
        ocr_confidence=ocr_confidence,
        llm_confidence=llm_confidence,
    )
