"""A small, polite client for the GDELT DOC 2.0 API.

GDELT asks for no more than one request every five seconds and returns a plain-text
429 notice (not a JSON error) when it thinks you have gone too fast, so every call
here is throttled, retried with backoff, and checked for a JSON body before parsing.

Two endpoints are used:

  timeline_volume()  daily share of worldwide monitored coverage matching a query.
                     This is the *uncapped* attention measure - it counts all
                     matching articles, not just the 250 a single artlist request
                     can return.

  day_articles()     up to 250 article records (title, domain, seen-time) for one
                     day. This is the text corpus the NLP scoring runs on.
"""
from __future__ import annotations

import datetime as dt
import json
import random
import time
from typing import Any

import pandas as pd
import requests

from config import GDELT_DOC, MAX_RECORDS, GDELT_SLEEP, GDELT_MAX_RETRIES, USER_AGENT

_last_call = [0.0]


def _get(params: dict[str, str]) -> dict[str, Any] | None:
    """One throttled, retried GDELT request. Returns parsed JSON or None.

    GDELT's refusals turn out to be mostly load-based rather than strictly
    rate-based - backing off to one request every 16 seconds does no better than
    one every 8 - so the wait is held roughly constant with a little jitter and the
    request is simply retried.
    """
    for attempt in range(GDELT_MAX_RETRIES):
        wait = GDELT_SLEEP + random.uniform(0, 2.0) - (time.time() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.time()
        try:
            r = requests.get(GDELT_DOC, params=params, timeout=120,
                             headers={"User-Agent": USER_AGENT})
        except requests.RequestException as e:
            print(f"    request error ({e}); retrying")
            continue
        text = r.text.lstrip()
        # GDELT returns rate-limit notices as 200/429 plain text, not JSON.
        if r.status_code == 200 and text.startswith("{"):
            try:
                return r.json()
            except json.JSONDecodeError:
                pass
        if attempt == GDELT_MAX_RETRIES - 1:
            print(f"    giving up after {GDELT_MAX_RETRIES} attempts "
                  f"(status {r.status_code}): {text[:70]}")
    return None


def timeline_volume(query: str, start: dt.date, end: dt.date) -> pd.Series:
    """Daily volume intensity: matching articles as a share of all GDELT coverage."""
    js = _get({
        "query": query, "mode": "timelinevol", "format": "json",
        "startdatetime": start.strftime("%Y%m%d") + "000000",
        "enddatetime": end.strftime("%Y%m%d") + "235959",
    })
    if not js or not js.get("timeline"):
        raise RuntimeError("GDELT returned no timeline; try again in a few minutes")
    data = js["timeline"][0]["data"]
    s = pd.Series({pd.Timestamp(d["date"][:8]): float(d["value"]) for d in data})
    return s.sort_index()


def timeline_tone(query: str, start: dt.date, end: dt.date) -> pd.Series:
    """Daily average GDELT tone of matching coverage (negative = more negative)."""
    js = _get({
        "query": query, "mode": "timelinetone", "format": "json",
        "startdatetime": start.strftime("%Y%m%d") + "000000",
        "enddatetime": end.strftime("%Y%m%d") + "235959",
    })
    if not js or not js.get("timeline"):
        raise RuntimeError("GDELT returned no tone timeline")
    data = js["timeline"][0]["data"]
    s = pd.Series({pd.Timestamp(d["date"][:8]): float(d["value"]) for d in data})
    return s.sort_index()


def day_articles(query: str, day: dt.date) -> list[dict[str, str]]:
    """Up to MAX_RECORDS article records for one calendar day (UTC)."""
    js = _get({
        "query": query, "mode": "artlist", "maxrecords": str(MAX_RECORDS),
        "format": "json", "sort": "hybridrel",
        "startdatetime": day.strftime("%Y%m%d") + "000000",
        "enddatetime": day.strftime("%Y%m%d") + "235959",
    })
    if js is None:
        return []
    out = []
    for a in js.get("articles", []):
        out.append({
            "seendate": a.get("seendate", ""),
            "domain": a.get("domain", ""),
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "sourcecountry": a.get("sourcecountry", ""),
        })
    return out
