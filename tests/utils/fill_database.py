import asyncio
import json

from bubble_parser.database import write_result


async def fill_by_res_large() -> None:
    """Fill database by res-large.json content."""
    with open("res-large.json") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert all(isinstance(value, list) for value in data.values())

    for articolul, pdfs in data.items():
        num = int(articolul[-2:])
        await write_result(num, pdfs)


async def main():
    await fill_by_res_large()


if __name__ == "__main__":
    asyncio.run(main())
