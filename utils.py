import pandas as pd


def klines_to_df(raw_klines_store):
    """
    Gets list of lists as input
    Returns sorted dataframe
    """
    df_klines_store = pd.DataFrame(
        raw_klines_store, columns=['time', 'open', 'high',
                                   'low', 'close', 'volume', 'turnover']
                                   ).astype(float)

    df_klines_store['time'] = pd.to_datetime(
        df_klines_store['time'], unit='ms')

    df_klines_store = df_klines_store.set_index('time')
    df_klines_store = df_klines_store.sort_index(ascending=True)
    return df_klines_store


def process_new_kline(df_klines_store, new_kline):
    """
    Gets dataframe with historical klines see klines_to_df
    Gets new kline with str values
    Returns dataframe where new kline adde, latest deleted
    """
    new_kline[0] = pd.to_datetime(int(new_kline[0]), unit='ms')
    new_kline[1:] = [float(value) for value in new_kline[1:]]
    df_klines_store.loc[new_kline[0]] = new_kline[1:]
    df_klines_store = df_klines_store.sort_index(ascending=True)
    df_klines_store = df_klines_store.iloc[1:]
    return df_klines_store
