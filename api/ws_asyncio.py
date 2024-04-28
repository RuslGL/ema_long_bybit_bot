import json
import asyncio
import traceback
import aiohttp


class SocketBybit():

    def __init__(self, url, params=None):
        self.url = url
        self.params = params

    async def connect(self):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.url) as ws:
                await self.on_open(ws)
                while True:
                    try:
                        message = await ws.receive()
                        await self.on_message(ws, message)
                    except Exception as e:
                        await self.on_error(ws, e)
                        break

    async def send_heartbeat(self, ws):
        while True:
            try:
                await ws.send_json({"req_id": "100001", "op": "ping"})
                await asyncio.sleep(20)  # Пауза между пингами
            except Exception as e:
                await self.on_error(ws, e)
                break

    async def on_open(self, ws):
        print(ws, 'Websocket was opened')

        # Запуск асинхронного отправления heartbeat
        asyncio.create_task(self.send_heartbeat(ws))

        # Подписка на топики:
        data = {"op": "subscribe", "args": self.params}
        await ws.send_json(data)

    async def on_error(self, ws, error):
        print('on_error', ws, error)
        print(traceback.format_exc())

    async def on_message(self, ws, msg):
        # print('on_message', ws, msg.data)
        data = json.loads(msg.data)
        print(data)
        # await asyncio.sleep(20)


if __name__ == '__main__':

    url_spot = 'wss://stream.bybit.com/v5/public/spot'
    url_futures = 'wss://stream.bybit.com/v5/public/linear'

    topics = [
        'kline.60.BTCUSDT',
        'orderbook.1.AXSUSDT',
    ]

    socket = SocketBybit(url_spot, topics)
    asyncio.run(socket.connect())
