from typing import Literal

from pydantic import BaseModel, Field


class ExtractedRecordSchema(BaseModel):
    entity_title: str = ""
    relevant_fields: dict = Field(default_factory=dict)
    match_status: Literal["match", "no_match", "ambiguous"] = "ambiguous"
    evidence: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    confidence: float | None = None
