import json

import anthropic

from packages.config import settings
from packages.understanding.page_model_schema import PageModel

_SYSTEM = """You are a browser page analyst. Given a URL, HTML excerpt, visible text, and a user objective,
analyze the page and return a structured JSON response describing the page structure."""

_USER_TEMPLATE = """URL: {url}

Objective: {objective}

HTML excerpt (first 8000 chars):
{html_excerpt}

Visible text excerpt (first 3000 chars):
{text_excerpt}

Analyze this page and return a JSON object matching this schema:
{{
  "page_type": "list" | "detail" | "unknown",
  "result_item_selector_candidates": ["CSS or text description of result card elements"],
  "detail_link_selector_candidates": ["CSS selectors or descriptions for links to detail pages"],
  "traversal_type_guess": "pagination" | "load_more" | "infinite_scroll" | "url_param_pagination" | null,
  "next_control_candidates": ["CSS selectors or text descriptions of next page controls"],
  "total_results_hint": <integer or null>,
  "entity_type": "<what kind of items are on this page, e.g. jobs, apartments, products, or null>",
  "planner_notes": "<brief notes about anything unusual or relevant>"
}}

Return only valid JSON. No markdown, no extra text."""


def _trim(text: str, max_chars: int) -> str:
    return text[:max_chars] if len(text) > max_chars else text


async def classify_page(url: str, html: str, objective: str) -> PageModel:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    prompt = _USER_TEMPLATE.format(
        url=url,
        objective=objective,
        html_excerpt=_trim(html, 8000),
        text_excerpt=_trim(_extract_text_from_html(html), 3000),
    )

    message = await client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    return PageModel(**data)


def _extract_text_from_html(html: str) -> str:
    import re
    # strip tags, collapse whitespace
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
