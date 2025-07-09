#!/usr/bin/env python
import os
import time
import argparse
import logging
from binance.client import Client
from binance.enums import *

# ======================
# Load Config from .env or CLI
# ======================
def load_env():
    config = {}
    try:
        with open('.env') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    except FileNotFoundError:
        logging.warning(".env file not found. Proceeding with CLI/default config.")
    return config

# ======================
# Logging Setup
# ======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

# ======================
# Main Trading Bot Class
# ======================
class BasicBot:
    def __init__(self, api_key, api_secret, symbol, buy_price, sell_price, quantity, testnet=True):
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.symbol = symbol
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.quantity = quantity
        self.in_position = False

    def get_balance(self):
        try:
            info = self.client.get_account()
            return {
                b['asset']: float(b['free'])
                for b in info['balances'] if float(b['free']) > 0
            }
        except Exception as e:
            logging.error(f"Failed to fetch account balance: {e}")
            return {}

    def execute_trade(self, is_buy):
        try:
            if is_buy:
                order = self.client.order_market_buy(symbol=self.symbol, quantity=self.quantity)
            else:
                order = self.client.order_market_sell(symbol=self.symbol, quantity=self.quantity)
            logging.info(f"{'BUY' if is_buy else 'SELL'} order executed: {order}")
            return True
        except Exception as e:
            logging.error(f"Trade failed: {e}")
            return False

    def place_stop_limit_sell(self, stop_price, limit_price):
        try:
            order = self.client.create_order(
                symbol=self.symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_STOP_LOSS_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=self.quantity,
                price=str(limit_price),
                stopPrice=str(stop_price)
            )
            logging.info(f"Stop-Limit SELL order placed: {order}")
        except Exception as e:
            logging.error(f"Failed to place stop-limit sell order: {e}")

    def place_oco_order(self, take_profit_price, stop_price, stop_limit_price):
        try:
            order = self.client.create_oco_order(
                symbol=self.symbol,
                side=SIDE_SELL,
                quantity=self.quantity,
                price=str(take_profit_price),
                stopPrice=str(stop_price),
                stopLimitPrice=str(stop_limit_price),
                stopLimitTimeInForce=TIME_IN_FORCE_GTC
            )
            logging.info(f"OCO SELL order placed: {order}")
        except Exception as e:
            logging.error(f"Failed to place OCO order: {e}")

    def run(self, ui_mode=False):
        logging.info("=== Trading Bot Started ===")
        logging.info(f"Symbol: {self.symbol}, Buy below: {self.buy_price}, Sell above: {self.sell_price}")
        logging.info(f"Balance: {self.get_balance()}")

        try:
            while True:
                try:
                    price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
                    logging.info(f"{self.symbol} Price: ${price:.2f} | Position: {'YES' if self.in_position else 'NO'}")

                    if ui_mode:
                        user_input = input("Enter 'b' to buy, 's' to sell, 'oco' for OCO, 'stop' for Stop-Limit, or 'q' to quit: ").strip().lower()
                        if user_input == 'b':
                            self.execute_trade(is_buy=True)
                        elif user_input == 's':
                            self.execute_trade(is_buy=False)
                        elif user_input == 'oco':
                            tp = float(input("Take Profit Price: "))
                            sp = float(input("Stop Price: "))
                            slp = float(input("Stop Limit Price: "))
                            self.place_oco_order(tp, sp, slp)
                        elif user_input == 'stop':
                            sp = float(input("Stop Price: "))
                            lp = float(input("Limit Price: "))
                            self.place_stop_limit_sell(sp, lp)
                        elif user_input == 'q':
                            break
                        continue

                    if not self.in_position and price < self.buy_price:
                        if self.execute_trade(is_buy=True):
                            self.in_position = True
                            logging.info(f"BOUGHT {self.quantity} {self.symbol} at ${price:.2f}")

                    elif self.in_position and price > self.sell_price:
                        if self.execute_trade(is_buy=False):
                            self.in_position = False
                            logging.info(f"SOLD {self.quantity} {self.symbol} at ${price:.2f}")

                    time.sleep(3)

                except KeyboardInterrupt:
                    logging.info("Bot stopped by user.")
                    break
                except Exception as e:
                    logging.error(f"Error in main loop: {e}")

        except Exception as e:
            logging.critical(f"Fatal bot crash: {e}", exc_info=True)


# ======================
# Main Entrypoint
# ======================
if __name__ == '__main__':
    env = load_env()

    parser = argparse.ArgumentParser(description="Binance Futures Testnet Trading Bot")
    parser.add_argument('--api_key', default=env.get('BINANCE_API_KEY', ''), help='Binance API Key')
    parser.add_argument('--api_secret', default=env.get('BINANCE_API_SECRET', ''), help='Binance API Secret')
    parser.add_argument('--symbol', default=env.get('SYMBOL', 'BTCUSDT'), help='Trading symbol')
    parser.add_argument('--buy', type=float, default=float(env.get('BUY_THRESHOLD', '60000')), help='Buy threshold')
    parser.add_argument('--sell', type=float, default=float(env.get('SELL_THRESHOLD', '68000')), help='Sell threshold')
    parser.add_argument('--qty', type=float, default=float(env.get('TRADE_QUANTITY', '0.001')), help='Trade quantity')
    parser.add_argument('--testnet', action='store_true', default=env.get('USE_TESTNET', 'True').lower() == 'true', help='Use Binance Futures Testnet')
    parser.add_argument('--ui', action='store_true', help='Enable interactive CLI mode')

    args = parser.parse_args()

    bot = BasicBot(
        api_key=args.api_key,
        api_secret=args.api_secret,
        symbol=args.symbol,
        buy_price=args.buy,
        sell_price=args.sell,
        quantity=args.qty,
        testnet=args.testnet
    )
    bot.run(ui_mode=args.ui)
