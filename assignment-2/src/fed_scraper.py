"""Scrapes FOMC statements, minutes, Chair speeches, testimony and press
conference transcripts from federalreserve.gov, Feb 2018 to present.

Everything is a plain GET to a static HTML or PDF page: the Fed's site does
not require auth or rate-limit aggressively, but we throttle politely anyway.
"""
import io
import re
import time
import datetime as dt
from dataclasses import dataclass, asdict

import requests
from bs4 import BeautifulSoup

from config import USER_AGENT, START_DATE, END_DATE, chair_for_date

BASE = "https://www.federalreserve.gov"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})
THROTTLE = 0.25


def get(url: str, retries: int = 3) -> requests.Response | None:
    for attempt in range(retries):
        try:
            r = SESSION.get(url, timeout=20)
            time.sleep(THROTTLE)
            if r.status_code == 200:
                if "charset" not in (r.headers.get("content-type") or "").lower():
                    r.encoding = "utf-8"
                return r
            if r.status_code == 404:
                return None
        except requests.RequestException:
            time.sleep(1.0 * (attempt + 1))
    return None


def clean_htm_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    article = soup.find(id="article") or soup.find(class_="col-xs-12 col-sm-8 col-md-8") or soup
    text = article.get_text("\n")
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def pdf_to_text(content: bytes) -> str:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            text_parts.append(t)
    return "\n".join(text_parts)


@dataclass
class Doc:
    doc_type: str          # statement | minutes | speech | testimony | presser
    date: str               # YYYY-MM-DD, release date
    chair: str
    speaker: str
    title: str
    url: str
    n_words: int


def yyyymmdd(url: str) -> str | None:
    m = re.search(r"(20\d{6})", url)
    if not m:
        return None
    s = m.group(1)
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"


def collect_meeting_links() -> dict:
    """Returns {date: {"statement": url|None, "minutes": url|None}}"""
    pages = ["monetarypolicy/fomccalendars.htm"] + [
        f"monetarypolicy/fomchistorical{y}.htm" for y in range(2018, 2021)
    ]
    links = {}
    for page in pages:
        r = get(f"{BASE}/{page}")
        if r is None:
            continue
        for href in re.findall(r'href="([^"]+)"', r.text):
            if re.search(r"/newsevents/pressreleases/monetary\d{8}a\.htm$", href):
                d = yyyymmdd(href)
                links.setdefault(d, {}).setdefault("statement", BASE + href)
            elif re.search(r"/monetarypolicy/fomcminutes\d{8}\.htm$", href):
                d = yyyymmdd(href)
                links.setdefault(d, {}).setdefault("minutes", BASE + href)
    return links


def collect_speaker_links(section: str, speaker_keys: list[str], years: range) -> list[tuple[str, str]]:
    """section: 'speech' or 'testimony'. Returns list of (date, url)."""
    out = []
    for y in years:
        r = get(f"{BASE}/newsevents/{section}/{y}-{section}es.htm" if section == "speech"
                else f"{BASE}/newsevents/{section}/{y}-{section}.htm")
        if r is None:
            continue
        for href in re.findall(r'href="([^"]+)"', r.text):
            m = re.match(rf"^/newsevents/{section}/([a-z]+)(\d{{8}})a\.htm$", href)
            if m and m.group(1) in speaker_keys:
                out.append((f"{m.group(2)[0:4]}-{m.group(2)[4:6]}-{m.group(2)[6:8]}", BASE + href))
    return out


def fetch_document_text(url: str) -> str:
    r = get(url)
    if r is None:
        return ""
    if url.lower().endswith(".pdf"):
        return pdf_to_text(r.content)
    return clean_htm_text(r.text)


def presconf_url_for(date_str: str) -> str:
    d = date_str.replace("-", "")
    return f"{BASE}/mediacenter/files/FOMCpresconf{d}.pdf"


def release_datetime_from_text(text: str, fallback_date: str) -> str:
    """Look for 'For release at H:MM a.m./p.m.' boilerplate; else assume 2:00 PM ET."""
    m = re.search(r"[Ff]or release at (\d{1,2}:\d{2}\s*[ap]\.?m\.?)", text)
    if m:
        return f"{fallback_date} {m.group(1).upper().replace('.', '')} ET"
    return f"{fallback_date} 2:00 PM ET"
