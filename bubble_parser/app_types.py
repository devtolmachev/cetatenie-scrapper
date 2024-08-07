from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Any, TypeAlias

from pydantic import BaseModel

NULL: TypeAlias = None


class Articolul(BaseModel):
    """Articolul Type."""

    articolul_id: int | NULL = NULL
    number: int
    url: str | Any = NULL


class ArticolulPDF(BaseModel):
    """PDF Articolul Type."""

    pdf_id: int | NULL = NULL
    articolul_num: int
    list_name: str
    number_order: str
    date: datetime
    year: int
    url: str
    parsed_at: int


class Dosar(BaseModel):
    record_id: int | NULL = NULL
    num_dosar: str | NULL = NULL
    date: datetime | NULL = NULL
    termen: str | datetime | NULL = NULL
    numar_ordin: str | NULL = NULL
    data_ordin: str | NULL = NULL
    raw_dosar: str
    articolul_num: int
    year: int


def dump_without_null(model_type: BaseModel) -> dict:
    """Dump type values without null."""
    obj = dict(model_type)
    for field_name in model_type.model_fields:
        if getattr(model_type, field_name) == NULL:
            del obj[field_name]
    return obj
