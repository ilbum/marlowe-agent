import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    seed_url: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class InvestigationPlan(Base):
    __tablename__ = "investigation_plans"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    investigation_id: Mapped[str] = mapped_column(String, ForeignKey("investigations.id"), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    traversal_strategy: Mapped[str | None] = mapped_column(String(64), nullable=True)
    output_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    user_condition: Mapped[str] = mapped_column(Text, nullable=False, default="")
    planner_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")


class PageSnapshot(Base):
    __tablename__ = "page_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    investigation_id: Mapped[str] = mapped_column(String, ForeignKey("investigations.id"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    page_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    dom_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DiscoveredItem(Base):
    __tablename__ = "discovered_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    investigation_id: Mapped[str] = mapped_column(String, ForeignKey("investigations.id"), nullable=False)
    source_page_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_page_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    stable_key: Mapped[str] = mapped_column(String(64), nullable=False)
    title_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="discovered")


class ExtractedRecord(Base):
    __tablename__ = "extracted_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    item_id: Mapped[str] = mapped_column(String, ForeignKey("discovered_items.id"), nullable=False)
    fields: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    match_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)


class TraversalLedger(Base):
    __tablename__ = "traversal_ledgers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    investigation_id: Mapped[str] = mapped_column(String, ForeignKey("investigations.id"), nullable=False)
    traversal_type: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    pages_visited: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scroll_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_items_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stop_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    completion_status: Mapped[str] = mapped_column(String(32), nullable=False, default="uncertain")
