#!/usr/bin/env python3
"""
stock_quote.py
----------------------------------
A small CLI tool to fetch live stock info (company name, price, change, % change)
using Yahoo Finance via the `yfinance` library.

Example:
    Please enter a symbol:
    ADBE

Output:
    Mon Oct 10 17:23:48 PDT 2016

    Adobe Systems Incorporated (ADBE)

    109.24 +0.60 (+0.55%)

Features:
- No API key required
- Handles invalid symbols and network errors gracefully
- Runs fully in terminal or PyCharm console
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import sys
import yfinance as yf
import pandas as pd

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


# Set timezone (Pacific Time)
TZ = ZoneInfo("America/Los_Angeles") if ZoneInfo else None


@dataclass
class Quote:
    symbol: str
    company: str
    price: float
    change: float
    percent: float


class QuoteError(Exception):
    """Custom exception for quote retrieval errors."""


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format timestamp like: Mon Oct 10 17:23:48 PDT 2016"""
    dt = dt or (datetime.now(TZ) if TZ else datetime.now())
    return dt.strftime("%a %b %d %H:%M:%S %Z %Y").strip()


def _get_name_safe(ticker: yf.Ticker, symbol: str) -> str:
    """Safely get company name."""
    try:
        info = ticker.get_info()
        return info.get("longName") or info.get("shortName") or symbol.upper()
    except Exception:
        return symbol.upper()


def _get_prices_safe(ticker: yf.Ticker) -> tuple[float, float]:
    """Return (last_price, previous_close) safely."""
    try:
        fi = ticker.fast_info
        last_price = float(fi.get("last_price"))
        prev_close = float(fi.get("previous_close"))
        if pd.notna(last_price) and pd.notna(prev_close):
            return last_price, prev_close
    except Exception:
        pass

    # Fallback to historical data
    hist = ticker.history(period="5d", interval="1d")
    if hist.empty or "Close" not in hist.columns:
        raise QuoteError("No valid price data found.")
    last_price = float(hist["Close"].iloc[-1])
    prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else last_price
    return last_price, prev_close


def fetch_quote(symbol: str) -> Quote:
    """Main function to fetch and return a stock quote."""
    if not symbol.strip():
        raise QuoteError("Symbol cannot be empty.")
    symbol = symbol.strip().upper()

    try:
        ticker = yf.Ticker(symbol)
        company_name = _get_name_safe(ticker, symbol)
        last_price, prev_close = _get_prices_safe(ticker)
    except Exception as e:
        raise QuoteError(f"Unable to retrieve data: {e}")

    change = last_price - prev_close
    percent = (change / prev_close) * 100 if prev_close != 0 else 0
    return Quote(
        symbol=symbol,
        company=f"{company_name} ({symbol})",
        price=round(last_price, 2),
        change=round(change, 2),
        percent=round(percent, 2)
    )


def render_quote(q: Quote) -> str:
    """Pretty-print a quote object."""
    sign_change = "+" if q.change > 0 else "-" if q.change < 0 else ""
    sign_pct = "+" if q.percent > 0 else "-" if q.percent < 0 else ""
    return (
        f"{format_timestamp()}\n\n"
        f"{q.company}\n\n"
        f"{q.price:.2f} {sign_change}{abs(q.change):.2f} ({sign_pct}{abs(q.percent):.2f}%)\n"
    )


def main():
    print("Please enter a symbol:")
    try:
        for line in sys.stdin:
            symbol = line.strip()
            if not symbol:
                print("Goodbye!")
                break
            try:
                q = fetch_quote(symbol)
                print(render_quote(q))
            except QuoteError as qe:
                print(f"Error: {qe}\n")
            except Exception as e:
                print(f"Unexpected error: {e}\n")
            finally:
                print("Please enter a symbol:")
    except KeyboardInterrupt:
        print("\nInterrupted by user.")


if __name__ == "__main__":
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
