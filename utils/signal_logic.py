import pandas as pd
import numpy as np

def generate_supertrend(df, period=10, multiplier=3):
    """Calculate Supertrend indicator."""
    hl2 = (df['High'] + df['Low']) / 2
    atr = df['High'].combine(df['Low'], max) - df['Low'].combine(df['High'], min)
    atr = atr.rolling(window=period).mean()

    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)

    supertrend = [True] * len(df)

    for i in range(1, len(df)):
        if df['Close'][i] > upperband[i - 1]:
            supertrend[i] = True
        elif df['Close'][i] < lowerband[i - 1]:
            supertrend[i] = False
        else:
            supertrend[i] = supertrend[i - 1]
            if supertrend[i] and lowerband[i] < lowerband[i - 1]:
                lowerband[i] = lowerband[i - 1]
            if not supertrend[i] and upperband[i] > upperband[i - 1]:
                upperband[i] = upperband[i - 1]

    df['Supertrend'] = np.where(supertrend, lowerband, upperband)
    df['In_Uptrend'] = supertrend

    return df


def generate_signals(df, params):
    """Generate buy/sell signals using Supertrend + RSI confirmation."""
    df = df.copy()
    df = generate_supertrend(df, params["st_period"], params["st_multiplier"])

    df['Signal'] = np.nan

    for i in range(1, len(df)):
        if df['In_Uptrend'][i] and not df['In_Uptrend'][i - 1]:
            df.loc[df.index[i], 'Signal'] = 'BUY'
        elif not df['In_Uptrend'][i] and df['In_Uptrend'][i - 1]:
            df.loc[df.index[i], 'Signal'] = 'SELL'

    signals_df = df[['Close', 'Supertrend', 'Signal']].dropna()
    return df, signals_df
