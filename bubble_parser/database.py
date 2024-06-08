from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from bubble_parser import get_config
from bubble_parser.models import Base
from bubble_parser.repositories import (
    ArticolulPDFRepository,
    ArticolulRepository,
)
from bubble_parser.app_types import Articolul, ArticolulPDF


async def setup_db() -> None:
    """Create all tables in database."""
    async with create_sqlalchemy_async_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def create_sqlalchemy_async_engine() -> AsyncEngine:
    """Return sqlalchemy async engine from config."""
    cfg = get_config()["postgres"]
    url = (
        f"postgresql+asyncpg://{cfg["user"]}:{cfg["password"]}@"
        f"{cfg["host"]}:{cfg["port"]}/{cfg["dbname"]}"
    )
    return create_async_engine(url).execution_options(
        isolation_level="AUTOCOMMIT"
    )


async def write_result(articolul_num: int, pdfs: list[dict]) -> None:
    """Write result to database."""
    articolul_num = int(articolul_num)
    session = async_sessionmaker(
        create_sqlalchemy_async_engine(), expire_on_commit=False
    )
    async with session() as db:
        repository = ArticolulRepository(db)
        articolul = await repository.get_by_num(articolul_num=articolul_num)
        if not articolul:
            articolul = Articolul(number=articolul_num)
            await repository.create(articolul=articolul)

    async with session() as db:
        repository = ArticolulPDFRepository(db)
        tasks = []
        for pdf in pdfs:
            articolur_pdf = ArticolulPDF(
                list_name=pdf["list_name"],
                articolul_num=articolul_num,
                number_order=pdf["number_order"],
                date=datetime.strptime(pdf["date"], "%d.%m.%Y"),
                url=pdf["pdf_link"],
                parsed_at=int(pdf["timestamp"]),
            )
            tasks.append(
                repository.create(articolur_pdf)
            )
        start = datetime.now()
        await asyncio.gather(*tasks)
        print(datetime.now() - start, len(tasks))
