import pandas as pd

from decimal import Decimal, ROUND_DOWN


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
    # length -1 here if you need 500 klines KLINES_LENGTH = 501
    df_klines_store = df_klines_store.iloc[1:]
    return df_klines_store


#def calculate_purchase_volume(sum_amount, price, min_volume, tick):
#    """
#    Calculates trade volume based on the market price
#    and rounds it to tick size
#    returns -1 if quantity les than min quantity
#    else returns trade quantity 
#    """
#    volume = sum_amount / price
#    if volume < min_volume:
#        return -1
#    return (volume // tick) * tick

def calculate_purchase_volume(sum_amount, price, min_volume, tick):
    """
    Calculates trade volume based on the market price
    and rounds it to tick size.
    Returns -1 if quantity is less than min quantity,
    else returns trade quantity.
    """
    # Convert inputs to Decimal for accurate calculations
    sum_amount = Decimal(str(sum_amount))
    price = Decimal(str(price))
    min_volume = Decimal(str(min_volume))
    tick = Decimal(str(tick))
    
    # Calculate volume
    volume = sum_amount / price
    
    # Check if volume is less than minimum volume
    if volume < min_volume:
        return -1
    
    # Round volume down to the nearest tick size
    rounded_volume = (volume // tick) * tick
    
    # Quantize the result to match the tick size
    rounded_volume = rounded_volume.quantize(tick, rounding=ROUND_DOWN)
    
    return float(rounded_volume)


def round_base_coin_volume(coin_amount, min_volume, tick):
    """
    Calculates trade volume of base_coin and rounds it to tick size
    returns -1 if quantity is less than min quantity
    else returns trade quantity 
    """
    coin_amount = Decimal(str(coin_amount))
    min_volume = Decimal(str(min_volume))
    tick = Decimal(str(tick))
    
    if coin_amount < min_volume:
        return -1
    rounded_amount = (coin_amount // tick) * tick
    rounded_amount = rounded_amount.quantize(tick, rounding=ROUND_DOWN)
    return float(rounded_amount)


#def round_price(price, price_tick):
#    """
#    Calculates price rounded to floor by price_tick 
#    """
#
#    return (price // price_tick) * price_tick

def round_price(price, price_tick):
    """
    Calculates price rounded to floor by price_tick.
    """
    # Convert inputs to Decimal for accurate calculations
    price = Decimal(str(price))
    price_tick = Decimal(str(price_tick))
    
    # Round price down to the nearest tick size
    rounded_price = (price // price_tick) * price_tick
    
    # Quantize the result to match the tick size
    rounded_price = rounded_price.quantize(price_tick, rounding=ROUND_DOWN)
    
    return float(rounded_price)
