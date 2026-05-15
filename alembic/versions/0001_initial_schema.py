"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("seed_url", sa.Text(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "investigation_plans",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("investigation_id", sa.String(), sa.ForeignKey("investigations.id"), nullable=False),
        sa.Column("entity_type", sa.String(128), nullable=True),
        sa.Column("traversal_strategy", sa.String(64), nullable=True),
        sa.Column("output_schema", JSONB(), nullable=False, server_default="{}"),
        sa.Column("user_condition", sa.Text(), nullable=False, server_default=""),
        sa.Column("planner_notes", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "page_snapshots",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("investigation_id", sa.String(), sa.ForeignKey("investigations.id"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("page_type", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("dom_excerpt", sa.Text(), nullable=True),
        sa.Column("screenshot_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "discovered_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("investigation_id", sa.String(), sa.ForeignKey("investigations.id"), nullable=False),
        sa.Column("source_page_url", sa.Text(), nullable=False),
        sa.Column("source_page_index", sa.Integer(), nullable=True),
        sa.Column("item_url", sa.Text(), nullable=True),
        sa.Column("stable_key", sa.String(64), nullable=False),
        sa.Column("title_hint", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="discovered"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_discovered_items_investigation_id", "discovered_items", ["investigation_id"])
    op.create_index("ix_discovered_items_stable_key", "discovered_items", ["investigation_id", "stable_key"])
    op.create_table(
        "extracted_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), sa.ForeignKey("discovered_items.id"), nullable=False),
        sa.Column("fields", JSONB(), nullable=False, server_default="{}"),
        sa.Column("match_status", sa.String(32), nullable=False),
        sa.Column("reasoning_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence", JSONB(), nullable=False, server_default="[]"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "traversal_ledgers",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("investigation_id", sa.String(), sa.ForeignKey("investigations.id"), nullable=False),
        sa.Column("traversal_type", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("pages_visited", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scroll_rounds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_items_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stop_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("completion_status", sa.String(32), nullable=False, server_default="uncertain"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("traversal_ledgers")
    op.drop_table("extracted_records")
    op.drop_index("ix_discovered_items_stable_key")
    op.drop_index("ix_discovered_items_investigation_id")
    op.drop_table("discovered_items")
    op.drop_table("page_snapshots")
    op.drop_table("investigation_plans")
    op.drop_table("investigations")
