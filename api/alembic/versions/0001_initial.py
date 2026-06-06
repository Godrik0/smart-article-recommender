"""create articles and recommendation_requests

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-17
"""

from __future__ import annotations

import json
from pathlib import Path

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("tags", sa.Text(), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_articles_category", "articles", ["category"])

    op.create_table(
        "recommendation_requests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_recommendation_requests_status", "recommendation_requests", ["status"])
    op.create_index("ix_recommendation_requests_created_at", "recommendation_requests", ["created_at"])

    seed_path = Path(__file__).resolve().parent.parent.parent / "seed_data.json"
    if seed_path.exists():
        with open(seed_path) as f:
            raw_articles = json.load(f)

        articles_table = sa.table(
            "articles",
            sa.column("title", sa.String),
            sa.column("description", sa.Text),
            sa.column("category", sa.String),
            sa.column("tags", sa.Text),
            sa.column("url", sa.String),
        )
        rows = [
            {
                "title": a["title"],
                "description": a["description"],
                "category": a["category"],
                "tags": json.dumps(a["tags"]),
                "url": a["url"],
            }
            for a in raw_articles
        ]
        op.bulk_insert(articles_table, rows)


def downgrade() -> None:
    op.drop_index("ix_recommendation_requests_created_at", table_name="recommendation_requests")
    op.drop_index("ix_recommendation_requests_status", table_name="recommendation_requests")
    op.drop_table("recommendation_requests")
    op.drop_index("ix_articles_category", table_name="articles")
    op.drop_table("articles")
