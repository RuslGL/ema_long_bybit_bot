import json
import asyncio
# import threading

from api.ws_asyncio import Socket_conn_Bybit
from api.bybit_api import get_klines

Pers2018

class SignalSocket(Socket_conn_Bybit):
    def __init__(self, url, topics, symbol, interval, limit, *args):
        super().__init__(url, topics, *args)
        self.symbol = symbol
        self.interval = interval
        self.limit = limit
        self.last_price = None
        self.last_closed_kline = None

        # change to async
        self.prev_klines = get_klines(
            symbol=self.symbol, interval=self.interval, limit=self.limit
            ).get('list')
        print(*self.prev_klines, sep='\n')

    async def on_message(self, ws, msg):
        data = json.loads(msg.data)
        if 'data' in data:
            data = data.get('data')
            if 'lastPrice' in data:
                self.last_price = data.get('lastPrice')
                print(self.last_price)
            elif data[0].get('confirm'):
                self.last_closed_kline = data[0]
                print(self.last_closed_kline)


if __name__ == '__main__':

    url_spot = 'wss://stream.bybit.com/v5/public/spot'
    url_futures = 'wss://stream.bybit.com/v5/public/linear'

    symbol = 'BTCUSDT'
    interval = '1'  # 1 3 5 15 30 60 120 240 360 720 (min) D (day) W (week) M (month)
    limit = 5

    topics = [
        f'kline.{interval}.{symbol}',
        f'tickers.{symbol}'
    ]

    socket = SignalSocket(url_spot, topics, symbol, interval, limit)
    asyncio.run(socket.connect())
