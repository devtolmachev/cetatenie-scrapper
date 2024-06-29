from __future__ import annotations

import asyncio
import os
from datetime import datetime
import pickle

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)

from bubble_parser import get_config
from bubble_parser.app_types import Articolul, ArticolulPDF, Dosar
from bubble_parser.models import Base
from bubble_parser.repositories import (
    ArticolulPDFRepository,
    ArticolulRepository,
    DosarRepository,
)


async def setup_db() -> None:
    """Create all tables in database."""
    async with create_sqlalchemy_async_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def create_sqlalchemy_async_engine() -> AsyncEngine:
    """Return sqlalchemy async engine from config."""
    cfg = get_config()["postgres"]
    host = os.getenv("POSTGRES_HOST")

    if host:
        cfg["host"] = host

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
    scoped_sessionmaker = async_scoped_session(session, asyncio.current_task)
    async with scoped_sessionmaker() as db:
        repository = ArticolulRepository(db)
        articolul = await repository.get_by_num(articolul_num=articolul_num)
        if not articolul:
            articolul = Articolul(number=articolul_num)
            await repository.create(articolul=articolul)

    async def write(pdf: ArticolulPDF):
        async with scoped_sessionmaker() as db:
            repository = ArticolulPDFRepository(db)
            await repository.create(pdf)

    tasks = []
    for pdf in pdfs:
        pdf_date = datetime.strptime(pdf["date"], "%d.%m.%Y")
        articolur_pdf = ArticolulPDF(
            articolul_num=articolul_num,
            list_name=pdf["list_name"],
            number_order=pdf["number_order"],
            date=pdf_date,
            year=pdf_date.year,
            url=pdf["pdf_link"],
            parsed_at=int(pdf["timestamp"]),
        )
        tasks.append(write(articolur_pdf))

    await asyncio.gather(*tasks)


async def write_dosars(dosars: list[Dosar]):
    """Func for write list of dosars to repository db.

    Parameters
    ----------
    dosars : list[Dosar]
        dosars list.
    """
    session = async_sessionmaker(
        create_sqlalchemy_async_engine(), expire_on_commit=False
    )
    scoped_sessionmaker = async_scoped_session(session, asyncio.current_task)
    tasks = []

    async def write(dosar: Dosar):
        async with scoped_sessionmaker() as db:
            repository = DosarRepository(db)
            await repository.create(dosar)

    for dosar in dosars:
        tasks.append(write(dosar))

    await asyncio.gather(*tasks)


def divide_list(lst, n):
    """
    Divide a list into n equal parts.

    Parameters:
    lst (list): The list to be divided.
    n (int): The number of parts to divide the list into.

    Returns:
    list of lists: A list containing n sublists.
    """
    # Calculate the size of each chunk
    chunk_size = len(lst) // n
    remainder = len(lst) % n

    # Create the chunks
    chunks = []
    start = 0
    for i in range(n):
        end = start + chunk_size + (1 if i < remainder else 0)
        chunks.append(lst[start:end])
        start = end

    return chunks


async def write_dosars_by_parts(dosars: list[Dosar]):
    """Divide list dosars by equals parts and write them into database

    Parameters
    ----------
    dosars : list[Dosar]
        list of dosars
    """
    parts = divide_list(dosars, 1000)

    group_by = 4
    for _ in range(int(len(parts) / group_by)):
        tasks = [write_dosars(p) for p in parts[:group_by]]
        await asyncio.gather(*tasks)
        del parts[:group_by]
