#!/usr/bin/env python
import os
import time
import logging
from binance.client import Client

# ======================
# Configuration Setup
# ======================
def load_config():
    """Load configuration from .env file without external packages"""
    config = {}
    try:
        with open('.env') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    except FileNotFoundError:
        print("Warning: No .env file found. Using default testnet config.")
        config = {
            'BINANCE_API_KEY': 'your_testnet_key',
            'BINANCE_API_SECRET': 'your_testnet_secret',
            'USE_TESTNET': 'True',
            'SYMBOL': 'BTCUSDT',
            'BUY_THRESHOLD': '60000',
            'SELL_THRESHOLD': '68000',
            'TRADE_QUANTITY': '0.001'
        }
    return config

config = load_config()

# ======================
# Initialize Services
# ======================
client = Client(
    api_key=config['BINANCE_API_KEY'],
    api_secret=config['BINANCE_API_SECRET'],
    testnet=config.get('USE_TESTNET', 'True').lower() == 'true'
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

# ======================
# Trading Functions
# ======================
def get_account_balance():
    """Get available balances"""
    return {
        item['asset']: float(item['free'])
        for item in client.get_account()['balances']
        if float(item['free']) > 0
    }

def send_alert(message):
    """Basic alert system (extend with Telegram/Email later)"""
    logging.warning(f"ALERT: {message}")

def execute_safe_trade(symbol, quantity, is_buy):
    """Handles trades with error checking"""
    try:
        order_func = client.order_market_buy if is_buy else client.order_market_sell
        order = order_func(symbol=symbol, quantity=quantity)
        logging.info(f"{'BUY' if is_buy else 'SELL'} order executed: {order}")
        return True
    except Exception as e:
        logging.error(f"Trade failed: {e}")
        send_alert(f"TRADE FAILED: {symbol} {quantity} {'BUY' if is_buy else 'SELL'}")
        return False

# ======================
# Main Trading Logic
# ======================
def run_bot():
    logging.info("=== Starting Trading Bot ===")
    logging.info(f"Mode: {'TESTNET' if client.testnet else 'LIVE'}")
    logging.info(f"Balance: {get_account_balance()}")

    symbol = config['SYMBOL']
    buy_price = float(config['BUY_THRESHOLD'])
    sell_price = float(config['SELL_THRESHOLD'])
    quantity = float(config['TRADE_QUANTITY'])
    check_interval = 3  # seconds

    in_position = False
    
    try:
        while True:
            # Get market data
            price = float(client.get_symbol_ticker(symbol=symbol)['price'])
            logging.info(f"{symbol} Price: ${price:,.2f} | Position: {'YES' if in_position else 'NO'}")

            # Trading logic
            if not in_position and price < buy_price:
                if execute_safe_trade(symbol, quantity, is_buy=True):
                    in_position = True
                    send_alert(f"Bought {quantity} {symbol} at ${price:,.2f}")

            elif in_position and price > sell_price:
                if execute_safe_trade(symbol, quantity, is_buy=False):
                    in_position = False
                    send_alert(f"Sold {quantity} {symbol} at ${price:,.2f}")

            time.sleep(check_interval)

    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.critical(f"Fatal error: {e}", exc_info=True)
        send_alert(f"BOT CRASHED: {e}")

if __name__ == "__main__":
    run_bot()
