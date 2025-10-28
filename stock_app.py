# stock_app.py
"""
Streamlit Web App — Stock Price Viewer
--------------------------------------
Displays live stock data using Yahoo Finance (via yfinance).
"""

import streamlit as st
from CMPE285_HW2 import fetch_quote, QuoteError

st.set_page_config(page_title="Stock Price Viewer", page_icon="📈", layout="centered")

# --- App title ---
st.title("📈 Stock Price Viewer")

st.write("Type a stock ticker (e.g. **AAPL**, **MSFT**, **ADBE**) to see live price info.")

symbol = st.text_input("Enter Stock Symbol:")

if symbol:
    try:
        q = fetch_quote(symbol)
        st.success(f"**{q.company}**")

        col1, col2, col3 = st.columns(3)
        col1.metric("Price", f"${q.price:.2f}")
        col2.metric("Change", f"{q.change:+.2f}")
        col3.metric("Percent", f"{q.percent:+.2f}%")

        st.caption("Data provided by Yahoo Finance (via yfinance).")

    except QuoteError as e:
        st.error(f"⚠️ {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
else:
    st.info("Enter a symbol above to get started.")
