"""Contains parser for `cetatenie.just.ro`."""

from __future__ import annotations

import asyncio
import datetime
import json
import random
import re
import shutil
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Coroutine, List

import aiofiles
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent
from pdfminer.high_level import extract_text


def aiohttp_session(
    timeout: int = 5,
    attempts: int = 5,
    sleeps: tuple[float, float] = (0.5, 1.5),
) -> Any:
    """Decorate web scrapping function.
    This decorator generate aiohttp.ClientSession.

    Parameters
    ----------
    timeout : int, optional
        timeout, by default 5.
    attempts : int, optional
        attempts for parse, by default 5.
    sleeps : tuple[float, float], optional
        range for `asyncio.sleep(random.uniform())`, by default (0.5, 1.5).

    Returns
    -------
    Any
        func result.
    """

    def wrapper(f: Callable):
        @wraps(f)
        async def inner(self: ParserCetatenie, *args, **kwargs):
            nonlocal attempts

            headers = HEADERS
            headers["User-Agent"] = UserAgent().random
            client_timeout = ClientTimeout(total=timeout)
            connector = TCPConnector(ssl=False, limit_per_host=10)
            async with ClientSession(
                connector=connector,
                timeout=client_timeout,
                headers=headers,
                trust_env=True,
            ) as session:
                try:
                    result = await f(self, session, *args, **kwargs)
                except asyncio.TimeoutError:
                    if attempts > 0:
                        attempts = attempts - 1
                        await asyncio.sleep(random.uniform(*sleeps))
                        return await inner(self, *args, **kwargs)
                    raise
                else:
                    return result
                finally:
                    if not session.closed:
                        await session.close()

        return inner

    return wrapper


HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,my;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
}


PDF_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,my;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://cetatenie.just.ro/ordine-articolul-1-1/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
}


class ParserCetatenie:
    """Class which provide web scrapping methods."""

    articolul_urls = {
        "10": "https://cetatenie.just.ro/ordine-articolul-10/",
        "11": "https://cetatenie.just.ro/ordine-articolul-1-1/",
    }

    @aiohttp_session(sleeps=(4, 10), attempts=10, timeout=3)
    async def _collect_scrapping_tasks(
        self, session: ClientSession, articoluls_data: dict, path_data: str
    ) -> List[Coroutine]:
        """Collect correctly tasks for scrapping articoluls.

        Parameters
        ----------
        session : ClientSession
            generated aiohttp session.
        articoluls_data : dict
            request body.
        path_data : str
            path that will passed to tasks.

        Returns
        -------
        List[Coroutine]
            list with tasks. you need to call `asyncio.gather(tasks)`

        Raises
        ------
        TypeError
            if articoluls data is wrong
        """
        tasks = []

        for articolul in articoluls_data:
            if not articolul.split("_")[-1].isdigit():
                msg = (
                    "articolul must be named like "
                    f"`articolul_10`, now - {articolul}"
                )
                raise TypeError(msg)

            # Article num. e.g. 10
            articolul_num = int(articolul.split("_")[-1])
            # Url for needed article
            url = self.articolul_urls[str(articolul_num)]

            # Set headers
            headers = HEADERS
            headers["User-Agent"] = session.headers["User-Agent"]
            session._default_headers = headers

            async with session.get(url) as resp:
                page_text = await resp.text()

            soup = BeautifulSoup(page_text, "html.parser")
            articles_block = soup.find("div", class_="penci-entry-content")

            # Iters for years articles
            for year_block in articles_block.find_all("ul"):
                if not isinstance(year_block, Tag):
                    continue

                # Iters for articles in concrete year
                for article in year_block.find_all("li"):
                    if not isinstance(article, Tag):
                        continue

                    if article.find("a") is None:
                        continue

                    # Get raw datetime article
                    _article_date = re.findall(r"\d+\.\d+\.\d+", article.text)
                    if not _article_date:
                        continue

                    article_date = datetime.datetime.strptime(
                        _article_date[0],
                        "%d.%m.%Y",
                    ).replace(tzinfo=datetime.UTC)

                    # If this year not in request data, continue it
                    if str(article_date.year) not in articoluls_data[articolul]:
                        continue

                    # If num in request data. Means this article is old
                    num = article.find("a").text
                    if (
                        num
                        in articoluls_data[articolul][str(article_date.year)]
                    ):
                        continue

                    # Collect articles over the last 6 years
                    if (
                        datetime.datetime.now(datetime.UTC) - article_date
                    ).days // 365 > 6:
                        continue

                    link = article.find("a")["href"]
                    task = self._collect_data(
                        url=link,
                        dt=article_date,
                        articolul_num=articolul_num,
                        num=num,
                        src_path=path_data,
                    )
                    tasks.append(task)

        return tasks

    async def parse_articoluls(
        self, articoluls_data: dict, path_data: str
    ) -> dict[str, list[dict]]:
        """Parse new articles.

        Parameters
        ----------
        session : ClientSession
            generated arg.
        articoluls_data : dict
            like
            `{
                "articolul_10": {
                    "2022": [“932P”, “931P”, “815P”, “828P”],
                    "2023": [“932P”, “931P”, “815P”, “828P”]
                }
            }`
        path_data : str
            path to save downloaded PDF's.

        Returns
        -------
        dict[str, list[dict]]
            dictionary with only updated articles. like

        Raises
        ------
        TypeError
            if articoluls_data keys don't validated.
        """
        # Create path for PDF's
        Path(path_data).mkdir(parents=True, exist_ok=True)

        tasks = await self._collect_scrapping_tasks(articoluls_data, path_data)
        articoluls = {}

        pdf = ParserPDF()

        async def collect_numbers(
            path: str,
            dt: datetime.datetime,
            articolul_num: int,
            num: int,
            url_pdf: str,
        ):
            numbers = await asyncio.to_thread(pdf.extract_numbers, path)
            for number_order in numbers:
                articoluls[f"articolul_{articolul_num}"].append(
                    {
                        "list_name": num,
                        "number_order": number_order,
                        "year": dt.year,
                        "date": dt.strftime("%d.%m.%Y"),
                        "pdf_link": url_pdf,
                        "timestamp": time.time(),
                    }
                )

        collect_number_tasks = []
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if not isinstance(res, tuple):
                continue

            path, dt, articolul_num, num, url_pdf = res

            if not articoluls.get(f"articolul_{articolul_num}"):
                articoluls[f"articolul_{articolul_num}"] = []

            collect_number_tasks.append(
                collect_numbers(
                    path=path,
                    dt=dt,
                    articolul_num=articolul_num,
                    num=num,
                    url_pdf=url_pdf,
                )
            )

        await asyncio.gather(*collect_number_tasks)

        shutil.rmtree(path_data)
        return articoluls

    async def _collect_data(
        self,
        url: str,
        dt: datetime.datetime,
        articolul_num: int,
        num: int,
        src_path: str,
    ) -> tuple[str, datetime.datetime, int]:
        @aiohttp_session(sleeps=(5, 10), attempts=10)
        async def parse(self, session: ClientSession):
            # Set headers
            headers = PDF_HEADERS
            headers["User-Agent"] = session.headers["User-Agent"]
            session._default_headers = headers

            await asyncio.sleep(random.uniform(3, 7))

            async with session.get(url) as resp:
                resp.raise_for_status()
                fn = str(Path(src_path) / f"{url.split("/")[-1]}")

                async with aiofiles.open(fn, "wb") as f:
                    await f.write(await resp.read())

            return fn, dt, articolul_num, num, url

        return await parse(self)


class ParserPDF:
    """Class which provide methods for parsing pdf."""

    def extract_numbers(self, path_to_pdf: str | Path) -> list[str]:
        """Extract numbers from pdf which downloaded from cetatenie.just.ro."""
        if not Path(path_to_pdf).exists():
            raise FileNotFoundError(path_to_pdf)

        text = extract_text(path_to_pdf)
        lines = text.split("\n")
        return [
            i.group(2)
            for i in filter(
                None, [re.match(r"(\d+\.) (.+)", string=line) for line in lines]
            )
        ]


async def main() -> None:  # noqa: D103
    p = ParserCetatenie()
    data = {"articolul_10": {"2024": []}, "articolul_11": {"2024": []}}
    src_path = f"{time.time()}_{len(str(data))}"
    result = await p.parse_articoluls(data, src_path)

    with open("result.json", "w") as f:  # noqa: ASYNC101
        f.write(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
