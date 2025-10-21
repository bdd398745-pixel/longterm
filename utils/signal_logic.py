import pandas as pd
import numpy as np
import ta

# --- Enhanced Supertrend Strategy with Filter ---
def generate_signals(df, params):
    atr_period = params.get("atr_period", 10)
    multiplier = params.get("st_multiplier", 3.0)

    df = df.copy()
    df['ATR'] = ta.volatility.average_true_range(
        high=df['High'], low=df['Low'], close=df['Close'], window=atr_period
    )

    hl2 = (df['High'] + df['Low']) / 2
    df['UpperBand'] = hl2 + (multiplier * df['ATR'])
    df['LowerBand'] = hl2 - (multiplier * df['ATR'])

    df['Supertrend'] = np.nan
    trend = True  # True = uptrend

    for i in range(1, len(df)):
        if df['Close'][i] > df['UpperBand'][i-1]:
            trend = True
        elif df['Close'][i] < df['LowerBand'][i-1]:
            trend = False
        df.loc[df.index[i], 'Supertrend'] = (
            df['LowerBand'][i] if trend else df['UpperBand'][i]
        )

    # --- Trend Filter: 20 EMA confirmation ---
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()

    df['Signal'] = np.where(
        (df['Close'] > df['Supertrend']) & (df['Close'] > df['EMA20']), 'BUY',
        np.where((df['Close'] < df['Supertrend']) & (df['Close'] < df['EMA20']), 'SELL', '')
    )

    df = df.dropna(subset=['Supertrend'])
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Date'}, inplace=True)
    return df, df[['Date', 'Close', 'Supertrend', 'Signal']]


# --- Backtest Function ---
def backtest_signals(df):
    trades = []
    buy_price = None
    buy_date = None

    for _, row in df.iterrows():
        if row['Signal'] == 'BUY' and buy_price is None:
            buy_price = row['Close']
            buy_date = row['Date']
        elif row['Signal'] == 'SELL' and buy_price is not None:
            sell_price = row['Close']
            sell_date = row['Date']
            ret = ((sell_price - buy_price) / buy_price) * 100
            trades.append({
                'Buy Date': buy_date,
                'Buy Price': round(buy_price, 2),
                'Sell Date': sell_date,
                'Sell Price': round(sell_price, 2),
                'Return (%)': round(ret, 2)
            })
            buy_price = None

    results = pd.DataFrame(trades)

    if results.empty:
        return pd.DataFrame(), 0, 0, 0

    win_rate = (results['Return (%)'] > 0).sum() / len(results) * 100
    avg_return = results['Return (%)'].mean()
    cumulative = (results['Return (%)'] + 100).prod()/100 - 1

    return results, round(win_rate, 2), round(avg_return, 2), round(cumulative * 100, 2)
