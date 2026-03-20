from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from bot.client import BinanceFuturesClient, BinanceAPIError, BinanceNetworkError
from bot.logging_config import get_logger

logger = get_logger("orders")

@dataclass
class OrderResult:
    success: bool
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    price: Optional[str] = None
    avg_price: Optional[str] = None
    orig_qty: Optional[str] = None
    executed_qty: Optional[str] = None
    time_in_force: Optional[str] = None
    raw: dict = field(default_factory=dict)
    error: Optional[str] = None

    @classmethod
    def from_response(cls, data: dict) -> "OrderResult":
        return cls(
            success=True,
            order_id=data.get("orderId"),
            client_order_id=data.get("clientOrderId"),
            symbol=data.get("symbol"),
            side=data.get("side"),
            order_type=data.get("type"),
            status=data.get("status"),
            price=data.get("price"),
            avg_price=data.get("avgPrice"),
            orig_qty=data.get("origQty"),
            executed_qty=data.get("executedQty"),
            time_in_force=data.get("timeInForce"),
            raw=data,
        )

    @classmethod
    def from_error(cls, error: str) -> "OrderResult":
        return cls(success=False, error=error)


def place_order(client: BinanceFuturesClient, symbol, side, order_type,
                quantity: Decimal, price=None, stop_price=None,
                time_in_force="GTC", reduce_only=False) -> OrderResult:
    logger.info("Submitting: %s %s %s qty=%s", symbol, side, order_type, quantity)
    try:
        response = client.new_order(
            symbol=symbol, side=side, order_type=order_type,
            quantity=quantity, price=price, stop_price=stop_price,
            time_in_force=time_in_force, reduce_only=reduce_only,
        )
        result = OrderResult.from_response(response)
        logger.info("Success: orderId=%s status=%s executedQty=%s avgPrice=%s",
                    result.order_id, result.status, result.executed_qty, result.avg_price)
        return result
    except BinanceAPIError as e:
        msg = f"API error [{e.code}]: {e.message}"
        logger.error(msg)
        return OrderResult.from_error(msg)
    except BinanceNetworkError as e:
        msg = f"Network error: {e}"
        logger.error(msg)
        return OrderResult.from_error(msg)
    except Exception as e:
        msg = f"Unexpected error: {e}"
        logger.exception(msg)
        return OrderResult.from_error(msg)