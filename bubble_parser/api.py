"""Contain a REST API."""

import json
import time
from datetime import UTC, datetime, timedelta

import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from bubble_parser.parser import ParserCetatenie

app = FastAPI()


@app.post("/update")
async def subscribe_for_update(url: str, data: str) -> dict:
    """Subscribe for updates."""
    data = json.loads(data)
    scheduler = AsyncIOScheduler()
    date = datetime.now().astimezone(UTC) + timedelta(seconds=1)
    scheduler.add_job(
        webhook_response, args=(url, data), run_date=date, timezone="utc"
    )
    scheduler.start()

    return {
        "ok": True,
        "message": (
            f"Successful request! When scraping is finished,"
            f" we will send new data to the URL: {url}.",
        ),
    }


async def webhook_response(url: str, request: dict) -> None:
    """Send webhook response."""
    parser = ParserCetatenie()
    src_path = f"{time.time()}_{len(str(request))}"
    try:
        data = await parser.parse_articoluls(request, src_path)
    except Exception as exc:
        data = {"ok": False, "message": str(exc), "raw": exc}
    
    if not isinstance(data, dict):
        data = {"ok": False, "message": "Unknown error", "raw": data}
         
    async with aiohttp.ClientSession() as session:  # noqa: SIM117
        async with session.post(url, data=json.dumps(data)):
            pass
