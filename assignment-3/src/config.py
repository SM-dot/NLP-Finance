"""Shared paths, dates, query strings and variable definitions for Assignment 3.

The sample is calendar-2026-to-date: the Iran war began on February 28, 2026, so a
window that starts on January 2 gives roughly two months of pre-war trading days to
anchor the "low war-news variance" regime.
"""
from pathlib import Path
import datetime as dt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NEWS = DATA / "news"          # one JSON per day of GDELT headlines
MARKET = DATA / "market"
INTERIM = DATA / "interim"
FIGURES = ROOT / "figures"
TABLES = ROOT / "report_tables"

for d in [NEWS, MARKET, INTERIM, FIGURES, TABLES]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- sample window
START_DATE = dt.date(2026, 1, 2)    # first trading day of 2026
END_DATE = dt.date(2026, 9, 11)     # last trading day with both news and market data
                                    # complete (GDELT's timelines run a few days
                                    # behind; the market series go to 9/16)
WAR_START = dt.date(2026, 2, 28)    # US/Israeli strikes on Iran begin

USER_AGENT = "NYU FRE-GY-7871 student research (course assignment; contact via github.com/SM-dot)"

# ---------------------------------------------------------------- news queries
# GDELT DOC 2.0 syntax: space = AND, (a OR b) = OR group.
WAR_QUERY = ("(Iran OR Tehran) (war OR strike OR strikes OR missile OR Hormuz OR "
             "ceasefire OR nuclear OR retaliation) sourcelang:english")

# Themed slices of coverage, each one request covering the whole window. The
# escalation and de-escalation vocabularies are drawn from the same axis as the
# lexicon in warrisk_lexicon.py, so the daily index and the headline scoring in
# script 04 measure the same thing two different ways.
TIMELINE_QUERIES = {
    "war": WAR_QUERY,
    "iran": "(Iran OR Tehran) sourcelang:english",
    "escalation": ("(Iran OR Tehran) (strike OR strikes OR attack OR missile OR "
                   "retaliation OR escalation OR offensive OR blockade OR "
                   "ultimatum) sourcelang:english"),
    "deescalation": ("(Iran OR Tehran) (ceasefire OR truce OR talks OR "
                     "negotiations OR agreement OR deal OR diplomacy) "
                     "sourcelang:english"),
    "hormuz": "Hormuz sourcelang:english",
}

GDELT_DOC = "https://api.gdeltproject.org/api/v2/doc/doc"
MAX_RECORDS = 250          # GDELT's per-request cap on artlist
GDELT_SLEEP = 22.0         # seconds between requests. Their published rate limit is
                           # 5s, but in practice refusals persist at much wider
                           # spacing too (empirically ~20-30% of requests still fail
                           # at 7-16s); a single request after a 30s idle gap
                           # succeeded reliably in testing, suggesting a per-minute
                           # bucket rather than a simple per-request cooldown.
GDELT_MAX_RETRIES = 2      # per pass, at the wider spacing above; script 01/04 make
                           # several passes over whatever is still missing rather
                           # than retrying the same day repeatedly in a tight loop
GDELT_PASSES = 8

# ---------------------------------------------------------------- market data
# x1, the normalising variable. Rigobon and Sack use the two-year Treasury yield,
# because in 2003 it was the cleanest barometer of war risk: its variance rose more
# than six-fold on their war-news days. In 2026 it does not work - the two-year
# yield's variance is only 1.05 times higher on war-news days than on comparison
# days, and the ten-year's is *lower*. A war that arrives as an oil-supply shock in
# an inflationary economy pushes yields down through flight to quality and up
# through the inflation outlook, and the two roughly cancel.
#
# Normalising on a variable that barely responds to the factor puts a number near
# zero in the estimator's denominator, which is exactly the failure of the rank
# condition that Rigobon (2003) warns about. Brent is used instead: its variance
# rises more than six-fold on war-news days, the same order as the two-year yield
# did in 2003. Both normalisations are reported in script 05, since the comparison
# is itself a result.
NORMALISING_VAR = "brent"
PAPER_NORMALISING_VAR = "y2"

# FRED series (public fredgraph.csv endpoint, no API key)
FRED_SERIES = {
    "DGS2": "2-year Treasury yield",
    "DGS10": "10-year Treasury yield",
    "DFII10": "10-year TIPS yield",
    "BAMLC0A4CBBB": "BBB corporate OAS",
    "BAMLH0A0HYM2": "High-yield corporate OAS",
    "DTWEXBGS": "Broad nominal dollar index",
    "DGS3MO": "3-month bill yield",
}

# Yahoo Finance tickers
YAHOO_TICKERS = {
    "^GSPC": "S&P 500",
    "^STOXX50E": "Euro Stoxx 50",
    "^N225": "Nikkei 225",
    "^TA125.TA": "Tel Aviv 125",
    "EEM": "MSCI Emerging Markets ETF",
    "BZ=F": "Brent crude front-month futures",
    "GC=F": "Gold futures",
    "XLE": "US energy sector ETF",
    "JETS": "US airline ETF",
    "ITA": "US aerospace & defence ETF",
    "^VIX": "VIX",
    "CHF=X": "Swiss franc per USD",
}

# The nine financial variables of Rigobon-Sack Table 2, mapped onto instruments that
# exist in 2026, plus a global block. Each entry: (column, label, units, group).
#   "pp"  = percentage-point change in a yield or spread
#   "pct" = percent change in a price level
#   "$"   = dollar change in a price level
#   "vol" = index-point change in the VIX
VARIABLES = [
    ("y2",          "Two-year Treasury yield",          "pp",  "US (paper)"),
    ("y10",         "Ten-year Treasury yield",          "pp",  "US (paper)"),
    ("breakeven10", "Break-even inflation (10-year)",   "pp",  "US (paper)"),
    ("spx",         "S&P 500",                          "pct", "US (paper)"),
    ("bbb",         "BBB yield spread",                 "pp",  "US (paper)"),
    ("hy",          "High-yield yield spread",          "pp",  "US (paper)"),
    ("brent",       "Oil price (Brent front-month)",    "$",   "US (paper)"),
    ("gold",        "Gold price",                       "$",   "US (paper)"),
    ("dollar",      "Dollar (broad index)",             "pct", "US (paper)"),
    ("vix",         "VIX",                              "vol", "US (added)"),
    ("stoxx",       "Euro Stoxx 50",                    "pct", "Global"),
    ("nikkei",      "Nikkei 225",                       "pct", "Global"),
    ("ta125",       "Tel Aviv 125",                     "pct", "Global"),
    ("em",          "MSCI EM equities",                 "pct", "Global"),
    ("chf",         "Swiss franc per dollar",           "pct", "Global"),
    ("energy",      "US energy equities (XLE)",         "pct", "Sector"),
    ("airlines",    "US airlines (JETS)",               "pct", "Sector"),
    ("defence",     "Aerospace & defence (ITA)",        "pct", "Sector"),
]

VAR_LABELS = {c: lab for c, lab, _, _ in VARIABLES}
VAR_UNITS = {c: u for c, _, u, _ in VARIABLES}
VAR_GROUP = {c: g for c, _, _, g in VARIABLES}

# Normalisation for the reported coefficients. The paper scales every estimate to a
# war-risk increase large enough to move the two-year yield by -25bp; here the same
# role is played by a war-risk increase large enough to raise Brent by $5 a barrel.
NORMALISATION = 5.0
NORMALISATION_LABEL = "a war-risk increase that raises Brent $5/bbl"
PAPER_NORMALISATION = -0.25
PAPER_NORMALISATION_LABEL = "a war-risk increase that moves the 2-year yield -25bp"

# ---------------------------------------------------------------- H/L day selection
N_HIGH_DAYS = 18           # top decile of ~180 trading days; the paper used 17 of 47
QUIET_QUANTILE = 0.50      # comparison days must sit in the quiet half of the
                           # war-news score distribution (see event_days.pick_low_days)
BASELINE_WINDOW = 10       # trading days in the trailing baseline for "abnormal" news
ROBUSTNESS_N = [12, 15, 18, 24, 30]   # alternative H-set sizes (Rigobon 2003, sec. IV)
