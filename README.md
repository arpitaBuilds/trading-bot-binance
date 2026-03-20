# 🤖 Binance Futures Testnet Trading Bot

A lightweight Python CLI bot I built to place and manage orders on the 
Binance USDT-M Futures Testnet — no heavy wrappers, just clean `requests`.

---

## Why I Built It This Way

Most trading bot examples either use the full `python-binance` SDK (which 
hides too much) or are a single messy script. I wanted something in between — 
structured enough to extend, simple enough to read in one sitting.

The code is split into four clear layers:
- **client.py** — handles all HTTP, signing, and error mapping
- **orders.py** — bridges validated params to the client, returns clean results
- **validators.py** — catches bad input before any network call is made
- **cli.py** — thin interface layer, just parsing and pretty output

---

## Project Structure
```
trading_bot/
├── bot/
│   ├── client.py           # HMAC-signed REST client
│   ├── orders.py           # Order placement + OrderResult dataclass
│   ├── validators.py       # Input validation
│   └── logging_config.py  # File + console logging
├── cli.py                  # CLI entry point (argparse)
├── logs/                   # Auto-created daily log files
├── .env.example            # Credential template
└── requirements.txt
```

---

## Setup

### 1. Clone and install
```bash
git clone https://github.com/YOUR_USERNAME/trading-bot-binance
cd trading-bot-binance
pip install -r requirements.txt
```

### 2. Add your Testnet credentials

Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
```
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
```

Get your keys from: https://testnet.binancefuture.com  
(Login → API Key tab → Generate)

---

## Running the Bot

### Place a MARKET order
```bash
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.002
```

### Place a LIMIT order
```bash
python cli.py order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.002 --price 90000
```

### Place a STOP_MARKET order
```bash
python cli.py order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.002 --stop-price 80000
```

### Interactive guided mode (my favourite way to test)
```bash
python cli.py interactive
```
Prompts you step by step — useful when you don't want to remember all the flags.

### List open orders
```bash
python cli.py open-orders --symbol BTCUSDT
```

### Cancel an order
```bash
python cli.py cancel --symbol BTCUSDT --order-id 12345
```

### Verbose logging (shows full request/response)
```bash
python cli.py --log-level DEBUG order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.002
```

---

## Example Output
```
────────────────────────────────────────────────────────
  📋  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────
  Symbol      : BTCUSDT
  Side        : BUY
  Order Type  : MARKET
  Quantity    : 0.002
────────────────────────────────────────────────────────

════════════════════════════════════════════════════════
  ✅  ORDER PLACED SUCCESSFULLY
════════════════════════════════════════════════════════
  Order ID      : 12894769755
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : NEW
  Orig Qty      : 0.002
  Executed Qty  : 0.000
════════════════════════════════════════════════════════
```

---

## Logging

Logs are written to `logs/trading_bot_YYYYMMDD.log` automatically.

Each entry captures the full request body, response, and any errors — 
useful for debugging without adding print statements everywhere.

---

## A Few Things I Assumed

- **Testnet only** — the base URL is hardcoded to `testnet.binancefuture.com`. 
  Swapping to live is one line change in `client.py`.
- **One-way mode** — uses `positionSide: BOTH`. Hedge mode would need 
  an extra parameter.
- **No leverage management** — set leverage manually in the testnet UI 
  before trading.
- **Minimum notional $100** — Binance rejects orders below this. 
  For BTCUSDT, quantity of 0.002 works fine.

---

## Dependencies

Only three packages needed:

| Package | Version | Why |
|---|---|---|
| `requests` | ≥ 2.31 | HTTP calls to Binance API |
| `python-dotenv` | ≥ 1.0 | Load credentials from `.env` |
| `colorama` | ≥ 0.4.6 | Colored terminal output on Windows |