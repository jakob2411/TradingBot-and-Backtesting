# TradingBot — Quick Manual

Portfolio management CLI for Alpaca, plus a minimal bot starting point.

## Quick Start
```bash
# 1) Create & activate venv
python3 -m venv .venv
source .venv/bin/activate

# 2) Install requirements
python -m pip install -r requirements.txt

# 3) Configure credentials (file or env)
# File: edit alpaca_secrets.py
#   ALPACA_API_KEY_ID = "YOUR_KEY"
#   ALPACA_API_SECRET_KEY = "YOUR_SECRET"
#   ALPACA_PAPER = True  # False for live
# Or env:
export APCA_API_KEY_ID="YOUR_KEY"
export APCA_API_SECRET_KEY="YOUR_SECRET"
export ALPACA_PAPER=true

# 4) Run the CLI
./master.py --help
./master.py account
```

Notes:
- Direct run works via the shebang; ensure the file is executable (`chmod +x master.py`).
- `.venv/` is ignored by [.gitignore](.gitignore); keep secrets out of Git.

## CLI Cheatsheet
```bash
# Account overview
./master.py account

# Positions
./master.py positions

# Orders
./master.py orders --status open --limit 20
./master.py orders --status all  --limit 50

# Buy / Sell (market)
./master.py buy  --symbol AAPL --qty 1   --tif DAY
./master.py sell --symbol TSLA --qty 0.5 --tif DAY

# Manage positions & orders
./master.py close-position   --symbol NVDA
./master.py cancel-order     --id <ORDER_ID>
./master.py cancel-open-orders
./master.py liquidate        # closes all positions (caution)

# Portfolio value
./master.py portfolio-value
```

## Minimal Bot (optional)
Save as `bot_example.py` and run inside the venv.
```python
#!/usr/bin/env python3
import os, time
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

client = TradingClient(os.getenv("APCA_API_KEY_ID"), os.getenv("APCA_API_SECRET_KEY"),
             paper=os.getenv("ALPACA_PAPER", "true").lower() not in {"0","false","no","off"})
SYMBOL, QTY, TARGET_PL = "AAPL", 1, 25.0

while True:
  try:
    acct = client.get_account()
    bp = float(getattr(acct, 'buying_power', 0))
    pos = next((p for p in client.get_all_positions() or [] if p.symbol == SYMBOL), None)

    if not pos and bp > 5000:
      client.submit_order(MarketOrderRequest(symbol=SYMBOL, qty=QTY, side=OrderSide.BUY, time_in_force=TimeInForce.DAY))
    elif pos and float(getattr(pos, 'unrealized_pl', 0.0) or 0.0) > TARGET_PL:
      client.submit_order(MarketOrderRequest(symbol=SYMBOL, qty=QTY, side=OrderSide.SELL, time_in_force=TimeInForce.DAY))
    time.sleep(30)
  except KeyboardInterrupt:
    break
  except Exception as e:
    print("Error:", e)
    time.sleep(10)
```
Run:
```bash
source .venv/bin/activate
python bot_example.py
```

## Troubleshooting
- `ModuleNotFoundError: alpaca`: install deps in venv (`pip install -r requirements.txt`).
- Missing credentials: use [alpaca_secrets.py](alpaca_secrets.py) or export env vars.
- Paper vs live: `ALPACA_PAPER=true|false` (paper is safe for testing).
