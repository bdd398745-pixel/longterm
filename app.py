import streamlit as st
from utils.signal_logic import generate_signals, backtest_signals
import yfinance as yf
import pandas as pd

st.title("📈 Intraday Signal & Backtest Dashboard")

ticker = st.text_input("Enter Stock Symbol (e.g., INFY.NS):", "INFY.NS")
interval = st.selectbox("Select Interval", ["1h", "1d"])

if st.button("Generate Signals"):
    df = yf.download(ticker, period="6mo", interval=interval, progress=False)
    df.reset_index(inplace=True)

    signals = generate_signals(df)
    st.subheader("🧭 Signal Summary")
    st.dataframe(signals.tail(10), use_container_width=True)

    # --- Backtest Section ---
    st.subheader("💰 Backtest Results")
    results, win_rate, avg_ret, total = backtest_signals(signals)

    if results.empty:
        st.warning("No completed trades yet.")
    else:
        st.dataframe(results, use_container_width=True)
        st.markdown(f"""
        **📊 Summary:**
        - ✅ Win Rate: `{win_rate}%`
        - 📈 Average Return per Trade: `{avg_ret}%`
        - 💵 Total Cumulative Return: `{total}%`
        - 🔁 Total Trades: `{len(results)}`
        """)
