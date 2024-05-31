import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from api.bybit_api import (get_instruments_info_asc,
                           get_pair_budget_asc, get_klines_asc,
                           place_market_order_sell_spot,
                           place_market_order_buy_spot,
                           # place_conditional_order_buy_spot,
                           place_conditional_order_sell_spot,
                           cancel_spot_order, get_open_spot_orders)

from api.bybit_api import WS_SPOT

from api.ws_asyncio import SocketBybit
from utils import (klines_to_df, process_new_kline, calculate_purchase_volume,
                   round_price, round_base_coin_volume)
from signal_strategy import define_ema_signal

import json
from aiohttp.client_exceptions import ClientConnectorError

from dotenv import load_dotenv

load_dotenv()

# TELEGRAM BOT VARIABLES
bot_token = str(os.getenv('token_Test_algo_one_bot'))
chat_id = str(os.getenv('chat_id'))
dp = Dispatcher()

# BASE CONSTANT VARIABLES
SYMBOL = 'BTCUSDT'
BASE_COIN = 'BTC'
KLINE_INTERVAL = 1
RISK_TOLERANCE = 0.75
STOP_LOSS_LIMIT = 0.95
TAKE_PROFIT_RANGE = 1.05
KLINES_LENGTH = 500
IF_TAKE_PROFIT = 0


# PRE START CALCULATIONS
async def get_variables():
    tasks = [asyncio.create_task(get_pair_budget_asc(BASE_COIN, SYMBOL)),
             asyncio.create_task(get_instruments_info_asc(symbol=SYMBOL)),
             asyncio.create_task(get_klines_asc(symbol=SYMBOL,
                                                interval=KLINE_INTERVAL,
                                                limit=KLINES_LENGTH+1)),]
    return await asyncio.gather(*tasks)
try:
    result = asyncio.run(get_variables())

    budget = result[0].get('total_budget')
    symbol_params = result[1]
    raw_klines_store = result[2].get('result').get('list')

    # BUDGET RESTRICTIONS
    start_total_budget = budget
    stop_budget = start_total_budget * RISK_TOLERANCE

    # STRATEGY INPUT VARIABLES
    ema_short = 5
    ema_long = 190

    # TRADE VARIABLES
    quantity_tick = symbol_params.get('base_coin_prec')
    price_tick = symbol_params.get('price_tick')
    min_quantity = symbol_params.get('minOrderQty')
    df_klines_store = klines_to_df(raw_klines_store)
    in_position = 0
    last_price = None
    tp_sl_list = []


except Exception as e:
    print('Проблемы с получением первичных переменных от api', e)


class TradeSocketBybit(SocketBybit):
    def __init__(self, url, params=None):
        super().__init__(url, params)
        self.message_queue = asyncio.Queue()
        self.bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        self.dispatcher = Dispatcher()
        asyncio.create_task(self.start_bot())
        asyncio.create_task(self.process_message_queue())

    async def start_bot(self):
        """
        Запускает Telegram-бота
        """
        await self.dispatcher.start_polling(self.bot)

    async def process_message_queue(self):
        """
        Обрабатывает очередь сообщений и отправляет их в Telegram
        """
        while True:
            chat_id, text = await self.message_queue.get()
            await self.bot.send_message(chat_id, text)
            self.message_queue.task_done()

    async def send_message(self, chat_id, text):
        """
        Отправляет сообщение в указанный чат через бота.
        """
        await self.message_queue.put((chat_id, str(text)))

    async def on_message(self, ws, msg):

        global df_klines_store, in_position, symbol_params, \
            budget, stop_budget, last_price, min_quantity, \
            quantity_tick, tp_sl_list, ema_short, ema_long

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
                    last_price = float(data.get('close'))

                    # ### SIGNAL LOGIC STARTS HERE ###
                    signal = define_ema_signal(ema_short, ema_long,
                                               df_klines_store,
                                               print_result=True)
                    print(signal)
                    # ### SIGNAL LOGIC STOPS HERE ###

# #############################################################################
            ########################################################
# {'symbol': 'BTCUSDT', 'base_coin_prec': 1e-06, 'price_tick': 0.01,
# 'minOrderQty': 4.8e-05}#

                    # ### TRADE LOGIC STARTS HERE ###

# ####### WHERE QUANTITY -1 - reaction
# ##### tp sl cancellation

                    if signal == 1 and in_position == 0:
                        message = (
                            f'Buy, budget= {budget} stop_budget= {stop_budget}'
                                    )
                        print(message)
                        await self.send_message(chat_id, message)
                        try:
                            result = await get_pair_budget_asc(
                                BASE_COIN, SYMBOL)
                            usdt_budget = result.get('budget_usdt')
                            BTC_budget = result.get('quantity_base_coin')

                            quantity = calculate_purchase_volume(
                                usdt_budget, last_price * 1.05,
                                min_quantity, quantity_tick)
                            print(f'quantity to buy = {quantity}')
                            if quantity == -1:
                                raise Exception('Недостаточный баланс')
                            print('Покупаем')
                            buy_result = await place_market_order_buy_spot(
                                SYMBOL, quantity)
                            print(buy_result)
                            await self.send_message(chat_id, buy_result)
                            if buy_result.get('retMsg') == 'OK':
                                print('place sl')
                                in_position = 1
                                print(f'in_position = {in_position}')
                                sl = round_price(
                                    last_price * STOP_LOSS_LIMIT, price_tick)
                                sl_price = round_price(sl * 0.99, price_tick)
                                # tp = round_price(
                                #   last_price * TAKE_PROFIT_RANGE, price_tick)
                                # tp_price = round_price(tp * 0.99, price_tick)

                                tp_sl = [asyncio.create_task(
                                    place_conditional_order_sell_spot(
                                        symbol=SYMBOL, quantity=quantity,
                                        triggerPrice=sl, price=sl_price)),
                                    #    asyncio.create_task(
                                    # place_conditional_order_sell_spot(
                                    #    symbol=SYMBOL, quantity=quantity,
                                    #    triggerPrice=tp, price=tp_price))
                                        ]

                                tp_sl_result = await asyncio.gather(*tp_sl)
                                tp_sl_list = [
                                    tp_sl_result[0].get(
                                        'result').get('orderId'),
                                    # tp_sl_result[1].get(
                                    #    'result').get('orderId')
                                    ]
                                print(tp_sl_list)
                                await self.send_message(chat_id, tp_sl_list)
                                result = await get_pair_budget_asc(
                                    BASE_COIN, SYMBOL)
                                usdt_budget = result.get('budget_usdt')
                                BTC_budget = result.get('quantity_base_coin')
                                print(f'in_position = {in_position}')
                                print(f'BTC = {BTC_budget}')
                                print(f'USDT = {usdt_budget}')
                            else:
                                message = ('Не удалось разместить \
                                           ордер на Покупку!')
                                print(message)
                                await self.send_message(chat_id, message)

                        except Exception:
                            message = ('Не удалось разместить \
                                        ордер на Покупку!')
                            print(message)
                            await self.send_message(chat_id, message)

                    elif signal == -1 and in_position == 1:
                        message = (f'Sell, budget={budget}',
                                   f'stop_budget= {stop_budget}')
                        print(message)
                        await self.send_message(chat_id, message)

                        try:
                            result = await get_pair_budget_asc(
                                BASE_COIN, SYMBOL)
                            usdt_budget = result.get('budget_usdt')
                            BTC_budget = result.get('quantity_base_coin')

                            quantity = round_base_coin_volume(
                                BTC_budget, min_quantity, quantity_tick)
                            print(f'quantity to sell = {quantity}')
                            if quantity == -1:
                                message = 'Недостаточный баланс'
                                print(message)
                                await self.send_message(chat_id, message)
                                raise Exception(message)
                            print('Продаем')
                            sell_result = await place_market_order_sell_spot(
                                SYMBOL, quantity)
                            print(sell_result)
                            if sell_result.get('retMsg') == 'OK':
                                result = await get_pair_budget_asc(
                                    BASE_COIN, SYMBOL)
                                usdt_budget = result.get('budget_usdt')
                                BTC_budget = result.get('quantity_base_coin')
                                in_position = 0
                                print(f'in_position = {in_position}')
                                print(f'BTC = {BTC_budget}')
                                print(f'USDT = {usdt_budget}')
                                await self.send_message(chat_id, 'Sold')
                                await self.send_message(chat_id, sell_result)
                            else:
                                message = 'Не удалось разместить ордер на продажу!'
                                print(message)
                                await self.send_message(chat_id, message)

                        except Exception:
                            message = 'Не удалось разместить ордер на продажу!'
                            print(message)
                            await self.send_message(chat_id, message)

                        try:
                            print('Отменяем', tp_sl_list)
                            tp_sl_cancelation = [asyncio.create_task(
                                cancel_spot_order(tp_sl_list[0], SYMBOL)),
                                                 asyncio.create_task(
                                cancel_spot_order(tp_sl_list[1], SYMBOL))]
                            tp_sl_cancelation_result = await asyncio.gather(
                                *tp_sl_cancelation)
                            print(tp_sl_cancelation_result)
                            tp_sl_list = []
                        except Exception:
                            print('Не удалось отменить TP_SL')

                    # ## Нет сигналов нет позиций
                    else:
                        result = await get_pair_budget_asc(BASE_COIN, SYMBOL)
                        BTC_budget = result.get('quantity_base_coin')
                        if BTC_budget < min_quantity:
                            in_position = 0
                            orders_list = await get_open_spot_orders(SYMBOL)

                            if len(orders_list) != 0:
                                print('Начинаем удалять ордеры',  orders_list)

                                cancelation_tasks = []
                                for element in orders_list:
                                    cancelation_tasks.append(
                                        asyncio.create_task(
                                            cancel_spot_order(
                                                element, SYMBOL)))

                                try:
                                    await asyncio.gather(*cancelation_tasks)
                                    tp_sl_list = []
                                except Exception:
                                    print('Проблемы с удалением TP/SL')

                        message = (
                            f'No signal, in_position = {in_position},\n tp/sl = {tp_sl_list}')
                        print(message)
                        await self.send_message(chat_id, message)

                    # ### TRADE LOGIC STOPS HERE ###
            # #######################################################
# #############################################################################


topics = [
    f'kline.{KLINE_INTERVAL}.{SYMBOL}',
    f'publicTrade.{SYMBOL}'
    ]


async def run_socket_connection(url, topics):
    while True:
        try:
            ws_connection = TradeSocketBybit(url, topics)
            await ws_connection.connect()
        except ClientConnectorError as e:
            print("WebSocket connection lost. Reconnecting...", e)
            await asyncio.sleep(1)  # Wait before retrying
        except Exception as e:
            print("An unexpected error occurred:", e)
            await asyncio.sleep(1)  # Wait before retrying


async def main():
    await run_socket_connection(WS_SPOT, topics)

if __name__ == '__main__':
    asyncio.run(main())
