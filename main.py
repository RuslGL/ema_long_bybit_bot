from api.bybit_api import get_wallet_balance, get_klines


# functions test
# result = get_wallet_balance('USDT')
a = get_wallet_balance
b = get_klines

result = a()
print(result)
