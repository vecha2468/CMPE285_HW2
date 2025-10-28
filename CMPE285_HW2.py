#!/usr/bin/env python3
"""
CMPE285_HW2.py
----------------------------------
Fetches live stock data using the Alpha Vantage API.
Works both locally and on Streamlit Cloud.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import sys
import requests
import os
import pandas as pd

# ✅ Alpha Vantage API key (you can also store it as an environment variable)
ALPHA_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "PM0UVH844BWE9QWF")

# ✅ Optional timezone support
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None
TZ = ZoneInfo("America/Los_Angeles") if ZoneInfo else None


# -----------------------------
# Data structures and exceptions
# -----------------------------
@dataclass
class Quote:
    symbol: str
    company: str
    price: float
    change: float
    percent: float


class QuoteError(Exception):
    """Raised when there’s an issue fetching stock data."""


# -----------------------------
# Helper functions
# -----------------------------
def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format current timestamp nicely."""
    dt = dt or (datetime.now(TZ) if TZ else datetime.now())
    return dt.strftime("%a %b %d %H:%M:%S %Z %Y").strip()


def fetch_alpha_vantage(symbol: str) -> tuple[str, float, float]:
    """Fetch company name, last price, and previous close using Alpha Vantage."""
    try:
        symbol = symbol.upper()
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_KEY}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        quote = data.get("Global Quote", {})
        if not quote:
            raise QuoteError("No valid data returned from Alpha Vantage.")

        company = symbol  # Alpha Vantage doesn’t return full name; symbol as fallback
        last_price = float(quote.get("05. price", 0))
        prev_close = float(quote.get("08. previous close", 0))
        if last_price == 0 or prev_close == 0:
            raise QuoteError("Incomplete data from Alpha Vantage.")
        return company, last_price, prev_close
    except Exception as e:
        raise QuoteError(f"No valid price data found. ({e})")


# -----------------------------
# Main fetch function
# -----------------------------
def fetch_quote(symbol: str) -> Quote:
    """Fetch stock quote using Alpha Vantage API."""
    if not symbol or not symbol.strip():
        raise QuoteError("Stock symbol cannot be empty.")
    symbol = symbol.strip().upper()

    company, last_price, prev_close = fetch_alpha_vantage(symbol)

    change = last_price - prev_close
    percent = (change / prev_close * 100) if prev_close != 0 else 0

    return Quote(
        symbol=symbol,
        company=f"{company} ({symbol})",
        price=round(last_price, 2),
        change=round(change, 2),
        percent=round(percent, 2),
    )


# -----------------------------
# For testing / CLI use
# -----------------------------
def render_quote(q: Quote) -> str:
    """Format quote nicely for display."""
    sign_change = "+" if q.change > 0 else "-" if q.change < 0 else ""
    sign_pct = "+" if q.percent > 0 else "-" if q.percent < 0 else ""
    return (
        f"{format_timestamp()}\n\n"
        f"{q.company}\n\n"
        f"{q.price:.2f} {sign_change}{abs(q.change):.2f} ({sign_pct}{abs(q.percent):.2f}%)\n"
    )


if __name__ == "__main__":
    print("Enter a stock symbol:")
    for line in sys.stdin:
        symbol = line.strip()
        if not symbol:
            print("Goodbye!")
            break
        try:
            q = fetch_quote(symbol)
            print(render_quote(q))
        except QuoteError as e:
            print(f"Error: {e}\n")
        except Exception as e:
            print(f"Unexpected error: {e}\n")
        print("Enter a stock symbol:")
