import hashlib
import urllib.parse
import urllib.robotparser

import requests
from bs4 import BeautifulSoup


def is_allowed_by_robots(url: str, user_agent: str, timeout_seconds: int) -> bool:
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    response = requests.get(
        robots_url, headers={"User-Agent": user_agent}, timeout=timeout_seconds
    )
    response.raise_for_status()

    parser = urllib.robotparser.RobotFileParser()
    parser.parse(response.text.splitlines())
    return parser.can_fetch(user_agent, url)


def get_section_hash(url: str, selector: str, user_agent: str, timeout_seconds: int) -> str:
    response = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout_seconds)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    target = soup.select_one(selector)
    if target is None:
        raise ValueError(f"Selector not found: {selector}")

    text = target.get_text(separator="\n", strip=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
