# TradingBot — Quick Manual

**Portfolio management CLI for Alpaca** with comprehensive **backtesting capabilities** and bot automation.

## 🎯 Key Features

- **📊 Advanced Backtesting Engine**: Test trading strategies over 3-50 years of historical data
- **📈 Multiple Strategies**: MA200, Buyback-N, and support for 1x-3x leveraged ETFs
- **💰 Portfolio Management**: Complete CLI for Alpaca trading (buy, sell, positions, orders)
- **🤖 Bot Framework**: Minimal starting point for automated trading
- **📉 Risk Analysis**: Comprehensive performance metrics (CAGR, Sharpe, Max Drawdown)
- **📊 Visualization**: Generate charts and export data to CSV

For more information, see the [official Alpaca documentation](https://docs.alpaca.markets/docs/getting-started).

---

## ⚠️ Disclaimer

**This software is for educational and research purposes only. It is NOT investment advice.**

- **Past performance does not guarantee future results.** All backtest results presented are based on historical data and do not indicate future performance.
- **Trading involves substantial risk of loss.** You may lose some or all of your invested capital.
- **Do your own research.** Always conduct independent research and consult with licensed financial advisors before making investment decisions.
- **No warranties.** This software is provided "as is" without any warranties of any kind, express or implied.
- **Use at your own risk.** The authors and contributors are not responsible for any financial losses or damages resulting from the use of this software.

By using this software, you acknowledge that you understand these risks and agree to use it responsibly.

---

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

# Backtest: Moving Average Strategy
# Buys when price > N-day moving average, sells when below
./master.py backtest-ma200                              # MA200, 5 years (default)
./master.py backtest-ma200 --years 1                    # 1 year backtest
./master.py backtest-ma200 --years 10                   # 10 years backtest
./master.py backtest-ma200 --ma-period 50               # Use MA50 instead of MA200
./master.py backtest-ma200 --symbol SPY --years 5 --initial-cash 20000
./master.py backtest-ma200 --csv equity.csv             # save data to CSV
./master.py backtest-ma200 --plot                       # show plot window
./master.py backtest-ma200 --plot-file backtest.png     # save plot image (auto-saved to outputs/)
./master.py backtest-ma200 --years 10 --plot            # 10 years with plot

# Backtest: Buyback Strategy (Superior Performance!)
# Sells when price crosses below MA200, automatically buys back after N days
# This strategy often outperforms simple MA and buy-and-hold strategies
./master.py backtest-buyback                            # 10-day wait, 5 years (default)
./master.py backtest-buyback --years 10                 # 10 years backtest
./master.py backtest-buyback --wait-days 12             # Buy back after 12 days
./master.py backtest-buyback --ma-period 200 --wait-days 10  # Full config
./master.py backtest-buyback --symbol SPY --years 10 --wait-days 12 --plot-file result.png
./master.py backtest-buyback --csv equity.csv           # save data to CSV

# Example Results (SPY, 10 years):
# - Buyback-12: 765% return, 24.09% CAGR (best overall)
# - Buyback-10: 736% return, 23.66% CAGR
# - MA200:      135% return,  8.91% CAGR
# - Buy&Hold:   234% return, ~12.8% CAGR
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
- `ModuleNotFoundError: yfinance|pandas|matplotlib`: install deps via `pip install -r requirements.txt`.
- Missing credentials: use [alpaca_secrets.py](alpaca_secrets.py) or export env vars.
- Paper vs live: `ALPACA_PAPER=true|false` (paper is safe for testing).
