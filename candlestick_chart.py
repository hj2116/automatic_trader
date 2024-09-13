import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
import threading
import websocket
import json
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates


class CandlestickChart:
    def __init__(self, parent_window):
        self.root = parent_window  
        self.price_data = []
        self.buy_markers = []  
        self.sell_markers = []  

        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.chart_frame = None

    def create_chart_frame(self, parent_frame):
        self.chart_frame = parent_frame

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    def start_candlestick_stream(self):
        socket = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"  

        def on_message(ws, message):
            try:
                data = json.loads(message)
                kline = data['k']  

                if kline and kline['x']:
                    candle = {
                        'time': pd.to_datetime(kline['t'], unit='ms'),
                        'open': float(kline['o']),
                        'high': float(kline['h']),
                        'low': float(kline['l']),
                        'close': float(kline['c']),
                        'volume': float(kline['v'])
                    }
                    self.price_data.append(candle)

                    if len(self.price_data) > 100:
                        self.price_data.pop(0)

                    self.update_candlestick_chart()

            except Exception as e:
                print(f"WebSocket Error: {e}")

        def on_error(ws, error):
            print(f"WebSocket Error: {error}")

        def on_close(ws):
            print("WebSocket closed")

        def on_open(ws):
            print("WebSocket connection opened")

        self.ws = websocket.WebSocketApp(socket, on_message=on_message, on_error=on_error, on_close=on_close)
        self.ws.on_open = on_open

        self.socket_thread = threading.Thread(target=self.ws.run_forever)
        self.socket_thread.start()

    def update_candlestick_chart(self):
        if len(self.price_data) == 0:
            return 

        df = pd.DataFrame(self.price_data)

        df.set_index('time', inplace=True)

        self.ax.clear()

        mpf.plot(df, type='candle', ax=self.ax, style='charles', volume=False)

        self.plot_trade_markers()

        self.canvas.draw()

    def mark_trade_action(self, price, action, timestamp):
        if action == "Buy":
            self.buy_markers.append((timestamp, price))
        elif action == "Sell":
            self.sell_markers.append((timestamp, price))

    def plot_trade_markers(self):
        for timestamp, price in self.buy_markers:
            self.ax.plot(mdates.date2num(timestamp), price, marker="^", color="green", markersize=10)

        for timestamp, price in self.sell_markers:
            self.ax.plot(mdates.date2num(timestamp), price, marker="v", color="red", markersize=10)

    def stop_stream(self):
        if self.ws:
            self.ws.close()