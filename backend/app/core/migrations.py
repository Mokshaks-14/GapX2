"""Lightweight, non-destructive schema upgrades.

`Base.metadata.create_all` creates missing tables but never adds columns to tables
that already exist. This adds any missing columns so older databases keep working
after the models gain new fields. It never drops tables, columns or rows.
"""
import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.core.database import Base

logger = logging.getLogger(__name__)


def _column_default_sql(column) -> str:
    default = column.default
    if default is None or not getattr(default, "is_scalar", False):
        return ""
    value = default.arg
    if isinstance(value, bool):
        return f" DEFAULT {1 if value else 0}"
    if isinstance(value, (int, float)):
        return f" DEFAULT {value}"
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f" DEFAULT '{escaped}'"
    return ""


def upgrade_schema(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                col_type = column.type.compile(dialect=engine.dialect)
                sql = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}{_column_default_sql(column)}'
                logger.info("Schema upgrade: %s", sql)
                conn.execute(text(sql))
