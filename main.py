import tkinter as tk
from tkinter import ttk
import threading
import websocket
import json
import time
import pandas as pd
from candlestick_chart import CandlestickChart  
from trading_logic import TradingLogic  


class CryptoTradingBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Trading Bot")
        self.root.geometry("900x900")  

       
        self.root.attributes("-alpha", 0.95)
        self.root.configure(background='#1c1c1c')

     
        self.candlestick_chart = None

      
        self.logic = TradingLogic()  
        self.root.initialbalance = self.logic.simulated_balance

        self.ws = None
        self.trading_active = False

        self.create_styles()

        # Create GUI elements
        self.create_widgets()


        self.logic.fetch_fear_greed_index()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_styles(self):
        self.style = ttk.Style()

        self.style.configure("Treeview", background="#2e2e2e", foreground="white",
                             fieldbackground="#2e2e2e", rowheight=25, font=("Helvetica", 12))

        self.style.configure("Treeview.Heading", background="#3c3c3c", foreground="white", font=("Helvetica", 14, "bold"))

        self.style.map("Treeview", background=[('selected', '#4e4e4e')],
                       foreground=[('selected', 'white')])

    def create_widgets(self):
        portfolio_frame = ttk.Frame(self.root, padding="10", style="TFrame")
        portfolio_frame.pack(side=tk.TOP, pady=10)

        self.btc_price_label = ttk.Label(portfolio_frame, text="BTC Price: $0.00", foreground="white", font=("Helvetica", 14))
        self.btc_price_label.grid(row=0, column=0, padx=5, pady=5)

        self.usd_balance_label = ttk.Label(portfolio_frame, text="USD Balance: $0.00", foreground="white", font=("Helvetica", 14))
        self.usd_balance_label.grid(row=0, column=1, padx=5, pady=5)

        self.portfolio_label = ttk.Label(portfolio_frame, text="Portfolio Value: $0.00", foreground="white", font=("Helvetica", 14))
        self.portfolio_label.grid(row=1, column=0, padx=5, pady=5)

        self.profit_label = ttk.Label(portfolio_frame, text="Profit: 0%", foreground="white", font=("Helvetica", 14))
        self.profit_label.grid(row=1, column=1, padx=5, pady=5)

        score_frame = ttk.Frame(self.root, padding="10", style="TFrame")
        score_frame.pack(side=tk.TOP, pady=10)

        self.sma_score_label = ttk.Label(score_frame, text="SMA Score: 0.00", foreground="white", font=("Helvetica", 12))
        self.sma_score_label.grid(row=0, column=0, padx=5, pady=5)

        self.fear_greed_score_label = ttk.Label(score_frame, text="Fear & Greed Score: 0", foreground="white", font=("Helvetica", 12))
        self.fear_greed_score_label.grid(row=0, column=1, padx=5, pady=5)

        self.sentiment_score_label = ttk.Label(score_frame, text="Sentiment Score: 0.00", foreground="white", font=("Helvetica", 12))
        self.sentiment_score_label.grid(row=0, column=2, padx=5, pady=5)

        self.buy_score_label = ttk.Label(score_frame, text="Total Buy Score: 0.00", foreground="lightgreen", font=("Helvetica", 14))
        self.buy_score_label.grid(row=1, column=0, padx=5, pady=5)

        self.sell_score_label = ttk.Label(score_frame, text="Total Sell Score: 0.00", foreground="red", font=("Helvetica", 14))
        self.sell_score_label.grid(row=1, column=1, padx=5, pady=5)

        table_frame = ttk.Frame(self.root, padding="10")
        table_frame.pack(side=tk.TOP, pady=10, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(table_frame, columns=("Time", "Price", "Action", "Balance (USD)", "BTC Position"),
                                 show='headings', height=10, style="Treeview")

        self.tree.heading("Time", text="Time", anchor=tk.CENTER)
        self.tree.heading("Price", text="Price (USDT)", anchor=tk.CENTER)
        self.tree.heading("Action", text="Action", anchor=tk.CENTER)
        self.tree.heading("Balance (USD)", text="Balance (USD)", anchor=tk.CENTER)
        self.tree.heading("BTC Position", text="BTC Position", anchor=tk.CENTER)

        self.tree.column("Time", width=120, anchor=tk.CENTER)
        self.tree.column("Price", width=120, anchor=tk.CENTER)
        self.tree.column("Action", width=150, anchor=tk.CENTER)
        self.tree.column("Balance (USD)", width=120, anchor=tk.CENTER)
        self.tree.column("BTC Position", width=120, anchor=tk.CENTER)

        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.BOTTOM, pady=10)

        self.start_button = ttk.Button(control_frame, text="Start", command=self.start_trading_and_candlestick)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_trading_and_candlestick)
        self.stop_button.pack(side=tk.LEFT, padx=5)

    def start_trading_and_candlestick(self):
        self.start_trading()
        self.open_candlestick_window()

    def stop_trading_and_candlestick(self):
        self.stop_trading()
        if self.candlestick_chart:
            self.candlestick_chart.stop_stream()

    def open_candlestick_window(self):
        candlestick_window = tk.Toplevel(self.root)
        candlestick_window.title("Candlestick Chart")
        candlestick_window.geometry("800x600")

        self.candlestick_chart = CandlestickChart(candlestick_window)

        chart_frame = ttk.Frame(candlestick_window, padding="10", style="TFrame")
        chart_frame.pack(side=tk.TOP, pady=10, fill=tk.BOTH, expand=True)

        self.candlestick_chart.create_chart_frame(chart_frame)

        self.candlestick_chart.start_candlestick_stream()

    def start_trading(self):
        if not self.trading_active:
            self.trading_active = True
            print("Trading started")

            self.socket_thread = threading.Thread(target=self.start_websocket)
            self.socket_thread.start()

    def stop_trading(self):
        if self.trading_active:
            self.trading_active = False
            print("Trading stopped")

            if self.ws:
                self.ws.close()

    def start_websocket(self):
        socket = "wss://stream.binance.com:9443/ws/btcusdt@trade"

        def on_message(ws, message):
            try:
                if not self.trading_active:
                    ws.close()
                    return

                data = json.loads(message)
                price = float(data['p'])  
                self.logic.update_price_data(price)

                decision, reason, sma_score, fear_greed_score, sentiment_score, buy_score, sell_score = self.logic.apply_trading_logic()

                self.update_gui(price, sma_score, fear_greed_score, sentiment_score, buy_score, sell_score)

                if decision != "Hold":
                    current_time = pd.Timestamp.now() 
                    action = self.logic.get_state()['last_trade']
                    usd_balance = f"${self.logic.get_state()['balance']:.2f}"
                    btc_position = f"{self.logic.get_state()['btc_position']:.6f} BTC"

                    row_color = "green" if "Buy" in action else "red"
                    self.tree.insert('', 'end', values=(current_time.strftime('%H:%M:%S'), f"${price:.2f}", action, usd_balance, btc_position), tags=(row_color,))
                    self.tree.tag_configure("green", foreground="green")
                    self.tree.tag_configure("red", foreground="red")

                    self.tree.yview_moveto(1)

                    if self.candlestick_chart:
                        self.candlestick_chart.mark_trade_action(price, action, current_time)

            except KeyError as e:
                print(f"KeyError: {e}")
            except ValueError as e:
                print(f"ValueError: {e}")
            except Exception as e:
                print(f"Unexpected WebSocket Error: {e}")
        def on_error(ws, error):
            print(f"WebSocket Error: {error}")

        def on_close(ws):
            print("WebSocket closed")

        def on_open(ws):
            print("WebSocket connection opened")

        self.ws = websocket.WebSocketApp(socket, on_message=on_message, on_error=on_error, on_close=on_close)
        self.ws.on_open = on_open
        self.ws.run_forever()

    def update_gui(self, price, sma_score, fear_greed_score, sentiment_score, buy_score, sell_score):
        self.btc_price_label.config(text=f"BTC Price: ${price:.2f}")

        state = self.logic.get_state()
        self.usd_balance_label.config(text=f"USD Balance: ${state['balance']:.2f}")

        total_value = state['balance'] + (state['btc_position'] * price)
        self.portfolio_label.config(text=f"Portfolio Value: ${total_value:.2f}")

        if self.root.initialbalance == 0:
            profit_percentage = 0
        else:
            profit_percentage = ((total_value - self.root.initialbalance) / self.root.initialbalance) * 100
        self.profit_label.config(text=f"Profit: {profit_percentage:.2f}%")

        color = "green" if profit_percentage > 0 else "red" if profit_percentage < 0 else "white"
        self.btc_price_label.config(foreground=color)
        self.usd_balance_label.config(foreground=color)
        self.portfolio_label.config(foreground=color)
        self.profit_label.config(foreground=color)

        self.sma_score_label.config(text=f"SMA Score: {sma_score:.2f}")
        self.fear_greed_score_label.config(text=f"Fear & Greed Score: {fear_greed_score}")
        self.sentiment_score_label.config(text=f"Sentiment Score: {sentiment_score:.2f}")
        self.buy_score_label.config(text=f"Total Buy Score: {buy_score:.2f}")
        self.sell_score_label.config(text=f"Total Sell Score: {sell_score:.2f}")
        
    def on_closing(self):
        self.stop_trading_and_candlestick()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoTradingBotGUI(root)
    root.mainloop()