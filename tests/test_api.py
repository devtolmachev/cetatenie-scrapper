import json

import aiohttp
import pytest


@pytest.mark.asyncio()
async def test_subscribe() -> None:
    """Test for subscribtion."""
    session = aiohttp.ClientSession()
    data = json.dumps({"articolul_10": ["925P"], "articolul_11": ["935P"]})
    url_receive = "http://127.0.0.1:7654/"
    async with session.post(
        f"http://127.0.0.1:8000/update?url={url_receive}&data={data}"
    ) as response:
        assert (await response.json())["ok"] is True
