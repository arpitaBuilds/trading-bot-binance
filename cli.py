import argparse
import os
import sys
from decimal import Decimal

from dotenv import load_dotenv
from colorama import init, Fore, Style

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logging, get_logger
from bot.orders import place_order, OrderResult
from bot.validators import validate_all

# Windows pe colors kaam karein
init(autoreset=True)
load_dotenv()

# ── Color helpers ─────────────────────────────────────────────────────────────
def success(text): return f"{Fore.GREEN}{Style.BRIGHT}{text}{Style.RESET_ALL}"
def error(text):   return f"{Fore.RED}{Style.BRIGHT}{text}{Style.RESET_ALL}"
def info(text):    return f"{Fore.CYAN}{text}{Style.RESET_ALL}"
def warn(text):    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
def dim(text):     return f"{Style.DIM}{text}{Style.RESET_ALL}"
def bold(text):    return f"{Style.BRIGHT}{text}{Style.RESET_ALL}"

def hr(char="─", width=58): return dim(char * width)

# ── Output ────────────────────────────────────────────────────────────────────
def print_banner():
    print(f"\n{Fore.CYAN}{Style.BRIGHT}")
    print("  ╔══════════════════════════════════════════╗")
    print("  ║   Binance Futures Testnet Trading Bot    ║")
    print("  ╚══════════════════════════════════════════╝")
    print(Style.RESET_ALL)

def print_summary(symbol, side, order_type, quantity, price, stop_price):
    side_color = Fore.GREEN if side == "BUY" else Fore.RED
    print(f"\n{hr()}")
    print(bold("  📋  ORDER REQUEST SUMMARY"))
    print(hr())
    print(f"  Symbol      : {info(symbol)}")
    print(f"  Side        : {side_color}{Style.BRIGHT}{side}{Style.RESET_ALL}")
    print(f"  Order Type  : {warn(order_type)}")
    print(f"  Quantity    : {quantity}")
    if price:      print(f"  Price       : {price}")
    if stop_price: print(f"  Stop Price  : {stop_price}")
    print(hr())

def print_result(result: OrderResult):
    if result.success:
        print(f"\n{Fore.GREEN}{'═' * 58}{Style.RESET_ALL}")
        print(success("  ✅  ORDER PLACED SUCCESSFULLY"))
        print(f"{Fore.GREEN}{'═' * 58}{Style.RESET_ALL}")
        print(f"  Order ID      : {bold(str(result.order_id))}")
        print(f"  Symbol        : {result.symbol}")
        side_color = Fore.GREEN if result.side == "BUY" else Fore.RED
        print(f"  Side          : {side_color}{result.side}{Style.RESET_ALL}")
        print(f"  Type          : {result.order_type}")
        print(f"  Status        : {warn(result.status or '')}")
        print(f"  Orig Qty      : {result.orig_qty}")
        print(f"  Executed Qty  : {result.executed_qty}")
        if result.avg_price and result.avg_price != "0":
            print(f"  Avg Price     : {success(result.avg_price)}")
        if result.price and result.price != "0":
            print(f"  Limit Price   : {result.price}")
        print(f"{Fore.GREEN}{'═' * 58}{Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.RED}{'═' * 58}{Style.RESET_ALL}")
        print(error("  ❌  ORDER FAILED"))
        print(f"{Fore.RED}{'═' * 58}{Style.RESET_ALL}")
        print(f"  {error(result.error or 'Unknown error')}")
        print(f"{Fore.RED}{'═' * 58}{Style.RESET_ALL}\n")

# ── Client factory ────────────────────────────────────────────────────────────
def build_client() -> BinanceFuturesClient:
    api_key    = os.environ.get("BINANCE_API_KEY", "").strip()
    api_secret = os.environ.get("BINANCE_API_SECRET", "").strip()
    if not api_key or not api_secret:
        print(error("\n  ⚠  API credentials missing!"))
        print(info("  .env file mein BINANCE_API_KEY aur BINANCE_API_SECRET set karo\n"))
        sys.exit(1)
    return BinanceFuturesClient(api_key=api_key, api_secret=api_secret)

# ── Commands ──────────────────────────────────────────────────────────────────
def cmd_order(args):
    logger = get_logger("cli")
    try:
        params = validate_all(
            symbol=args.symbol, side=args.side, order_type=args.type,
            quantity=args.quantity, price=args.price, stop_price=args.stop_price,
        )
    except ValueError as e:
        print(error(f"\n  ❌  Validation Error: {e}\n"))
        logger.error("Validation error: %s", e)
        sys.exit(1)

    print_summary(**params)
    client = build_client()
    result = place_order(client=client, **params,
                         time_in_force=args.time_in_force,
                         reduce_only=args.reduce_only)
    print_result(result)
    sys.exit(0 if result.success else 1)

def cmd_open_orders(args):
    client = build_client()
    symbol = args.symbol.upper() if args.symbol else None
    orders = client.get_open_orders(symbol=symbol)
    print(f"\n{hr()}")
    print(bold(f"  📂  Open Orders{' — ' + symbol if symbol else ''} ({len(orders)} found)"))
    print(hr())
    if not orders:
        print(dim("  Koi open orders nahi hain."))
    for o in orders:
        side_color = Fore.GREEN if o.get("side") == "BUY" else Fore.RED
        print(f"  [{bold(str(o.get('orderId')))}]  "
              f"{o.get('symbol')}  "
              f"{side_color}{o.get('side')}{Style.RESET_ALL}  "
              f"{o.get('type')}  qty={o.get('origQty')}  "
              f"price={o.get('price')}  {warn(o.get('status', ''))}")
    print()

def cmd_cancel(args):
    client = build_client()
    try:
        r = client.cancel_order(symbol=args.symbol.upper(), order_id=args.order_id)
        print(success(f"\n  ✅  Order {r.get('orderId')} cancelled. Status: {r.get('status')}\n"))
    except Exception as e:
        print(error(f"\n  ❌  Cancel failed: {e}\n"))
        sys.exit(1)

def cmd_interactive(_args):
    print_banner()
    print(bold("  Guided mode — sab kuch step by step poochha jayega\n"))

    def ask(label, default=""):
        hint = f" [{default}]" if default else ""
        val = input(f"  {label}{hint}: ").strip()
        return val if val else default

    symbol     = ask("Symbol (e.g. BTCUSDT)", "BTCUSDT").upper()
    side       = ask("Side — BUY ya SELL", "BUY").upper()
    order_type = ask("Order Type (MARKET / LIMIT / STOP_MARKET / STOP)", "MARKET").upper()
    quantity   = ask("Quantity", "0.001")
    price      = ask("Limit Price (LIMIT/STOP ke liye)") or None
    stop_price = ask("Stop Trigger Price (STOP/STOP_MARKET ke liye)") or None

    try:
        params = validate_all(symbol, side, order_type, quantity, price, stop_price)
    except ValueError as e:
        print(error(f"\n  ❌  {e}\n"))
        sys.exit(1)

    print_summary(**params)
    confirm = input(warn("  Confirm karein? [y/N]: ")).strip().lower()
    if confirm not in {"y", "yes"}:
        print(dim("  Cancelled.\n"))
        sys.exit(0)

    client = build_client()
    result = place_order(client=client, **params)
    print_result(result)
    sys.exit(0 if result.success else 1)

# ── Parser ────────────────────────────────────────────────────────────────────
def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot",
        epilog="""
Examples:
  python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  python cli.py order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 90000
  python cli.py order --symbol BTCUSDT --side SELL --type STOP --quantity 0.001 --price 68000 --stop-price 68500
  python cli.py open-orders --symbol BTCUSDT
  python cli.py cancel --symbol BTCUSDT --order-id 12345
  python cli.py interactive
        """
    )
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    sub = parser.add_subparsers(dest="command", required=True)

    # order
    p = sub.add_parser("order", help="Naya order place karo")
    p.add_argument("--symbol",      required=True)
    p.add_argument("--side",        required=True, choices=["BUY", "SELL"])
    p.add_argument("--type",        required=True, dest="type",
                   choices=["MARKET", "LIMIT", "STOP_MARKET", "STOP"])
    p.add_argument("--quantity",    required=True)
    p.add_argument("--price",       default=None)
    p.add_argument("--stop-price",  default=None, dest="stop_price")
    p.add_argument("--time-in-force", default="GTC", dest="time_in_force",
                   choices=["GTC", "IOC", "FOK"])
    p.add_argument("--reduce-only", action="store_true", dest="reduce_only")
    p.set_defaults(func=cmd_order)

    # open-orders
    p2 = sub.add_parser("open-orders", help="Open orders dekho")
    p2.add_argument("--symbol", default=None)
    p2.set_defaults(func=cmd_open_orders)

    # cancel
    p3 = sub.add_parser("cancel", help="Order cancel karo")
    p3.add_argument("--symbol",   required=True)
    p3.add_argument("--order-id", required=True, type=int, dest="order_id")
    p3.set_defaults(func=cmd_cancel)

    # interactive
    p4 = sub.add_parser("interactive", help="Guided mode (bonus)")
    p4.set_defaults(func=cmd_interactive)

    return parser

def main():
    parser = build_parser()
    args   = parser.parse_args()
    setup_logging(log_level=args.log_level)
    args.func(args)

if __name__ == "__main__":
    main()