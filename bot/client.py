import hashlib
import hmac
import time
from decimal import Decimal
from typing import Any, Optional
from urllib.parse import urlencode

import requests

from bot.logging_config import get_logger

logger = get_logger("client")
TESTNET_BASE_URL = "https://testnet.binancefuture.com"

class BinanceAPIError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")

class BinanceNetworkError(Exception):
    pass

class BinanceFuturesClient:
    def __init__(self, api_key: str, api_secret: str,
                 base_url: str = TESTNET_BASE_URL, timeout: int = 10):
        if not api_key or not api_secret:
            raise ValueError("API key aur secret dono required hain.")
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "X-MBX-APIKEY": self._api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })
        logger.debug("Client ready. Base URL: %s", self._base_url)

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._signed_get("/fapi/v1/openOrders", params)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        return self._signed_delete("/fapi/v1/order", {"symbol": symbol, "orderId": order_id})

    def new_order(self, symbol, side, order_type, quantity: Decimal,
                  price=None, stop_price=None, time_in_force="GTC", reduce_only=False) -> dict:
        params: dict[str, Any] = {
            "symbol":   symbol,
            "side":     side,
            "type":     order_type,
            "quantity": str(quantity),
        }
        if order_type == "LIMIT":
            params["price"] = str(price)
            params["timeInForce"] = time_in_force
        if order_type == "STOP":
            params["price"] = str(price)
            params["stopPrice"] = str(stop_price)
            params["timeInForce"] = time_in_force
        if order_type == "STOP_MARKET":
            params["stopPrice"] = str(stop_price)
        if reduce_only:
            params["reduceOnly"] = "true"

        logger.info("Placing order: %s %s %s qty=%s price=%s stop=%s",
                    symbol, side, order_type, quantity, price, stop_price)
        response = self._signed_post("/fapi/v1/order", params)
        logger.info("Order placed! orderId=%s status=%s",
                    response.get("orderId"), response.get("status"))
        return response

    # ── private helpers ──────────────────────────────────────────────

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, query_string: str) -> str:
        return hmac.new(
            self._api_secret.encode("utf-8"),
            msg=query_string.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

    def _get(self, path, params=None):
        url = self._base_url + path
        logger.debug("GET %s params=%s", url, params)
        try:
            resp = self._session.get(url, params=params, timeout=self._timeout)
        except requests.exceptions.Timeout:
            raise BinanceNetworkError(f"Timeout: GET {url}")
        except requests.exceptions.ConnectionError as e:
            raise BinanceNetworkError(f"Connection error: {e}")
        return self._handle_response(resp)

    def _signed_get(self, path, params=None):
        params = dict(params or {})
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = 5000
        params["signature"] = self._sign(urlencode(params))
        return self._get(path, params)

    def _signed_post(self, path, params):
        params = dict(params)
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = 5000
        params["signature"] = self._sign(urlencode(params))
        url = self._base_url + path
        logger.debug("POST %s body=%s", url,
                     {k: v for k, v in params.items() if k != "signature"})
        try:
            resp = self._session.post(url, data=params, timeout=self._timeout)
        except requests.exceptions.Timeout:
            raise BinanceNetworkError(f"Timeout: POST {url}")
        except requests.exceptions.ConnectionError as e:
            raise BinanceNetworkError(f"Connection error: {e}")
        return self._handle_response(resp)

    def _signed_delete(self, path, params):
        params = dict(params)
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = 5000
        params["signature"] = self._sign(urlencode(params))
        url = self._base_url + path
        try:
            resp = self._session.delete(url, params=params, timeout=self._timeout)
        except requests.exceptions.Timeout:
            raise BinanceNetworkError(f"Timeout: DELETE {url}")
        except requests.exceptions.ConnectionError as e:
            raise BinanceNetworkError(f"Connection error: {e}")
        return self._handle_response(resp)

    @staticmethod
    def _handle_response(resp: requests.Response):
        logger.debug("Response %s: %s", resp.status_code, resp.text[:500])
        try:
            data = resp.json()
        except ValueError:
            raise BinanceAPIError(resp.status_code, f"Non-JSON: {resp.text[:200]}")
        if resp.status_code >= 400 or (isinstance(data, dict) and data.get("code", 0) < 0):
            raise BinanceAPIError(data.get("code", resp.status_code), data.get("msg", resp.text))
        return data