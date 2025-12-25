#!/usr/bin/env python3

# active venv first: source .venv/bin/activate
# execute CLI: ./master.py <command> [options]

"""
Master CLI for portfolio management using Alpaca (alpaca-py).

Quick start examples:
    # Show help
    python master.py --help

    # Show account info (cash, buying power, equity)
    python master.py account

    # List open positions
    python master.py positions

    # List recent orders
    python master.py orders --status open --limit 20

    # Buy 1 share of AAPL (market order, day)
    python master.py buy --symbol AAPL --qty 1 --tif DAY

    # Sell 0.5 shares of TSLA (fractional, market)
    python master.py sell --symbol TSLA --qty 0.5 --tif DAY

    # Close position in NVDA
    python master.py close-position --symbol NVDA

    # Cancel an order by ID
    python master.py cancel-order --id <ORDER_ID>

    # Cancel all open orders
    python master.py cancel-open-orders

    # Liquidate all positions (use with caution!)
    python master.py liquidate

Credentials:
    - Preferred: put keys in alpaca_secrets.py as shown.
    - Or set env vars: APCA_API_KEY_ID, APCA_API_SECRET_KEY
    - Paper/live: set ALPACA_PAPER=true/false (default: true)

Notes:
    - Requires package 'alpaca-py'. Install: pip install alpaca-py
    - Some endpoints may require extra permissions on live accounts.
"""

import os
import os
import sys
import argparse
from typing import Optional
try:
    import alpaca_secrets as _secrets
except Exception:  # pragma: no cover
    _secrets = None


def _get_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def get_client():
    """Create an authenticated TradingClient using secrets or env vars."""
    from alpaca.trading.client import TradingClient
    api_key = getattr(_secrets, "ALPACA_API_KEY_ID", None) if _secrets else None
    secret_key = getattr(_secrets, "ALPACA_API_SECRET_KEY", None) if _secrets else None

    api_key = api_key or _get_env("APCA_API_KEY_ID", "ALPACA_API_KEY", "ALPACA_KEY")
    secret_key = secret_key or _get_env("APCA_API_SECRET_KEY", "ALPACA_API_SECRET", "ALPACA_SECRET")

    paper = getattr(_secrets, "ALPACA_PAPER", None) if _secrets else None
    if paper is None:
        paper_raw = os.getenv("ALPACA_PAPER", "true").strip().lower()
        paper = paper_raw not in {"0", "false", "no", "off"}

    if not api_key or not secret_key:
        raise SystemExit(
            "Missing Alpaca credentials. Set them in alpaca_secrets.py or via env vars "
            "(APCA_API_KEY_ID / APCA_API_SECRET_KEY)."
        )

    return TradingClient(api_key, secret_key, paper=paper)


def cmd_account(args: argparse.Namespace) -> None:
    client = get_client()
    account = client.get_account()
    # Prints core account fields to provide a quick overview
    print(f"Account ID: {getattr(account, 'id', 'N/A')}")
    print(f"Status: {getattr(account, 'status', 'N/A')}")
    print(f"Type: {getattr(account, 'type', getattr(account, 'account_type', 'N/A'))}")
    print(f"Cash: ${getattr(account, 'cash', '0')}")
    print(f"Buying Power: ${getattr(account, 'buying_power', '0')}")
    dtbp = getattr(account, 'daytrading_buying_power', None)
    if dtbp is not None:
        print(f"Day-Trading Buying Power: ${dtbp}")
    equity = getattr(account, 'equity', None)
    if equity is not None:
        print(f"Equity: ${equity}")
    multiplier = getattr(account, 'multiplier', None)
    if multiplier is not None:
        print(f"Margin Multiplier: {multiplier}x")
    pdt = getattr(account, 'pattern_day_trader', None)
    if pdt is not None:
        print(f"Pattern Day Trader: {pdt}")


def cmd_positions(args: argparse.Namespace) -> None:
    client = get_client()
    try:
        positions = client.get_all_positions()
    except Exception as e:
        print(f"Failed to fetch positions: {e}")
        return
    if not positions:
        print("No open positions.")
        return
    for p in positions:
        symbol = getattr(p, 'symbol', 'N/A')
        qty = getattr(p, 'qty', '0')
        avg_entry = getattr(p, 'avg_entry_price', '0')
        current_price = getattr(p, 'current_price', getattr(p, 'asset_current_price', 'N/A'))
        market_value = getattr(p, 'market_value', '0')
        unrealized_pl = getattr(p, 'unrealized_pl', None)
        print(f"{symbol}: qty={qty} avg={avg_entry} price={current_price} value=${market_value} P/L={unrealized_pl}")


def cmd_orders(args: argparse.Namespace) -> None:
    client = get_client()
    try:
        # Prefer status filter; some versions don't support 'limit' arg
        orders = client.get_orders(status=args.status)
    except Exception:
        try:
            orders = client.get_orders()
        except Exception as e:
            print(f"Failed to fetch orders: {e}")
            return
    if not orders:
        print("No orders found.")
        return
    # Apply local limit if provided
    try:
        orders_iter = list(orders)[: args.limit]
    except Exception:
        orders_iter = orders
    for o in orders_iter:
        oid = getattr(o, 'id', 'N/A')
        symbol = getattr(o, 'symbol', 'N/A')
        side = getattr(o, 'side', 'N/A')
        qty = getattr(o, 'qty', getattr(o, 'quantity', 'N/A'))
        status = getattr(o, 'status', 'N/A')
        submitted_at = getattr(o, 'submitted_at', getattr(o, 'created_at', ''))
        print(f"{oid} {submitted_at} {symbol} {side} qty={qty} status={status}")


def _parse_tif(value: str):
    from alpaca.trading.enums import TimeInForce
    value = value.upper()
    try:
        return TimeInForce[value]
    except KeyError:
        valid = ", ".join([m.name for m in TimeInForce])
        raise argparse.ArgumentTypeError(f"Invalid time-in-force: {value}. Valid: {valid}")


def cmd_buy(args: argparse.Namespace) -> None:
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide
    client = get_client()
    order_req = MarketOrderRequest(
        symbol=args.symbol,
        qty=args.qty,
        side=OrderSide.BUY,
        time_in_force=_parse_tif(args.tif),
    )
    print("Submitting BUY market order...")
    order = client.submit_order(order_data=order_req)
    print(f"Order submitted: id={getattr(order, 'id', 'N/A')} status={getattr(order, 'status', 'N/A')}")


def cmd_sell(args: argparse.Namespace) -> None:
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide
    client = get_client()
    order_req = MarketOrderRequest(
        symbol=args.symbol,
        qty=args.qty,
        side=OrderSide.SELL,
        time_in_force=_parse_tif(args.tif),
    )
    print("Submitting SELL market order...")
    order = client.submit_order(order_data=order_req)
    print(f"Order submitted: id={getattr(order, 'id', 'N/A')} status={getattr(order, 'status', 'N/A')}")


def cmd_close_position(args: argparse.Namespace) -> None:
    client = get_client()
    try:
        resp = client.close_position(args.symbol)
        print(f"Close position request sent for {args.symbol}: {resp}")
    except Exception as e:
        print(f"Failed to close position for {args.symbol}: {e}")


def cmd_cancel_order(args: argparse.Namespace) -> None:
    client = get_client()
    try:
        client.cancel_order_by_id(args.id)
        print(f"Canceled order {args.id}")
    except Exception as e:
        print(f"Failed to cancel order {args.id}: {e}")


def cmd_cancel_open_orders(args: argparse.Namespace) -> None:
    client = get_client()
    try:
        client.cancel_orders()
        print("Canceled all open orders.")
    except Exception as e:
        print(f"Failed to cancel open orders: {e}")


def cmd_liquidate(args: argparse.Namespace) -> None:
    client = get_client()
    try:
        resp = client.close_all_positions(cancel_orders=True)
        print(f"Liquidation requested: {resp}")
    except Exception as e:
        print(f"Failed to liquidate positions: {e}")


def cmd_portfolio_value(args: argparse.Namespace) -> None:
    client = get_client()
    try:
        positions = client.get_all_positions()
    except Exception as e:
        print(f"Failed to fetch positions: {e}")
        return
    total = 0.0
    for p in positions:
        try:
            total += float(getattr(p, 'market_value', 0.0))
        except Exception:
            pass
    print(f"Portfolio Market Value: ${total:.2f}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portfolio",
        description="Portfolio management CLI powered by Alpaca (alpaca-py)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # account
    p_account = sub.add_parser("account", help="Show account info")
    p_account.set_defaults(func=cmd_account)

    # positions
    p_positions = sub.add_parser("positions", help="List open positions")
    p_positions.set_defaults(func=cmd_positions)

    # orders
    p_orders = sub.add_parser("orders", help="List recent orders")
    p_orders.add_argument("--status", default="all", choices=["open", "closed", "all"], help="Order status filter")
    p_orders.add_argument("--limit", type=int, default=50, help="Max number of orders to fetch")
    p_orders.set_defaults(func=cmd_orders)

    # buy
    p_buy = sub.add_parser("buy", help="Submit a BUY market order")
    p_buy.add_argument("--symbol", required=True, help="Ticker symbol, e.g. AAPL")
    p_buy.add_argument("--qty", type=float, required=True, help="Quantity (supports fractional if enabled)")
    p_buy.add_argument("--tif", default="DAY", help="Time in force (e.g. DAY, GTC)")
    p_buy.set_defaults(func=cmd_buy)

    # sell
    p_sell = sub.add_parser("sell", help="Submit a SELL market order")
    p_sell.add_argument("--symbol", required=True, help="Ticker symbol, e.g. AAPL")
    p_sell.add_argument("--qty", type=float, required=True, help="Quantity (supports fractional if enabled)")
    p_sell.add_argument("--tif", default="DAY", help="Time in force (e.g. DAY, GTC)")
    p_sell.set_defaults(func=cmd_sell)

    # close-position
    p_close = sub.add_parser("close-position", help="Close/open position in a symbol")
    p_close.add_argument("--symbol", required=True, help="Ticker symbol to close")
    p_close.set_defaults(func=cmd_close_position)

    # cancel-order
    p_cancel = sub.add_parser("cancel-order", help="Cancel a single order by ID")
    p_cancel.add_argument("--id", required=True, help="Order ID to cancel")
    p_cancel.set_defaults(func=cmd_cancel_order)

    # cancel-open-orders
    p_cancel_all = sub.add_parser("cancel-open-orders", help="Cancel all open orders")
    p_cancel_all.set_defaults(func=cmd_cancel_open_orders)

    # liquidate
    p_liq = sub.add_parser("liquidate", help="Close all positions and cancel open orders")
    p_liq.set_defaults(func=cmd_liquidate)

    # portfolio-value
    p_val = sub.add_parser("portfolio-value", help="Sum market value of all positions")
    p_val.set_defaults(func=cmd_portfolio_value)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except KeyboardInterrupt:
        print("Interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())