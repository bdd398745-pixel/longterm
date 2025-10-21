import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.signal_logic import generate_signals

# Streamlit App
st.title("📈 Multi-Timeframe Investment & Trading Signal Dashboard")

# Sidebar inputs
ticker = st.sidebar.text_input("Ticker", value="AAPL", help="Enter stock symbol (e.g., AAPL, RELIANCE.NS)")

interval = st.sidebar.selectbox(
    "Select Timeframe",
    ["1m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo"],
    index=6
)

if interval in ["1m", "5m", "15m", "30m", "60m"]:
    period = st.sidebar.selectbox("Data Period", ["1d", "5d", "1mo"], index=1)
else:
    period = st.sidebar.selectbox("Data Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"], index=3)

params = {
    "atr_period": st.sidebar.number_input("ATR Period", min_value=1, value=14),
    "st_period": st.sidebar.number_input("Supertrend Period", min_value=1, value=10),
    "st_multiplier": st.sidebar.number_input("Supertrend Multiplier", min_value=1.0, value=3.0),
    "rsi_period": st.sidebar.number_input("RSI Period", min_value=1, value=14)
}

# Download data
st.write(f"📊 Fetching **{ticker}** data for `{period}` and `{interval}`...")
df = yf.download(ticker, period=period, interval=interval, progress=False)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

if df.empty:
    st.error("No data found. Try another stock, period, or interval.")
else:
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)

    # Moving Averages
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()

    # RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=params["rsi_period"]).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=params["rsi_period"]).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Supertrend signals
    analyzed_df, signals_df = generate_signals(df, params)
    analyzed_df['MA50'] = df['MA50']
    analyzed_df['MA200'] = df['MA200']
    analyzed_df['RSI'] = df['RSI']

    # --- 📊 Signal Summary Panel ---
    latest = analyzed_df.iloc[-1]
    price = latest['Close']
    ma50 = latest['MA50']
    ma200 = latest['MA200']
    rsi = latest['RSI']
    st_value = latest['Supertrend']

    # Determine trend strength
    if ma50 > ma200:
        trend = "Bullish"
    elif ma50 < ma200:
        trend = "Bearish"
    else:
        trend = "Sideways"

    # RSI-based momentum
    if rsi > 70:
        momentum = "Overbought"
    elif rsi < 30:
        momentum = "Oversold"
    else:
        momentum = "Neutral"

    # Supertrend position
    if price > st_value:
        supertrend_signal = "Buy Zone"
    else:
        supertrend_signal = "Sell Zone"

    # Combine all for Action
    if trend == "Bullish" and supertrend_signal == "Buy Zone" and momentum in ["Neutral", "Oversold"]:
        action = "Buy / Hold"
        color = "green"
    elif trend == "Bearish" and supertrend_signal == "Sell Zone" and momentum != "Oversold":
        action = "Sell / Avoid"
        color = "red"
    else:
        action = "Wait / Neutral"
        color = "orange"

    # Display summary in colored box
    st.markdown(f"""
    <div style='background-color:#f8f9fa;border-left:6px solid {color};padding:12px;border-radius:10px;margin-top:10px;'>
    <h4 style='margin:0;'>📊 <b>Signal Summary</b></h4>
    <p style='margin:5px 0;'>💹 <b>Trend:</b> {trend}</p>
    <p style='margin:5px 0;'>⚡ <b>Momentum (RSI):</b> {momentum} ({rsi:.2f})</p>
    <p style='margin:5px 0;'>🧭 <b>Supertrend:</b> {supertrend_signal}</p>
    <p style='margin:5px 0;'><b>🎯 Suggested Action:</b> <span style='color:{color};font-weight:bold;'>{action}</span></p>
    </div>
    """, unsafe_allow_html=True)

    # --- 📈 Chart with RSI ---
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75, 0.25],
                        vertical_spacing=0.05,
                        subplot_titles=(f"{ticker} Price Chart", "RSI Indicator"))

    fig.add_trace(go.Candlestick(
        x=analyzed_df.index,
        open=analyzed_df['Open'],
        high=analyzed_df['High'],
        low=analyzed_df['Low'],
        close=analyzed_df['Close'],
        name="Candlestick"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=analyzed_df.index, y=analyzed_df['MA50'], line=dict(color='orange', width=1.5), name='MA 50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=analyzed_df.index, y=analyzed_df['MA200'], line=dict(color='green', width=1.5), name='MA 200'), row=1, col=1)
    fig.add_trace(go.Scatter(x=analyzed_df.index, y=analyzed_df['Supertrend'], line=dict(color='blue', width=1), name='Supertrend'), row=1, col=1)

    # RSI plot
    fig.add_trace(go.Scatter(x=analyzed_df.index, y=analyzed_df['RSI'], line=dict(color='purple', width=1.5), name='RSI'), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

    fig.update_layout(
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        title=f"{ticker} - Multi-Timeframe Technical Analysis"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.subheader("📑 Latest Buy/Sell Signals")
    st.dataframe(signals_df, use_container_width=True)
