import asyncio
from api.bybit_api import (get_instruments_info_asc,
                           get_pair_budget_asc, get_klines_asc)
from api.ws_asyncio import SocketBybit
from utils import klines_to_df, process_new_kline
from signal_strategy import define_ema_signal

import json
import time


# BASE CONSTANT VARIABLES
SYMBOL = 'BTCUSDT'
BASE_COIN = 'BTC'
KLINE_INTERVAL = 1
RISK_TOLERANCE = 0.75
STOP_LOSS_LIMIT = 0.15
KLINES_LENGTH = 10


# PRE START CALCULATIONS
async def get_variables():
    tasks = [asyncio.create_task(get_pair_budget_asc(BASE_COIN, SYMBOL)),
             asyncio.create_task(get_instruments_info_asc(symbol=SYMBOL)),
             asyncio.create_task(get_klines_asc(symbol=SYMBOL,
                                                interval=KLINE_INTERVAL,
                                                limit=KLINES_LENGTH+1)),]
    return await asyncio.gather(*tasks)

result = asyncio.run(get_variables())


budget = result[0]
symbol_params = result[1]
raw_klines_store = result[2].get('result').get('list')


# BUDGET RESTRICTIONS
start_total_budget = budget.get('total_budget')
stop_budget = start_total_budget * RISK_TOLERANCE


# STRATEGY INPUT VARIABLES
ema_short = 5
ema_long = 15


# TRADE VARIABLES
quantity_tick = symbol_params.get('base_coin_prec')
price_tick = symbol_params.get('price_tick')
min_quantity = symbol_params.get('minOrderQty')
df_klines_store = klines_to_df(raw_klines_store)


class TradeSocketBybit(SocketBybit):
    def __init__(selfself, url, params=None):
        super().__init__(url, params)

        global df_klines_store, ema_short, ema_long

    async def on_message(self, ws, msg):
        global df_klines_store
        data = json.loads(msg.data)
        if 'data' in data:
            if data.get('topic') == 'kline.1.BTCUSDT':
                if data.get('data')[0].get('confirm'):
                    data = data.get('data')[0]
                    new_candle = []
                    new_candle.extend([
                        data.get('start'), data.get('open'), data.get('high'),
                        data.get('low'), data.get('close'), data.get('volume'),
                        data.get('turnover')])
                    df_klines_store = process_new_kline(
                        df_klines_store, new_candle)

                    # ### SIGNAL LOGIC STARTS HERE ###
                    start_time = time.time()
                    signal = define_ema_signal(ema_short, ema_long,
                                               df_klines_store,
                                               print_result=True)
                    print(signal)
                    # ### SIGNAL LOGIC STOPS HERE ###

                    # ### TRADE LOGIC STARTS HERE ###
                    if signal == 0:
                        print('No signal')
                    elif signal == 1:
                        print('Buy')
                    else:
                        print('Sell')
                    execution_time = time.time() - start_time
                    print(f'execution time = {execution_time}')

                    # ### TRADE LOGIC STOPS HERE ###


if __name__ == '__main__':

    url_spot = 'wss://stream.bybit.com/v5/public/spot'
    url_futures = 'wss://stream.bybit.com/v5/public/linear'

    topics = [
        f'kline.{KLINE_INTERVAL}.{SYMBOL}',
        f'publicTrade.{SYMBOL}'
    ]

    socket = TradeSocketBybit(url_spot, topics)
    asyncio.run(socket.connect())
