from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET", "STOP"}

def validate_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not symbol or not symbol.isalnum():
        raise ValueError(f"Invalid symbol '{symbol}'. Example: BTCUSDT")
    return symbol

def validate_side(side: str) -> str:
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Side must be BUY or SELL, got '{side}'")
    return side

def validate_order_type(order_type: str) -> str:
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(f"Order type must be one of: {', '.join(VALID_ORDER_TYPES)}")
    return order_type

def validate_quantity(quantity: str) -> Decimal:
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}'")
    if qty <= 0:
        raise ValueError(f"Quantity must be > 0, got {qty}")
    return qty

def validate_price(price: Optional[str], order_type: str) -> Optional[Decimal]:
    if order_type in {"LIMIT", "STOP"}:
        if price is None:
            raise ValueError(f"--price is required for {order_type} orders")
        try:
            p = Decimal(str(price))
        except InvalidOperation:
            raise ValueError(f"Invalid price '{price}'")
        if p <= 0:
            raise ValueError(f"Price must be > 0")
        return p
    return None

def validate_stop_price(stop_price: Optional[str], order_type: str) -> Optional[Decimal]:
    if order_type in {"STOP", "STOP_MARKET"}:
        if stop_price is None:
            raise ValueError(f"--stop-price is required for {order_type} orders")
        try:
            sp = Decimal(str(stop_price))
        except InvalidOperation:
            raise ValueError(f"Invalid stop price '{stop_price}'")
        if sp <= 0:
            raise ValueError(f"Stop price must be > 0")
        return sp
    return None

def validate_all(symbol, side, order_type, quantity, price=None, stop_price=None) -> dict:
    return {
        "symbol":     validate_symbol(symbol),
        "side":       validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity":   validate_quantity(quantity),
        "price":      validate_price(price, order_type.upper()),
        "stop_price": validate_stop_price(stop_price, order_type.upper()),
    }