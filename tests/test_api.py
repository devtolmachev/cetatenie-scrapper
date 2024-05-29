import json

import aiohttp
import pytest


@pytest.mark.asyncio()
async def test_subscribe() -> None:
    """Test for subscribtion."""
    session = aiohttp.ClientSession()
    data = json.dumps(
        {"articolul_10": {"2024": ["925P"]}, "articolul_11": {"2024": ["925P"]}}
    )
    url_receive = "http://127.0.0.1:7654/"
    async with session.post(
        f"http://127.0.0.1:8000/update?url={url_receive}&data={data}"
    ) as response:
        assert (await response.json())["ok"] is True


@pytest.mark.asyncio()
async def test_get_updates() -> None:
    """Test for /get_updates endpoint."""
    session = aiohttp.ClientSession()
    data = json.dumps(
        json.dumps(
            {
                "articolul_10": {"2024": ["925P"]},
                "articolul_11": {"2024": ["925P"]},
            }
        )
    )
    async with session.post(
        f"http://127.0.0.1:8000/get_updates?data={data}"
    ) as resp:
        response = await resp.json()
        assert response["ok"] is True
