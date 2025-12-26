# TradingBot & Backtesting — Quick Manual

**Portfolio management CLI for Alpaca** with comprehensive **backtesting capabilities** and bot automation.

## 🎯 Key Features

- **📊 Advanced Backtesting Engine**: Test trading strategies over 3-50 years of historical data
- **📈 Multiple Strategies**: MA200, Buyback-N, and support for 1x-3x leveraged ETFs
- **💰 Portfolio Management**: Complete CLI for Alpaca trading (buy, sell, positions, orders)
- **🤖 Bot Framework**: Minimal starting point for automated trading
- **📉 Risk Analysis**: Comprehensive performance metrics (CAGR, Sharpe, Max Drawdown)
- **📊 Visualization**: Generate charts and export data to CSV

For more information, see the [official Alpaca documentation](https://docs.alpaca.markets/docs/getting-started).

**Historical market data** is retrieved via [yfinance](https://ranaroussi.github.io/yfinance/) for backtesting purposes.

---

## ⚠️ Disclaimer

**This software is for educational and research purposes only. It is NOT investment advice.**

- **Past performance does not guarantee future results.** All backtest results presented are based on historical data and do not indicate future performance.
- **Trading involves substantial risk of loss.** You may lose some or all of your invested capital.
- **Do your own research.** Always conduct independent research before making investment decisions.
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

---

## 📊 Backtesting Strategies

This project includes a **comprehensive backtesting engine** with two proven strategies tested over decades of market data.

### 🎯 Available Strategies

#### 1. **MA200 Strategy** (Moving Average Crossover)
- **Logic**: Buy when price > MA200, sell when below
- **Best for**: Simple trend following
- **Typical CAGR**: 8-12% (SPY)
- **Max Drawdown**: ~25-35%

#### 2. **Buyback-N Strategy** ⭐ **Recommended**
- **Logic**: Sell on MA200 cross below, auto-buyback after N trading days
- **Innovation**: Prevents "missing the market" during recoveries
- **Parameter Study**: Tested with 2, 5, 8, 10, 12, 15, 20 wait days
- **Best Configuration**: 
  - **10-12 wait days** for optimal risk/return balance
  - **SPY (1x)**: 24% CAGR, -18% Max DD (10Y)
  - **SSO (2x)**: 42% CAGR, -45% Max DD (10Y) 🚀
  - **15Y SSO**: 38.55% CAGR, turns $10K into $1.34M

### 📈 Tested Instruments

- **SPY** (S&P 500): Standard, lower risk
- **SSO** (2x Leveraged S&P 500): Higher returns, higher risk
- **Custom symbols**: Works with any ticker available on yfinance

### 🔬 Extensive Testing Periods

- **3 years** (2022-2025): Recent bull market
- **5 years** (2020-2025): Including COVID crash recovery
- **10 years** (2015-2025): Full market cycle
- **15 years** (2010-2025): Post-2008 recovery + growth
- **20 years** (2006-2025): Including 2008 Financial Crisis
- **25 years** (2000-2025): Dot-com + Financial Crisis + COVID
- **50 years** (1975-2025): Maximum available data (when data exists)

### 📊 Key Findings

**Buyback Strategy vs Buy&Hold (10Y SPY):**
- Strategy: **+765%** return (24% CAGR)
- Buy&Hold: **+234%** return (13% CAGR)
- **Outperformance: +531 percentage points** ⭐

**With 2x Leverage (10Y SSO):**
- Strategy: **+3,232%** return (42% CAGR)
- Buy&Hold: **+655%** return
- Max Drawdown: -45% (manageable for leverage)

**📄 Detailed Analysis**: See [strategies/buyback_strategy_explanation.md](strategies/buyback_strategy_explanation.md) for:
- Complete parameter optimization studies
- Risk/return analysis
- Whipsaw analysis (trade frequency by year)
- Leverage comparison tables
- Historical drawdown analysis
- Visual charts and examples

---

## CLI Cheatsheet

### Portfolio Management
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

### Backtesting Commands

#### MA200 Strategy
```bash
./master.py backtest-ma200                              # MA200, 5 years (default)
./master.py backtest-ma200 --years 1                    # 1 year backtest
./master.py backtest-ma200 --years 10                   # 10 years backtest
./master.py backtest-ma200 --ma-period 50               # Use MA50 instead of MA200
./master.py backtest-ma200 --symbol SPY --years 5 --initial-cash 20000
./master.py backtest-ma200 --csv equity.csv             # save data to CSV
./master.py backtest-ma200 --plot                       # show plot window
./master.py backtest-ma200 --plot-file backtest.png     # save plot image (auto-saved to outputs/)
./master.py backtest-ma200 --years 10 --plot            # 10 years with plot
```

#### Buyback Strategy ⭐
```bash
# Basic usage
./master.py backtest-buyback                            # 10-day wait, 5 years (default)
./master.py backtest-buyback --years 10                 # 10 years backtest
./master.py backtest-buyback --years 3                  # Recent 3-year bull market

# Parameter optimization
./master.py backtest-buyback --wait-days 12             # Buy back after 12 days
./master.py backtest-buyback --wait-days 10 --years 10  # Optimal config
./master.py backtest-buyback --ma-period 200 --wait-days 10  # Full config

# Different instruments
./master.py backtest-buyback --symbol SPY --years 10    # Standard S&P 500
./master.py backtest-buyback --symbol SSO --years 10    # 2x Leveraged (higher risk/return)
./master.py backtest-buyback --symbol UPRO --years 5    # 3x Leveraged (extreme)

# Output options
./master.py backtest-buyback --plot                     # Show interactive chart
./master.py backtest-buyback --plot-file result.png     # Save chart (auto to outputs/)
./master.py backtest-buyback --csv equity.csv           # Export data to CSV
./master.py backtest-buyback --years 10 --wait-days 12 --plot-file SPY_10Y.png

# Real-world examples:
# SPY (Standard):
./master.py backtest-buyback --symbol SPY --years 10 --wait-days 12 --plot-file SPY_10Y.png
# Result: +765% return, 24.09% CAGR, -18.36% Max DD

# SSO (2x Leverage):
./master.py backtest-buyback --symbol SSO --years 10 --wait-days 10 --plot-file SSO_10Y.png
# Result: +3,232% return, 42% CAGR, -44.86% Max DD

# SSO (15 years - Sweet Spot):
./master.py backtest-buyback --symbol SSO --years 15 --wait-days 10 --plot-file SSO_15Y.png
# Result: +13,166% return, 38.55% CAGR, $10K → $1.34M 🚀
```

**Performance Summary** (Buyback Strategy, 10 years):

| Symbol | Wait Days | Total Return | CAGR | Max DD | Final Value |
|--------|-----------|--------------|------|--------|-------------|
| SPY    | 12        | **+765%**    | 24.09% | -18.36% | $86,527 |
| SPY    | 10        | **+736%**    | 23.66% | -19.56% | $83,589 |
| SSO    | 10        | **+3,232%**  | 42.00% | -44.86% | $333,206 |
| Buy&Hold SPY | -   | +234%        | 13.01% | -35%    | $33,441 |

---

## 🤖 Minimal Bot (Optional)
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
