import pandas as pd

ema_short = 5
ema_long = 15

df = pd.read_csv('last_klines.csv', index_col='time', parse_dates=True)

df['EMA_short'] = df['close'].ewm(span=ema_short, min_periods=0, adjust=False).mean()
df['EMA_long'] = df['close'].ewm(span=ema_long, min_periods=0, adjust=False).mean()
df['long_minus_short'] = df['EMA_long'] - df['EMA_short']
print(df)