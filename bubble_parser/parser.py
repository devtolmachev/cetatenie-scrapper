"""Contains parser for `cetatenie.just.ro`."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import datetime
import pickle
import random
import re
import shutil
from functools import wraps
from pathlib import Path
from typing import Any, Callable

import aiofiles
from aiohttp import ClientSession, ClientTimeout, TCPConnector
import aiohttp
import ua_generator
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent
from pdfminer.high_level import extract_text
import tempfile
import fitz
from dateutil.parser import parse

from bubble_parser.app_types import Dosar


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

            headers = {"User-Agent": UserAgent().random, "Accept": "*/*"}
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


class ParserCetatenie:
    """Class which provide web scrapping methods."""

    articolul_urls = {
        "10": "https://cetatenie.just.ro/ordine-articolul-10/",
        "11": "https://cetatenie.just.ro/ordine-articolul-1-1/",
    }

    @aiohttp_session(sleeps=(0.7, 2))
    async def parse_articoluls(  # noqa: C901, PLR0912
        self, session: ClientSession, articoluls_data: dict, path_data: str
    ) -> dict[str, list[dict]]:
        """Parse new articles.

        Parameters
        ----------
        session : ClientSession
            generated arg.
        articoluls_data : dict
            like
            `{
                “articul_10“: [“932P”, “931P”, “815P”, “828P”],
                “articul_11“: [“132P”, “231P”, “215P”, “328P”]
            }`.
        path_data : str
            path to save downloaded PDF's.

        Returns
        -------
        dict[str, list[dict]]
            dictionary with only updated articles. like

            `{
                “articul_10“: [{
                    "list_name": "932P",
                    "number_order": "(16309/2020)",
                    "year": 2024,
                    "date": "16.05.2024"
                    },
                    {
                    "list_name": "933P",
                    "number_order": "(16309/2020)",
                    "year": 2024,
                    "date": "16.05.2024"
                    }],
                “articul_11“: [{
                    "list_name": "934P",
                    "number_order": "(16309/2020)",
                    "year": 2024,
                    "date": "16.05.2024"
                    },
                    {
                    "list_name": "935P",
                    "number_order": "(16309/2020)",
                    "year": 2024,
                    "date": "16.05.2024"
                    }]
            }`.

        Raises
        ------
        TypeError
            if articoluls_data keys don't validated.
        """
        tasks = []
        # Create path for PDF's
        Path(path_data).mkdir(parents=True, exist_ok=True)

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

                    num = article.find("a").text

                    # If num in request data. Means this article is old
                    if num in articoluls_data[articolul]:
                        continue

                    # Get raw datetime article
                    _article_date = re.findall(r"\d+\.\d+\.\d+", article.text)
                    if not _article_date:
                        continue

                    article_date = datetime.datetime.strptime(
                        _article_date[0],
                        "%d.%m.%Y",
                    ).replace(tzinfo=datetime.UTC)

                    # Collect articles over the last 4 years
                    if (
                        datetime.datetime.now(datetime.UTC) - article_date
                    ).days // 365 > 4:
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

        articoluls = {}
        pdf = ParserPDF()

        @aiohttp_session(timeout=2, attempts=2, sleeps=(0.5, 3.0))
        async def collect_numbers(
            self: ParserCetatenie,  # noqa: ARG001
            path: str,
            dt: datetime.datetime,
            articolul_num: int,
            num: int,
        ):
            numbers = await pdf.extract_numbers(path)

            for number_order in numbers:
                articoluls[f"articolul_{articolul_num}"].append(
                    {
                        "list_name": num,
                        "number_order": number_order,
                        "year": dt.year,
                        "date": dt.strftime("%d.%m.%Y"),
                    }
                )

        collect_number_tasks = []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if not isinstance(res, tuple):
                continue

            path, dt, articolul_num, num = res

            if not articoluls.get(f"articolul_{articolul_num}"):
                articoluls[f"articolul_{articolul_num}"] = []

            collect_number_tasks.append(
                collect_numbers(
                    self, path=path, dt=dt, articolul_num=articolul_num, num=num
                )
            )

        await asyncio.gather(*collect_number_tasks, return_exceptions=True)

        shutil.rmtree(path_data)
        return articoluls

    @aiohttp_session(sleeps=(2, 7))
    async def _collect_data(
        self,
        session: ClientSession,
        url: str,
        dt: datetime.datetime,
        articolul_num: int,
        num: int,
        src_path: str,
    ) -> tuple[str, datetime.datetime, int]:
        async with session.get(url) as resp:
            resp.raise_for_status()

            fn = f"{src_path}/{url.split("/")[-1]}"
            async with aiofiles.open(fn, "ab") as f:
                async for chunk in resp.content.iter_chunked(1024):
                    await f.write(chunk)

            return fn, dt, articolul_num, num, url

        return await parse(self)


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


class ParserPDF:
    """Class which provide methods for parsing pdf."""

    async def extract_numbers(self, path_to_pdf: str | Path) -> list[str]:
        """Extract numbers from pdf which downloaded from cetatenie.just.ro."""
        if not Path(path_to_pdf).exists():
            raise FileNotFoundError(path_to_pdf)

        text = extract_text(path_to_pdf)
        lines = text.split("\n")
        return [
            i[0]
            for i in filter(
                None, [re.findall(r"\(\d+/\d+\)", line) for line in lines]
            )
        ]

    def _find_columns_for_dosar(self, path_to_pdf: str):
        pages = fitz.open(path_to_pdf)
        page = pages[0]
        obj = page.get_textpage().extractDICT()
        columns = [
            span["text"]
            for block in obj["blocks"]
            for line in block["lines"]
            for span in line["spans"]
            if span["font"].lower().count("bold")
        ]
        for c in columns:
            i = columns.index(c)
            if c.endswith(" "):
                columns[i] = f"{c.strip()} {columns.pop(i+1).strip()}"
        return columns

    def _find_content_for_dosar(self, path_to_pdf: str):
        pages = fitz.open(path_to_pdf)
        contents = []
        columns = self._find_columns_for_dosar(path_to_pdf)
        for page in pages:
            obj = page.get_textpage().extractDICT()
            line_content = []
            for block in obj["blocks"]:
                for line in block["lines"]:
                    if any(
                        s["font"].lower().count("bold") for s in line["spans"]
                    ):
                        continue

                    for span in line["spans"]:
                        v = span["text"].strip()
                        line_content.append(v)

                line_raw = "$".join(line_content.copy())
                if not line_raw:
                    continue
                contents.append(line_raw)
                line_content.clear()

        return columns, contents

    def extract_dosar_data(
        self, path_to_pdf: str | Path, articolul_num: int, year: int
    ) -> list[Dosar]:
        """Parse dosar data from pdf and transform to list of `Dosar`"""
        if not Path(path_to_pdf).exists():
            raise FileNotFoundError(path_to_pdf)

        columns, lines = self._find_content_for_dosar(path_to_pdf)
        return [
            Dosar(articolul_num=articolul_num, year=year, raw_dosar=raw_dosar)
            for raw_dosar in lines
        ]


class ParserDosars:
    urls = {
        "10": "https://cetatenie.just.ro/stadiu-dosar/#1576832764783-e9f4e574-df23",
        "11": "https://cetatenie.just.ro/stadiu-dosar/#1576832773102-627a212f-45ce",
    }

    @property
    def headers(self):
        headrs = {
            "Accept": "*/*",
            "Accept-Language": "*",
            "Connection": "keep-alive",
            "Referer": "https://cetatenie.just.ro/stadiu-dosar/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
        ua = ua_generator.generate(platform=("android", "ios"))
        for k, v in ua.headers.get().items():
            headrs[k] = v

        return headrs

    async def _download_pdf(self, url: str, year: int, src_path: str):
        @aiohttp_session(sleeps=(4, 8), timeout=15)
        async def parse(self, session: aiohttp.ClientSession):
            session._default_headers = self.headers
            async with session.get(url) as resp:
                content = await resp.read()

            await asyncio.to_thread(resp.raise_for_status)

            fn = str(Path(src_path) / f"{url.split("/")[-1]}")

            async with aiofiles.open(fn, "wb") as f:
                await f.write(content)

            return fn, year

        return await parse(self)

    async def _parse_dosars(self, articolul_nums: list[int]):
        @aiohttp_session()
        async def parse(_, session: aiohttp.ClientSession, articolul_num: int):
            session._default_headers = self.headers
            async with session:
                url = self.urls[str(articolul_num)]
                async with session.get(url) as resp:
                    html = await resp.text()
                soup = BeautifulSoup(html, "lxml")
                id_panel = url.split("#")[-1]
                records_raw = (
                    soup.find("div", class_="vc_tta-panels")
                    .find("div", id=id_panel)
                    .find("ul")
                    .find_all("li")
                )
                tasks = []
                records = []
                for r in records_raw:
                    a = r.find("a")
                    if not a:
                        continue
                    records.append((a.string, a["href"]))

                prefix = f"{time.time()}-{articolul_num}-"
                with tempfile.TemporaryDirectory(prefix=prefix) as tempdir:
                    dt_now = datetime.datetime.now()
                    for year, url in records:
                        if dt_now.year - int(year) > 6:
                            continue

                        tasks.append(
                            self._download_pdf(
                                url=url,
                                year=year,
                                src_path=tempdir,
                            )
                        )
                    paths = await asyncio.gather(*tasks, return_exceptions=True)
                    p = ParserPDF()

                    def _pool():
                        res = []
                        with ThreadPoolExecutor() as exec:
                            for r in exec.map(
                                p.extract_dosar_data,
                                [p[0] for p in paths],
                                [articolul_num for _ in paths],
                                [p[1] for p in paths],
                            ):
                                res.append(r)
                            return res

                    return await asyncio.to_thread(_pool)

        async_tasks = [parse(self, num) for num in articolul_nums]
        res = await asyncio.gather(*async_tasks)
        return [
            dosar
            for articolul_group in res
            for group in articolul_group
            for dosar in group
        ]

    async def parse_dosars(
        self, articolul_num: int | None = None
    ) -> list[Dosar]:
        articolul_nums = [articolul_num]
        if not articolul_num:
            articolul_nums = [10, 11]

        return await self._parse_dosars(articolul_nums)


async def main() -> None:  # noqa: D103
    p = ParserPDF()
    s = ParserDosars()
    result = await s.parse_dosars()
    ...


if __name__ == "__main__":
    asyncio.run(main())
