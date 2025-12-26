"""
MA200 strategy and simple backtester.

Rules (daily timeframe):
- Symbol: default 'SPY' (S&P 500 proxy)
- Go long when Close > 200-day simple moving average (SMA200)
- Exit to cash when Close < SMA200
- Max one trade per day (achieved by using daily bars and
  only reacting to previous day's signal). Orders are assumed
  to be executed at next day's open to avoid lookahead bias.

Backtest uses yfinance for historical data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import math
import datetime as dt

import pandas as pd

try:
    import yfinance as yf
except Exception as e:  # pragma: no cover
    yf = None


@dataclass
class BacktestResult:
    symbol: str
    start: pd.Timestamp
    end: pd.Timestamp
    initial_cash: float
    final_value: float
    total_return: float
    cagr: float
    max_drawdown: float
    trades: int
    summary: Dict[str, Any]
    equity_curve: pd.DataFrame


def _fetch_data(symbol: str, years: int) -> pd.DataFrame:
    if yf is None:
        raise RuntimeError("yfinance not installed. Please install with 'pip install yfinance'.")
    # Pull a bit more than requested to warm up SMA200
    period_years = max(years + 1, 2)
    df = yf.download(symbol, period=f"{period_years}y", interval="1d", auto_adjust=False, progress=False)
    if df is None or df.empty:
        raise RuntimeError(f"No data downloaded for {symbol}.")
    # Normalize columns - handle MultiIndex from newer yfinance versions
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns={c: c.title() if isinstance(c, str) else str(c).title() for c in df.columns})
    df = df[['Open', 'Close']].dropna()
    df.index = pd.to_datetime(df.index)
    return df


def _compute_sma200_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['SMA200'] = df['Close'].rolling(200, min_periods=200).mean()
    # Signal based on today's close vs SMA; position is prior-day signal to avoid lookahead
    df['signal'] = (df['Close'] > df['SMA200']).astype(int)
    df['position'] = df['signal'].shift(1).fillna(0)
    # Trade at next day's open, so compute open-to-open returns
    df['next_open'] = df['Open'].shift(-1)
    df['open_return'] = (df['next_open'] / df['Open']) - 1.0
    return df


def _restrict_to_window(df: pd.DataFrame, years: int) -> pd.DataFrame:
    if df.empty:
        return df
    end = df.index.max()
    start = end - pd.DateOffset(years=years)
    return df.loc[df.index >= start].copy()


def _max_drawdown(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    roll_max = series.cummax()
    dd = (series / roll_max) - 1.0
    return float(dd.min())


def backtest_ma200(
    symbol: str = "SPY",
    years: int = 5,
    initial_cash: float = 10_000.0,
) -> BacktestResult:
    """Run an MA200 backtest for the given symbol.

    Returns BacktestResult with metrics and equity curve.
    """
    if years < 1:
        raise ValueError("years must be >= 1")
    if initial_cash <= 0:
        raise ValueError("initial_cash must be > 0")

    raw = _fetch_data(symbol, years)
    with_signals = _compute_sma200_signals(raw)
    window = _restrict_to_window(with_signals, years)
    window = window.dropna(subset=['SMA200'])

    if len(window) < 5:
        raise RuntimeError("Not enough data in window after SMA warm-up.")

    # Strategy: apply position to open-to-open returns
    strat_ret = window['position'] * window['open_return']
    # Align to periods where next_open exists
    strat_ret = strat_ret.dropna()

    equity = (1.0 + strat_ret).cumprod() * initial_cash
    equity.name = 'equity'

    # Benchmark: buy-and-hold from first tradable open
    bh_ret = window['open_return'].dropna()
    bh_equity = (1.0 + bh_ret).cumprod() * initial_cash

    # Trades: count position changes (entry/exit); at most one change per day by design
    pos_changes = window['position'].diff().fillna(0)
    trades = int(pos_changes.abs().sum())

    # Metrics
    start_ts: pd.Timestamp = equity.index[0]
    end_ts: pd.Timestamp = equity.index[-1]
    days = (end_ts - start_ts).days or 1
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    years_elapsed = days / 365.25
    cagr = float((1.0 + total_return) ** (1.0 / years_elapsed) - 1.0) if years_elapsed > 0 else 0.0
    mdd = _max_drawdown(equity)

    out = pd.DataFrame({
        'equity': equity,
        'benchmark_equity': bh_equity.reindex(equity.index).ffill(),
        'position': window['position'].reindex(equity.index).fillna(0),
        'open_return': window['open_return'].reindex(equity.index),
        'strategy_return': strat_ret.reindex(equity.index),
        'close': window['Close'].reindex(equity.index),
        'sma200': window['SMA200'].reindex(equity.index),
    })

    summary = {
        'symbol': symbol,
        'period_days': days,
        'years_elapsed': years_elapsed,
        'initial_cash': initial_cash,
        'final_value': float(equity.iloc[-1]),
        'benchmark_final': float(out['benchmark_equity'].iloc[-1]),
        'total_return': total_return,
        'cagr': cagr,
        'max_drawdown': mdd,
        'trades': trades,
    }

    return BacktestResult(
        symbol=symbol,
        start=start_ts,
        end=end_ts,
        initial_cash=initial_cash,
        final_value=float(equity.iloc[-1]),
        total_return=total_return,
        cagr=cagr,
        max_drawdown=mdd,
        trades=trades,
        summary=summary,
        equity_curve=out,
    )


def run_cli(
    symbol: str = "SPY",
    years: int = 5,
    initial_cash: float = 10_000.0,
    csv: Optional[str] = None,
    plot: bool = False,
    plot_file: Optional[str] = None,
) -> None:
    """Convenience wrapper for CLI integration."""
    res = backtest_ma200(symbol=symbol, years=years, initial_cash=initial_cash)
    s = res.summary
    print("MA200 Backtest Summary")
    print(f"Symbol: {s['symbol']}")
    print(f"Period: {res.start.date()} → {res.end.date()}  (~{int(s['years_elapsed']*12)} months)")
    print(f"Initial: ${s['initial_cash']:,.2f}  Final: ${s['final_value']:,.2f}")
    print(f"Total Return: {s['total_return']*100:.2f}%  CAGR: {s['cagr']*100:.2f}%")
    print(f"Max Drawdown: {s['max_drawdown']*100:.2f}%  Trades: {s['trades']}")
    print(f"Benchmark Final: ${s['benchmark_final']:,.2f}")
    if csv:
        res.equity_curve.to_csv(csv, index=True)
        print(f"Equity curve saved to {csv}")
    if plot or plot_file:
        try:
            plot_backtest(res, save=plot_file, show=plot)
        except Exception as e:
            print(f"Plotting failed: {e}")


def plot_backtest(result: BacktestResult, save: Optional[str] = None, show: bool = True) -> None:
    """Plot equity vs benchmark and position; optionally save to file.

    - Uses matplotlib only if available; install via `pip install matplotlib`.
    - If `save` is provided, saves the figure before showing.
    - If `show` is False, the window is not displayed (useful for headless save).
    """
    try:
        import matplotlib.pyplot as plt
    except Exception as e:  # pragma: no cover
        raise RuntimeError("matplotlib not installed. Install with 'pip install matplotlib'.") from e

    df = result.equity_curve.copy()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 9), sharex=True,
                                    gridspec_kw={'height_ratios': [3, 2, 1]})

    ax1.plot(df.index, df['equity'], label='Strategy Equity', color='#2E86DE', linewidth=2)
    if 'benchmark_equity' in df:
        ax1.plot(df.index, df['benchmark_equity'], label='Benchmark (Buy&Hold)', color='#7F8C8D', linewidth=2)
    ax1.set_ylabel('Equity ($)')
    ax1.set_title(f"MA200 Backtest {result.symbol}: {result.start.date()} → {result.end.date()}")
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)

    # Price & SMA200 subplot
    if 'close' in df and 'sma200' in df:
        ax2.plot(df.index, df['close'], label='Close Price', color='#3498DB', linewidth=1.5)
        ax2.plot(df.index, df['sma200'], label='SMA200', color='#E74C3C', linewidth=1.5, linestyle='--')
        ax2.set_ylabel('Price ($)')
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)

    # Position subplot (0/1)
    pos = df.get('position')
    if pos is not None:
        ax3.step(df.index, pos.fillna(0), where='post', color='#27AE60', linewidth=2)
        ax3.set_ylabel('Position')
        ax3.set_yticks([0, 1])
        ax3.set_ylim(-0.1, 1.1)
        ax3.grid(True, alpha=0.3)

    fig.tight_layout()
    if save:
        fig.savefig(save, dpi=150, bbox_inches='tight')
    if show:
        plt.show()
    plt.close(fig)
