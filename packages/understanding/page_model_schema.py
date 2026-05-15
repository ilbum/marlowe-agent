from typing import Literal

from pydantic import BaseModel, Field


class PageModel(BaseModel):
    page_type: Literal["list", "detail", "unknown"] = "unknown"
    result_item_selector_candidates: list[str] = Field(default_factory=list)
    detail_link_selector_candidates: list[str] = Field(default_factory=list)
    traversal_type_guess: str | None = None
    next_control_candidates: list[str] = Field(default_factory=list)
    total_results_hint: int | None = None
    entity_type: str | None = None
    planner_notes: str = ""
