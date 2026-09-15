"""Shared paths, dates and constants for the Assignment 2 pipeline."""
from pathlib import Path
import datetime as dt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
MARKET = DATA / "market"
LEXICONS = DATA / "lexicons"
FIGURES = ROOT / "figures"
TABLES = ROOT / "report_tables"

for d in [RAW / "statements", RAW / "minutes", RAW / "speeches", INTERIM, MARKET, LEXICONS, FIGURES, TABLES]:
    d.mkdir(parents=True, exist_ok=True)

# Sample window
START_DATE = dt.date(2018, 2, 5)   # Powell sworn in as Chair
END_DATE = dt.date(2026, 9, 15)    # day the assignment is due

# Chair transition
WARSH_START = dt.date(2026, 5, 22)  # Kevin Warsh sworn in as Fed Chair

CHAIRS = {
    "Powell": (dt.date(2018, 2, 5), dt.date(2026, 5, 21)),
    "Warsh": (dt.date(2026, 5, 22), dt.date(2099, 1, 1)),
}

def chair_for_date(d: dt.date) -> str:
    for name, (start, end) in CHAIRS.items():
        if start <= d <= end:
            return name
    return "Unknown"

USER_AGENT = "NYU FRE-GY-7871 student research (course assignment; contact via github.com/SM-dot)"

# FRED series used
FRED_SERIES = {
    "T10Y2Y": "10s2s spread (10y - 2y Treasury)",
    "DGS1": "1-year Treasury yield",
    "DGS3MO": "3-month T-bill yield (control)",
}

# Yahoo Finance tickers
YAHOO_TICKERS = {
    "DX-Y.NYB": "DXY (dollar index)",
    "IWF": "Russell 1000 Growth ETF",
    "IWN": "Russell 2000 Value ETF",
}
