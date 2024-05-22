"""Contain a REST API."""

import json
import time
from datetime import UTC, datetime, timedelta

import aiohttp
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from loguru import logger

from bubble_parser.parser import ParserCetatenie

app = FastAPI()


@app.post("/is_work")
async def is_work() -> dict:
    """Check if server is working."""
    return {"ok": True, "message": "yes, server working"}


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

    return {
        "ok": True,
        "message": (
            f"Successful request! When scraping is finished,"
            f" we will send new data to the URL: {url}.",
        ),
    }


async def webhook_response(
    url: str, request: dict, scheduler: AsyncIOScheduler
) -> None:
    """Send webhook response."""
    parser = ParserCetatenie()
    src_path = f"{time.time()}_{len(str(request))}"
    try:
        res = await parser.parse_articoluls(request, src_path)
    except Exception as exc:
        data = {"ok": False, "message": str(exc), "data": exc}
    else:
        data = {
            "ok": True,
            "message": "the proccess finish successfully",
            "data": res,
        }

    if not isinstance(res, dict):
        data = {"ok": False, "message": "Wrong result", "data": res}

    try:
        async with aiohttp.ClientSession() as session:  # noqa: SIM117
            async with session.post(url, data=json.dumps(data)):
                pass
    except Exception as err:
        logger.exception(err)
    finally:
        scheduler.remove_all_jobs()
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
