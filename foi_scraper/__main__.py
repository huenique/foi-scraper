"""
foi_scraper.__main__
--------------------

This module contains the logic for scraping www.foi.gov.ph
"""
import csv
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import requests
from bs4 import BeautifulSoup
from loguru import logger

from foi_scraper.utils import count_requests, save_page_url, total_requests

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    colorize=True,
    format="[{time}] [{level}] — {message}",
)

FOI_URL = "https://www.foi.gov.ph"
MONTH_DAY_YEAR = re.compile(
    r"(?:January|February|March|April|May|June|July|August|September|October|November"
    r"|December) \d{1,2}, \d{4}"
)
CSV_HEADERS = [
    "title",
    "agency",
    "requester name",
    "request date",
    "purpose",
    "status",
    "coverage",
    "tracking number",
]


def fetch_content(url: str) -> str:
    """Fetch the page content of the specified URL.

    Args:
        url (str): The page url.

    Returns:
        str: The page content.
    """
    page = requests.get(url)

    return page.text


def parse_content(content: str) -> BeautifulSoup:
    """Parse static HTML code.

    Args:
        content (str): Static HTML code.

    Returns:
        BeautifulSoup: An instance of `bs4.BeautifulSoup`.
    """
    return BeautifulSoup(content, "html.parser")


def fetch_next_url(soup: BeautifulSoup) -> Any | None:
    """Extract the URL of the next page.

    Args:
        soup (BeautifulSoup): An instance of `bs4.BeautifulSoup`.

    Raises:
        IndexError: If there are no pages left to scrape.

    Returns:
        Any | None: URL of the next page if it exists, None otherwise.
    """
    try:
        next_ = soup.find_all("a", class_="btn -icon ion-search -block -blueberry")[0][
            "href"
        ]
        if "/requests" not in next_:
            print(next_)
            raise IndexError
        return next_
    except IndexError:
        return None


def extract_content(soup: BeautifulSoup) -> tuple[int, Iterable[tuple[Any, ...]]]:
    """Extract the government agency, request date, purpose, status from all
    requests.

    Args:
        soup (BeautifulSoup): An instance of `bs4.BeautifulSoup`.

    Returns:
        tuple[int, Iterable[tuple[Any, ...]]]: List elements are related to other list
            elements on the basis of indices. The return order of the extracted
            information is as follows:
            0: Titles
            1: Agencies
            2: Requester names
            3: Request dates
            4: Purposes
            5: Statuses
            6: Coverages
            7: Tracking numbers
    """
    titles: list[str] = []
    agencies: list[str] = []
    requesters: list[str] = []
    request_dates: list[str] = []
    purposes: list[str] = []
    statuses: list[str] = []
    coverages: list[str] = []
    tracking_nums: list[str] = []

    for meta, stat, title in zip(
        soup.find_all("p", {"class": "description"}),
        soup.find_all("label", {"class": "component-status"}),
        soup.find_all("h4", {"class": "title"}),
    ):
        metadata = meta.find_all("span")

        # Extract request title
        titles.append(title.get_text().strip())

        # Extract department
        agencies.append(metadata[0].get_text().strip())

        # Extract name of requester
        requesters.append(metadata[1].get_text().strip())

        # Extract request date
        if date_match := MONTH_DAY_YEAR.search(meta.get_text().strip()):
            request_dates.append(date_match.group())

        # Extract purpose
        purposes.append(metadata[2].get_text().strip())

        # Extract status
        statuses.append(stat.get_text().strip())

        # Extract date of coverage
        coverages.append(metadata[3].get_text().strip())

        # Extract tracking number
        tracking_nums.append(metadata[4].get_text().strip())

    # ! DO NOT change the return order
    return (
        len(titles),
        zip(
            titles,
            agencies,
            requesters,
            request_dates,
            purposes,
            statuses,
            coverages,
            tracking_nums,
        ),
    )


def init_csv_file() -> None:
    """Initialize the csv file containing scraped data with predefined headers.

    NOTE: `CSV_HEADERS` or headers depend on the return value/s of `extract_content()`.
    """
    if Path("foi_requests.csv").is_file():
        return

    with open("foi_requests.csv", mode="w", encoding="utf-8") as file_object:
        writer = csv.writer(file_object)
        writer.writerow(CSV_HEADERS)


def append_to_csv(rows: Iterable[tuple[Any, ...]]) -> None:
    """
    Append scraped information to a csv file.

    Args:
        rows (Iterable[tuple[Any, ...]]): Tuple containing lists of scraped
            information.
    """
    row_num = 0

    with open("foi_requests.csv", mode="a", encoding="utf-8") as file_object:
        writer = csv.writer(file_object, escapechar="\\")
        for row in rows:
            writer.writerow(row)
            row_num += 1

    logger.success(
        f"requests collected: {row_num} / total: {int(total_requests()) + row_num}\n"
    )


if __name__ == "__main__":
    init_csv_file()

    # NOTE: Some variables are suffixed with "_" to avoid ovewrites.
    # NOTE: Change the value of `page_` to start at a specific page. See `pages.txt` to
    # resume the previous run.
    page_ = f"{FOI_URL}/requests"

    while True:
        save_page_url(page_)
        logger.info(f"scraping: {page_}")
        soup_ = parse_content(fetch_content(page_))
        result_ = extract_content(soup_)
        append_to_csv(result_[1])
        count_requests(result_[0])

        if (url_ := fetch_next_url(soup_)) is None:
            break

        page_ = f"{FOI_URL}/{url_}"
