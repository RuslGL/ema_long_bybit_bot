import asyncio
import hashlib
import hmac
import json
import math
import os
import requests
import time

import aiohttp
# from dotenv import load_dotenv


"""
SETTINGS
"""


IF_TEST = 1

MAIN_URL = None

MAIN_TEST = 'https://api-testnet.bybit.com'
MAIN_REAl = 'https://api.bybit.com'


if IF_TEST:

    MAIN_URL = MAIN_TEST
    API_KEY = str(os.getenv('test_01_bybit_api_key'))
    SECRET_KEY = str(os.getenv('test_01_bybit_secret_key'))

else:
    API_KEY = str(os.getenv('bybit_api_key'))
    SECRET_KEY = str(os.getenv('bybit_secret_key'))

    MAIN_URL = MAIN_REAl


ENDPOINTS_BYBIT = {
        # trade
        'place_order': '/v5/order/create',

        # market
        'server_time': '/v5/market/time',
        'get_kline': '/v5/market/kline',
        'instruments-info': '/v5/market/instruments-info',
        'get_tickers': '/v5/market/tickers',

        # account
        'wallet-balance': '/v5/account/wallet-balance'
}

"""
Functions for regular requests
"""

# SERVICE FUNCTIONS


def gen_signature_get(params, timestamp):
    """
    Returns signature for get request
    """
    param_str = timestamp + API_KEY + '5000' + '&'.join(
        [f'{k}={v}' for k, v in params.items()])
    signature = hmac.new(
        bytes(SECRET_KEY, "utf-8"), param_str.encode("utf-8"), hashlib.sha256
        ).hexdigest()
    return signature


def gen_signature_post(params, timestamp):
    param_str = timestamp + API_KEY + '5000' + json.dumps(params)
    signature = hmac.new(
        bytes(SECRET_KEY, "utf-8"), param_str.encode("utf-8"), hashlib.sha256
        ).hexdigest()
    return signature


def round_price_by_coin_params(price, coin_params):
    """
    Returns rounded quantity
    requires:
    1. price to round
    2. coin params in format given by get_instruments_info
    {'symbol': 'BTCUSDT', 'base_coin_prec': '0.000001',
    'price_tick': '0.01', 'minOrderQty': '0.000048'}
    """
    price_tick = float(coin_params.get('price_tick'))
    precision = int(math.log10(1 / price_tick))
    factor = 10 ** precision
    return int(price * factor) / factor


def round_quantity_by_coin_params(quantity, coin_params):
    """
    Returns rounded quantity
    requires:
    1. price to round
    2. coin params in format given by get_instruments_info
    {'symbol': 'BTCUSDT', 'base_coin_prec': '0.000001',
    'price_tick': '0.01', 'minOrderQty': '0.000048'}
    """
    quote_coin_prec = float(coin_params.get('base_coin_prec'))
    precision = int(math.log10(1 / quote_coin_prec))
    factor = 10 ** precision
    return int(quantity * factor) / factor


# TRADE ORDERS

def place_market_order(symbol, side, quantity, category='spot'):
    """
    Creates matket order
    Requires:
    symbol in format "BTCUSDT", quantity and
    side Buy, Sell
    By  default on spot, available spot, linear, inverse, option
    """

    params = {
        'orderType': 'Market',
        'category': category,
        'symbol': symbol,
        'side': side,
        'marketUnit': 'baseCoin',
        'qty': str(quantity),
    }

    url = MAIN_URL + ENDPOINTS_BYBIT.get('place_order')
    timestamp = str(int(time.time() * 1000))

    header = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": "5000"
    }

    header["X-BAPI-SIGN"] = gen_signature_post(params, timestamp)
    return requests.post(
        url=url, headers=header, data=json.dumps(params)).json()


# SIMPLE MARKET REQUESTS

def get_klines(category='spot', symbol='BTCUSDT', interval=60, limit=10):
    """
    Returns last klines from market
    On default:
    category = 'spot', also available spot,linear,inverse
    symbol = 'BTCUSDT'
    interval = 60, , also available  # 1,3,5,15,30,60,120,240,360,720,D,M,W
    limit = 10  # , also available[1, 1000]
    """
    url = MAIN_URL + ENDPOINTS_BYBIT.get('get_kline')

    params = {
        'category': category,
        'symbol': symbol,
        'interval': interval,
        'limit': limit,
    }

    response = requests.get(url, params=params)
    # print(response.url)
    return response.json().get('result')  # .get('list')


def get_instruments_info(category='spot', symbol='BTCUSDT'):
    """
    Returns info on pair(s) from market
    On default:
    category = 'spot', also linear, inverse, option, spot
    symbol = 'BTCUSDT', not mandatory
    Retunrs result as
    {'symbol': 'BTCUSDT', 'base_coin_prec': '0.000001',
    'price_tick': '0.01', 'minOrderQty': '0.000048'}
    """
    url = MAIN_URL + ENDPOINTS_BYBIT.get('instruments-info')

    params = {
        'category': category,
        'symbol': symbol,
    }

    response = requests.get(url, params=params)
    print(response.url)
    result = response.json().get('result').get('list')[0]
    # print(result)
    dic = {
        'symbol': result.get('symbol'),
        'base_coin_prec': float(
            result.get('lotSizeFilter').get('basePrecision')),
        'price_tick': float(result.get('priceFilter').get('tickSize')),
        'minOrderQty': float(result.get('lotSizeFilter').get('minOrderQty')),
    }
    return dic


def get_pair_price(symbol, category='spot'):
    """
    Returns last price on given pair
    By default spot market
    """
    url = MAIN_URL + ENDPOINTS_BYBIT.get('get_tickers')

    params = {
        'category': category,
        'symbol': symbol
    }

    result = requests.get(url=url, params=params).json().get(
        'result').get('list')[0].get('lastPrice')
    return result


# ASYNCIO MARKET REQUESTS
async def get_klines_asc(category='spot', symbol='BTCUSDT',
                         interval=60, limit=10):
    """
    Returns last klines from market
    On default:
    category = 'spot', also available spot,linear,inverse
    symbol = 'BTCUSDT'
    interval = 60, , also available  # 1,3,5,15,30,60,120,240,360,720,D,M,W
    limit = 10  # , also available[1, 1000]
    """
    url = MAIN_URL + ENDPOINTS_BYBIT.get('get_kline')

    params = {
        'category': category,
        'symbol': symbol,
        'interval': interval,
        'limit': limit,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            return await response.json()


async def get_instruments_info_asc(category='spot', symbol='BTCUSDT'):
    """
    Returns info on pair(s) from market
    On default:
    category = 'spot', also linear, inverse, option, spot
    symbol = 'BTCUSDT', not mandatory
    Retunrs result as
    {'symbol': 'BTCUSDT', 'base_coin_prec': '0.000001',
    'price_tick': '0.01', 'minOrderQty': '0.000048'}
    """
    url = MAIN_URL + ENDPOINTS_BYBIT.get('instruments-info')

    params = {
        'category': category,
        'symbol': symbol,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()

    result = data.get('result').get('list')[0]
    # print(result)
    dic = {
        'symbol': result.get('symbol'),
        'base_coin_prec': float(
            result.get('lotSizeFilter').get('basePrecision')),
        'price_tick': float(result.get('priceFilter').get('tickSize')),
        'minOrderQty': float(result.get('lotSizeFilter').get('minOrderQty')),
    }
    return dic


async def get_pair_price_asc(symbol='BTCUSDT', category='spot'):
    """
    Returns last price on given pair
    By default spot market
    """
    url = MAIN_URL + ENDPOINTS_BYBIT.get('get_tickers')

    params = {
        'category': category,
        'symbol': symbol
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()

    result = data.get(
        'result').get('list')[0].get('lastPrice')
    return result


# SIMPLE ACCOUNT REQUESTS

def get_wallet_balance(coin=None, accountType='UNIFIED'):
    """
    Returns wallet balane
    If coin provided in agruments, returns balancve on given coin
    """
    url = MAIN_URL + ENDPOINTS_BYBIT.get('wallet-balance')

    timestamp = str(int(time.time() * 1000))

    headers = {
        'X-BAPI-API-KEY': API_KEY,
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-RECV-WINDOW': '5000'
    }

    params = {
        'accountType': accountType,
    }

    if coin:
        params['coin'] = coin

    headers['X-BAPI-SIGN'] = gen_signature_get(params, timestamp)
    response = requests.get(url, headers=headers, params=params)

    return response.json().get('result').get(
        'list')[0].get('coin')[0].get('walletBalance')


def get_pair_budget(base_coin, symbol):
    """
    Returns total budget on given pair
    Request: get_pair_budget(base_coin='BTC', symbol='BTCUSDT')
    Result: {'total_budget': 993.523590982, 'budget_usdt': '991.38534782',
    'quantity_base_coin': '0.00004873', 'price_base_coin': '43879.4'}
    """

    quantity_base_coin = get_wallet_balance(coin=base_coin)
    budget_usdt = get_wallet_balance(coin='USDT')
    price_base_coin = get_pair_price(symbol=symbol)

    total_budget = float(budget_usdt) + float(
        quantity_base_coin) * float(price_base_coin)
    budget_usdt

    result = {
        'total_budget': total_budget,
        'budget_usdt': float(budget_usdt),
        'quantity_base_coin': float(quantity_base_coin),
        'price_base_coin': float(price_base_coin),
    }

    return result


# ASYNCIO ACCOUNT REQUESTS


async def get_wallet_balance_asc(coin=None, accountType='UNIFIED'):
    """
    Returns wallet balane
    If coin provided in agruments, returns balancve on given coin
    """
    url = MAIN_URL + ENDPOINTS_BYBIT.get('wallet-balance')

    timestamp = str(int(time.time() * 1000))

    headers = {
        'X-BAPI-API-KEY': API_KEY,
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-RECV-WINDOW': '5000'
    }

    params = {
        'accountType': accountType,
    }

    if coin:
        params['coin'] = coin

    headers['X-BAPI-SIGN'] = gen_signature_get(params, timestamp)

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url, headers=headers, params=params) as response:
            data = await response.json()

    return data.get('result').get(
        'list')[0].get('coin')[0].get('walletBalance')


async def get_pair_budget_asc(base_coin, symbol):
    """
    Returns total budget on given pair
    Request: get_pair_budget(base_coin='BTC', symbol='BTCUSDT')
    Result: {'total_budget': 993.523590982, 'budget_usdt': '991.38534782',
    'quantity_base_coin': '0.00004873', 'price_base_coin': '43879.4'}
    """

    my_requests = [asyncio.create_task(get_wallet_balance_asc(coin=base_coin)),
                   asyncio.create_task(get_wallet_balance_asc(coin='USDT')),
                   asyncio.create_task(get_pair_price_asc(symbol=symbol)),]
    result = await asyncio.gather(*my_requests)

    quantity_base_coin = result[0]
    budget_usdt = result[1]
    price_base_coin = result[2]

    total_budget = float(budget_usdt) + float(
        quantity_base_coin) * float(price_base_coin)
    budget_usdt

    result = {
        'total_budget': total_budget,
        'budget_usdt': float(budget_usdt),
        'quantity_base_coin': float(quantity_base_coin),
        'price_base_coin': float(price_base_coin),
    }

    return result


"""
TEST ZONE
"""

if __name__ == '__main__':

    SYMBOL = 'BTCUSDT'
    BASE_COIN = 'BTC'
    KLINE_INTERVAL = 1
    RISK_TOLERANCE = 0.75
    STOP_LOSS_LIMIT = 0.15
    KLINES_LENGTH = 100

    async def get_variables():
        my_requests = [asyncio.create_task(
                           get_pair_budget_asc(BASE_COIN, SYMBOL)),
                       asyncio.create_task(
                           get_instruments_info_asc(symbol=SYMBOL)),
                       asyncio.create_task(
                           get_klines_asc(symbol=SYMBOL,
                                          interval=KLINE_INTERVAL,
                                          limit=KLINES_LENGTH)),
                       ]
        return await asyncio.gather(*my_requests)

    start_time = time.time()
    result = asyncio.run(get_variables())
    execution_time = time.time() - start_time
    print(f'Execution time with get pair budget = {execution_time}')

    async def get_variables_two():
        my_requests = [asyncio.create_task(
                           get_wallet_balance_asc(coin=BASE_COIN)),
                       asyncio.create_task(
                           get_wallet_balance_asc(coin='USDT')),
                       asyncio.create_task(
                           get_pair_price_asc(symbol=SYMBOL)),

                       asyncio.create_task(
                           get_instruments_info_asc(symbol=SYMBOL)),
                       asyncio.create_task(
                           get_klines_asc(symbol=SYMBOL,
                                          interval=KLINE_INTERVAL,
                                          limit=KLINES_LENGTH)),
                       ]
        return await asyncio.gather(*my_requests)

    start_time = time.time()
    result = asyncio.run(get_variables_two())
    execution_time = time.time() - start_time
    print(f'Execution time without get pair budger = {execution_time}')

    start_time = time.time()
    budget = get_pair_budget(BASE_COIN, SYMBOL)
    symbol_params = get_instruments_info(symbol=SYMBOL)
    raw_klines_store = get_klines(symbol=SYMBOL,
                                  interval=KLINE_INTERVAL, limit=KLINES_LENGTH)
    execution_time = time.time() - start_time
    print(f'Execution time without async = {execution_time}')
