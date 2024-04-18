
import json
import threading
import time
import traceback
import websocket


class Socket_conn_Bybit(websocket.WebSocketApp):
    def __init__(self, url, params=None):
        super().__init__(
            url=url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.params = params
        self.run_forever()

    def send_heartbeat(self, ws):
        while True:
            ws.send(json.dumps({"req_id": "100001", "op": "ping"}))
            time.sleep(20)    		# Пауза между пингами

    def on_open(self, ws):
        print(ws, 'Websocket was opened')

        # Запуск потока heartbeat
        threading.Thread(target=self.send_heartbeat, args=(ws,)).start()

        # Подписка на топики:
        data = {"op": "subscribe", "args": self.params}
        ws.send(json.dumps(data))

    def on_error(self, ws, error):
        print('on_error', ws, error)
        print(traceback.format_exc())

    def on_close(self, ws, status, msg):
        print('on_close', ws, status, msg)

    def on_message(self, ws, msg):
        # print('on_message', ws, msg)
        data = json.loads(msg)
        print(data)
        # time.sleep(20)


if __name__ == '__main__':

    url_spot = 'wss://stream.bybit.com/v5/public/spot'
    url_futures = 'wss://stream.bybit.com/v5/public/linear'

    topik = [
        'kline.60.BTCUSDT',
        # 'orderbook.1.AXSUSDT',

    ]

    threading.Thread(target=Socket_conn_Bybit, args=(url_spot, topik)).start()
