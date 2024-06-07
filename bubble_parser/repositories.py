from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CursorResult,
    Delete,
    Insert,
    Select,
    Update,
    delete,
    insert,
    select,
    text,
    update,
)

from bubble_parser.app_types import Articolul, ArticolulPDF, dump_without_null
from bubble_parser.models import Articolul as ArticolulTable
from bubble_parser.models import ArticolulPDF as ArticolulPDFTable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncResult, AsyncSession


class AbstractRepository(ABC):
    """Abstract storage repository."""

    @abstractmethod
    async def get(self) -> Any:
        """Get entity from repository."""
        raise NotImplementedError

    @abstractmethod
    async def update(self) -> Any:
        """Update entity in repository."""
        raise NotImplementedError

    @abstractmethod
    async def create(self) -> Any:
        """Create entity in repository."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self) -> Any:
        """Delete entity from repository."""
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository):
    """SQLAlchemy database repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        super().__init__()

    async def _execute_stmt(
        self,
        stmt: Select | Insert | Update | Delete | str,
        stream: bool = False,
    ) -> CursorResult | AsyncResult:
        if isinstance(stmt, str):
            stmt = text(stmt)

        conn = await self._session.connection()

        if stream:
            return await conn.stream(stmt)
        return await conn.execute(stmt)

    async def get(
        self, stmt: Select, stream: bool = False
    ) -> CursorResult | AsyncResult:
        return await self._execute_stmt(stmt, stream=stream)

    async def update(self, stmt: Update) -> CursorResult:
        """Update entity in sqlalchemy repository."""
        return await self._execute_stmt(stmt)

    async def delete(self, stmt: Delete) -> CursorResult:
        """Delete entity from sqlalchemy repository."""
        return await self._execute_stmt(stmt)

    async def create(self, stmt: Insert) -> CursorResult:
        """Create entity in sqlalchemy repository."""
        return await self._execute_stmt(stmt)


class ArticolulRepository(SQLAlchemyRepository):
    _model = ArticolulTable

    async def create(self, articolul: Articolul) -> int:
        """Create articolul in repository, return articolul repository-id."""
        stmt = (
            insert(self._model)
            .values(**dump_without_null(articolul))
            .returning(self._model.articolul_id)
        )
        return await super().create(stmt)

    async def delete(self, articolul_id: int) -> None:
        """Delete articolul from repository."""
        stmt = delete(self._model).where(
            self._model.articolul_id == articolul_id
        )
        await super().delete(stmt)

    async def get_by_id(self, articolul_id: int) -> Articolul:
        """Get articolul from repository."""
        stmt = select(self._model).where(
            self._model.articolul_id == articolul_id
        )
        res = await super().get(stmt)
        return Articolul(**res.fetchone()._mapping)
    
    async def get_by_num(self, articolul_num: int) -> Articolul:
        """Get articolul by articolul num from repository."""
        stmt = select(self._model).where(
            self._model.number == articolul_num
        )
        res = await super().get(stmt)
        data = res.fetchone()
        if not data:
            return data
        return Articolul(**data._mapping)

    async def update(self, articolul: Articolul) -> Articolul:
        """Update articolul in repository."""
        stmt = (
            update(self._model)
            .values(**dump_without_null(articolul))
            .where(self._model.articolul_id == articolul.articolul_id)
        )
        await super().update(stmt)
        return articolul


class ArticolulPDFRepository(SQLAlchemyRepository):
    _model = ArticolulPDFTable

    async def create(self, pdf: ArticolulPDF) -> int:
        r"""
        Create pdf in repository, return articolul pdf
        repository-id.
        """
        stmt = (
            insert(self._model)
            .values(**dump_without_null(pdf))
            .returning(self._model.pdf_id)
        )
        return await super().create(stmt)

    async def delete(self, pdf_id: int) -> None:
        """Delete pdf from repository."""
        stmt = delete(self._model).where(self._model.pdf_id == pdf_id)
        await super().delete(stmt)

    async def get_by_id(self, pdf_id: int) -> ArticolulPDF:
        """Get pdf from repository."""
        stmt = select(self._model).where(self._model.pdf_id == pdf_id)
        res = await super().get(stmt)
        return ArticolulPDF(**res.fetchone()._mapping)

    async def update(self, pdf: ArticolulPDF) -> ArticolulPDF:
        """Update articolul in repository."""
        stmt = (
            update(self._model)
            .values(**dump_without_null(pdf))
            .where(self._model.pdf_id == pdf.pdf_id)
        )
        await super().update(stmt)
        return pdf
