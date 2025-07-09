# 🪙 Binance Futures Trading Bot (Python)

This is a **Python-based automated trading bot** that works with the [Binance Futures Testnet](https://testnet.binancefuture.com/). It can place **market orders**, **stop-limit orders**, and **OCO (One-Cancels-the-Other)** orders. It also includes a **CLI mode** for manual trading and a fully automatic mode for price-based buying/selling.

---

## 🚀 Features

- Connects to **Binance USDT-M Futures Testnet**
- Places **Buy/Sell Market Orders**
- Supports **Stop-Limit** and **OCO Orders**
- CLI Arguments + `.env` file support
- Optional **interactive mode** (`--ui`)
- Full **logging** of trades, errors, and market prices
- Exception-safe design with easy customization

---

## 🛠 Requirements

- Python 3.7+
- `python-binance` library

```bash
pip install python-binance
