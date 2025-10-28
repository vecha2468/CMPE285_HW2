#!/usr/bin/env python3
"""
CMPE285_HW2.py
----------------------------------
Backend logic for fetching live stock information using Yahoo Finance (via yfinance).
Optimized for Streamlit Cloud.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import sys
import pandas as pd
import yfinance as yf
import requests_cache

# ✅ Caching session to stabilize yfinance on Streamlit Cloud
session = requests_cache.CachedSession("/tmp/yf_cache", expire_after=3600)
yf.utils.get_yf_session = lambda: session

# ✅ Optional timezone support (safe fallback)
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
    """Raised when there’s an issue fetching the stock quote."""


# -----------------------------
# Helper functions
# -----------------------------
def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format the current timestamp nicely."""
    dt = dt or (datetime.now(TZ) if TZ else datetime.now())
    return dt.strftime("%a %b %d %H:%M:%S %Z %Y").strip()


def _get_name_safe(ticker: yf.Ticker, symbol: str) -> str:
    """Safely extract company name."""
    try:
        info = ticker.get_info()
        return info.get("longName") or info.get("shortName") or symbol.upper()
    except Exception:
        return symbol.upper()


def _get_prices_safe(ticker: yf.Ticker) -> tuple[float, float]:
    """
    Fetch reliable last price and previous close for the ticker.
    Uses cached Yahoo session to avoid throttling issues.
    """
    try:
        # Try 5 days of data to ensure at least 2 valid rows
        hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
        hist = hist.dropna(how="all")
        if hist.empty or "Close" not in hist.columns:
            raise QuoteError("No valid price data found.")

        last_price = float(hist["Close"].iloc[-1])
        if len(hist) >= 2:
            prev_close = float(hist["Close"].iloc[-2])
        else:
            prev_close = float(hist["Open"].iloc[-1])
        return last_price, prev_close

    except Exception as e:
        raise QuoteError(f"No valid price data found. ({e})")


# -----------------------------
# Core function
# -----------------------------
def fetch_quote(symbol: str) -> Quote:
    """Fetch stock quote given a symbol."""
    if not symbol or not symbol.strip():
        raise QuoteError("Stock symbol cannot be empty.")
    symbol = symbol.strip().upper()

    try:
        ticker = yf.Ticker(symbol)
        company_name = _get_name_safe(ticker, symbol)
        last_price, prev_close = _get_prices_safe(ticker)
    except QuoteError as qe:
        raise qe
    except Exception as e:
        raise QuoteError(f"Error retrieving data for {symbol}: {e}")

    change = last_price - prev_close
    percent = (change / prev_close * 100) if prev_close != 0 else 0

    return Quote(
        symbol=symbol,
        company=f"{company_name} ({symbol})",
        price=round(last_price, 2),
        change=round(change, 2),
        percent=round(percent, 2),
    )


# -----------------------------
# Utility for CLI testing
# -----------------------------
def render_quote(q: Quote) -> str:
    """Nicely format the stock quote output."""
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
