
def define_ema_signal(ema_short, ema_long, input_df, print_result=False):
    """
    Calculates ema logic and returns signals {-1, 0, 1}
    -1 sell, 0 no signal, 1 buy
    if print result: prints dataframe

    """
    df = input_df.copy()
    df['EMA_short'] = df['close'].ewm(
        span=ema_short, min_periods=0, adjust=False).mean()
    df['EMA_long'] = df['close'].ewm(
        span=ema_long, min_periods=0, adjust=False).mean()
    df['short_minus_long'] = df['EMA_short'] - df['EMA_long']
    df['prev_value'] = df['short_minus_long'].shift(1)

    # Define function to calculate signal
    def calculate_signal(row):
        if row['short_minus_long'] > 0 and row['prev_value'] < 0:
            return 1
        elif row['short_minus_long'] < 0 and row['prev_value'] > 0:
            return -1
        else:
            return 0

    # Apply function to each row
    df['signal'] = df.apply(calculate_signal, axis=1)

    if print_result:
        print(df[['short_minus_long', 'prev_value', 'signal']].tail(10))

    return df['signal'].iloc[-1]
