"""Contain a REST API."""

import json
import time
from datetime import UTC, datetime, timedelta
from typing import Optional

import aiohttp
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from loguru import logger

from bubble_parser.database import (
    setup_db,
    write_dosars_by_parts,
    write_result,
)
from bubble_parser.parser import ParserCetatenie, ParserDosars, aiohttp_session

app = FastAPI()


@app.post("/is_work")
async def is_work() -> dict:
    """Check if server is working."""
    return {"ok": True, "message": "yes, server working"}


@app.post("/get_updates")
async def get_updates(data: str) -> dict:
    """Get updates."""
    request = json.loads(data)
    logger.info(f"/get_updates trigerred with data - {data}")
    return await get_result(request=request)


@app.post("/get_dosars")
async def get_dosars(data: Optional[str] = None, url: Optional[str] = None):
    """Get dosars."""
    if not data:
        articoluls = None
    else:
        request = json.loads(data)
        articoluls = request["articoluls"]

    scheduler = AsyncIOScheduler()
    date = datetime.now().astimezone(UTC) + timedelta(seconds=1)
    scheduler.add_job(
        process_dosars,
        args=(articoluls, url),
        run_date=date,
        timezone="utc",
    )
    scheduler.start()

    return {
        "ok": True,
        "message": f"process started",
    }


@app.post("/update")
async def subscribe_for_update(url: str, data: str) -> dict:
    """Subscribe for updates."""
    data = json.loads(data)
    scheduler = AsyncIOScheduler()
    date = datetime.now().astimezone(UTC) + timedelta(seconds=1)
    scheduler.add_job(
        webhook_response,
        args=(url, data, scheduler),
        run_date=date,
        timezone="utc",
    )
    scheduler.start()

    logger.info(f"/update trigerred with data - {data}. scheduler started")

    return {
        "ok": True,
        "message": (
            f"Successful request! When scraping is finished,"
            f" we will send new data to the URL: {url}.",
        ),
    }


async def process_dosars(articolul_num: int | None, url: str = None):
    p = ParserDosars()
    dosars = await p.parse_dosars(articolul_num=articolul_num)

    try:
        await write_dosars_by_parts(dosars)
        msg = {
            "ok": True,
            "message": f"{len(dosars)} dosars written to db",
            "dosars": [d.model_dump_json(indent=2) for d in dosars],
        }
    except Exception as e:
        logger.exception(e)
        msg = {
            "ok": False,
            "message": f"write dosars to db was failed with error {str(e)}",
            "dosars": [d.model_dump_json() for d in dosars],
        }

    @aiohttp_session(timeout=10)
    async def send_request(_, session: aiohttp.ClientSession):
        async with session.post(url, json=msg) as r:
            pass

    if url:
        try:
            await send_request("")
        except Exception as e:
            logger.exception(e)


async def get_result(request: dict) -> dict:
    """Get results."""
    parser = ParserCetatenie()
    src_path = f"{time.time()}_{len(str(request))}"
    try:
        res = await parser.parse_articoluls(request, src_path)
    except Exception as exc:
        logger.exception(exc)
        data = {
            "ok": False,
            "message": f"{exc.__class__.__name__}: {exc!s}",
            "result": {},
        }
    else:
        data = {
            "ok": False,
            "message": f"Wrong result: {res}",
            "result": {},
        }

        if isinstance(res, dict):
            data = {
                "ok": True,
                "message": "the proccess finish successfully",
                "result": res,
            }

            try:
                for articolul in res:
                    articolul_num = int(articolul[-2:])
                    await write_result(articolul_num, res[articolul])
            except Exception as exc:
                logger.exception(exc)

    return data


async def webhook_response(
    url: str, request: dict, scheduler: AsyncIOScheduler
) -> None:
    """Send webhook response."""
    data = await get_result(request=request)

    try:
        async with aiohttp.ClientSession() as session:  # noqa: SIM117
            async with session.post(url, json=data):
                pass
    except Exception as exc:
        data = {
            "ok": False,
            "message": f"{exc.__class__.__name__}: {exc!s}",
            "result": {},
        }
        logger.exception(exc)
        async with aiohttp.ClientSession() as session:  # noqa: SIM117
            async with session.post(url, json=data):
                pass
    finally:
        scheduler.remove_all_jobs()
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    logger.add(
        "log_{time}.log",
        level="INFO",
        rotation="1 day",
    )
    asyncio.run(setup_db())
    uvicorn.run(app, host="0.0.0.0", port=8000)
