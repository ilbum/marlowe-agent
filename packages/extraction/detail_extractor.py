import json

import anthropic

from packages.config import settings
from packages.extraction.schemas import ExtractedRecordSchema

_SYSTEM = """You are a precise data extraction agent. Given a web page and a user objective,
extract relevant structured information and classify whether the item matches the objective."""

_USER_TEMPLATE = """Objective: {objective}

Page URL: {url}

Page text:
{page_text}

Extract information from this page and return a JSON object matching this schema:
{{
  "entity_title": "<title of this item>",
  "relevant_fields": {{
    "<field_name>": "<field_value>",
    ...
  }},
  "match_status": "match" | "no_match" | "ambiguous",
  "evidence": ["<exact text snippet that supports your classification>", ...],
  "reasoning_summary": "<one sentence explaining your match decision>",
  "confidence": <0.0 to 1.0 or null>
}}

Rules:
- Use "match" only when the text clearly and explicitly satisfies the objective.
- Use "ambiguous" when there is insufficient or unclear evidence (e.g., "remote eligible" when the objective requires a specific location).
- Use "no_match" when the text clearly does not satisfy the objective.
- Always include at least one evidence snippet for "match" or "ambiguous".
- Return only valid JSON. No markdown, no extra text."""


def _trim(text: str, max_chars: int) -> str:
    return text[:max_chars] if len(text) > max_chars else text


async def extract_detail(url: str, page_text: str, objective: str) -> ExtractedRecordSchema:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    prompt = _USER_TEMPLATE.format(
        objective=objective,
        url=url,
        page_text=_trim(page_text, 6000),
    )

    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        data = json.loads(raw)
        return ExtractedRecordSchema(**data)
    except Exception:
        return ExtractedRecordSchema(
            entity_title=url,
            match_status="ambiguous",
            reasoning_summary="Extraction failed — could not parse LLM response.",
            evidence=[],
        )
