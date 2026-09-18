"""Daily event text from Wikipedia's Current Events Portal.

Why a second news source. GDELT's *timeline* endpoint is what the daily measures are
built on: it counts every article it monitored, one request covers the whole window,
and it is the right instrument for measuring how much coverage a day drew. Its
*article* endpoint is a different story - it caps at 250 records per day, and in
practice refuses so large and random a share of requests that fetching a few dozen
days takes hours and does not reproduce.

So the event text comes from Wikipedia's Current Events Portal instead: one curated,
dated, sourced page per day, fetched through the MediaWiki API without throttling.
It is a chronology rather than a wire feed, which suits the job it does here - naming
what happened on each selected day in Table 1, and giving the lexicon and FinBERT a
common piece of text to read. It is not used to *select* the days; that is done by
the GDELT coverage measures, before this module is ever called.

One page per day is cached under data/news/wiki/.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import time

import requests
from bs4 import BeautifulSoup

from config import NEWS, USER_AGENT

WIKI_API = "https://en.wikipedia.org/w/api.php"
IRAN = re.compile(r"\b(Iran|Iranian|Iranians|Tehran|Hormuz|Khamenei|IRGC)\b", re.I)
NAV = {"edit", "history", "watch", "purge"}

_CACHE = NEWS / "wiki"
_CACHE.mkdir(parents=True, exist_ok=True)
_last = [0.0]


def _page_name(day: dt.date) -> str:
    return f"Portal:Current_events/{day.year}_{day.strftime('%B')}_{day.day}"


def day_events(day: dt.date, iran_only: bool = True) -> list[str]:
    """Leaf bullet items for one day, optionally filtered to Iran-related ones."""
    path = _CACHE / f"{day.isoformat()}.json"
    if path.exists():
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            items = []
    else:
        wait = 1.0 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = requests.get(WIKI_API, timeout=45,
                             headers={"User-Agent": USER_AGENT},
                             params={"action": "parse", "page": _page_name(day),
                                     "prop": "text", "format": "json",
                                     "formatversion": "2"})
            js = r.json()
        except (requests.RequestException, json.JSONDecodeError):
            return []
        if "parse" not in js:
            path.write_text("[]", encoding="utf-8")
            return []
        soup = BeautifulSoup(js["parse"]["text"], "html.parser")
        # Only leaf list items are events; the outer ones are topic breadcrumbs.
        items = []
        for li in soup.find_all("li"):
            if li.find("li"):
                continue
            txt = li.get_text(" ", strip=True)
            txt = re.sub(r"\s+([,.;:])", r"\1", txt)
            if len(txt.split()) < 5 or txt.strip().lower() in NAV:
                continue
            items.append(txt)
        path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")

    return [t for t in items if IRAN.search(t)] if iran_only else items
