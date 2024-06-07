import json
from datetime import datetime

import pytest
from bubble_parser.database import create_sqlalchemy_async_engine, write_result
from bubble_parser.models import Base


@pytest.mark.asyncio()
async def test_write_result() -> None:
    """Test for write_result to database."""
    with open("res-large.json") as f:
        data = json.load(f)
        
    engine = create_sqlalchemy_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    for articolul_num, pdfs in data.items():
        articolul_num = int(articolul_num[-2:])
        pdfs = pdfs[:1000]
        
        start = datetime.now()
        await write_result(articolul_num=articolul_num, pdfs=pdfs)
        print(f"Articolur {articolul_num} takes a {datetime.now() - start}")
