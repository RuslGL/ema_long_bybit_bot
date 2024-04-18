import os
import requests
import time
import hashlib
import hmac


from dotenv import load_dotenv


load_dotenv()


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
        'server_time': '/v5/market/time',

        # market
        'get_kline': '/v5/market/kline',

        # account
        'wallet-balance': '/v5/account/wallet-balance'
}

"""
Functions for regular requests
"""

# service functions


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


# market requests

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
    return response.json().get('result')  # .get('list')


# account requests

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


"""
Functions for ASYNCIO requests
"""


"""
TEST ZONE
"""
if __name__ == '__main__':
    print(get_wallet_balance(coin='BTC'))
