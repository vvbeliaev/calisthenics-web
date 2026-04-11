"""Prodamus helpers: build signed payment URL + verify webhook signature.

Signature algorithm (both directions):
  1. Convert all values to strings
  2. Sort all keys alphabetically, recursively (deep sort)
  3. JSON encode with compact separators
  4. Escape / as \/ (PHP json_encode default — Python omits this step by default)
  5. HMAC-SHA256 with secret key
"""

import hashlib
import hmac
import json
import re
import urllib.parse
from datetime import datetime

import httpx


# ── signature internals ───────────────────────────────────────────────────────


def _unflatten(flat: dict[str, str]) -> dict:
    """Convert PHP bracket-notation flat dict to nested dict/list.

    PHP's $_POST parses "products[0][name]=X" into {"products": [{"name": "X"}]}.
    Prodamus signs the nested structure, so we must reconstruct it before verifying.
    """

    def insert(node: dict | list, parts: list[str], value: str) -> None:
        part = parts[0]
        rest = parts[1:]
        if not rest:
            if isinstance(node, list):
                node.append(value)
            else:
                node[part] = value
            return
        is_next_list = rest[0].isdigit()
        if isinstance(node, list):
            idx = int(part)
            while len(node) <= idx:
                node.append([] if is_next_list else {})
            insert(node[idx], rest, value)
        else:
            if part not in node:
                node[part] = [] if is_next_list else {}
            insert(node[part], rest, value)

    result: dict = {}
    for key, value in flat.items():
        parts = re.findall(r"[^\[\]]+", key)
        insert(result, parts, value)
    return result


def _to_strings(data: object) -> object:
    if isinstance(data, dict):
        return {k: _to_strings(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_to_strings(v) for v in data]
    return str(data)


def _sort_recursive(data: object) -> object:
    if isinstance(data, dict):
        return {k: _sort_recursive(v) for k, v in sorted(data.items())}
    if isinstance(data, list):
        return [_sort_recursive(v) for v in data]
    return data


def _sign(data: dict, secret: str) -> str:
    prepared = _sort_recursive(_to_strings(data))
    payload = json.dumps(prepared, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("/", "\\/")
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


# ── URL builder ───────────────────────────────────────────────────────────────


def _flatten(data: dict, prefix: str = "") -> dict[str, str]:
    """Flatten nested dict to PHP-style bracket notation for URL encoding.

    {"products": [{"name": "X"}]} → {"products[0][name]": "X"}
    """
    result: dict[str, str] = {}
    for key, value in data.items():
        full_key = f"{prefix}[{key}]" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten(value, full_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                item_key = f"{full_key}[{i}]"
                if isinstance(item, dict):
                    result.update(_flatten(item, item_key))
                else:
                    result[item_key] = str(item)
        else:
            result[full_key] = str(value)
    return result


async def build_payment_url(
    tg_id: int,
    product: dict,
    webhook_base_url: str,
    secret: str,
) -> str:
    """Request a signed Prodamus subscription payment link.

    Makes a GET to the payform URL with subscription params — Prodamus returns
    the short payment URL as plain text (e.g. https://payform.ru/rsb83xl/).
    order_id encodes tg_id + product_id; returned in webhook as order_num.
    _param_telegram_id is a pass-through param returned in the webhook.
    """
    order_id = f"tg_{tg_id}_{product['product_id']}_{int(datetime.now().timestamp())}"
    data: dict = {
        "do": "link",
        "order_id": order_id,
        "subscription": str(product["subscription_id"]),
        "_param_telegram_id": str(tg_id),
        "urlSuccess": f"{webhook_base_url}/payment/success",
        "urlNotification": f"{webhook_base_url}/payment/webhook",
    }
    data["signature"] = _sign(data, secret)
    url = f"{product['prodamus_url']}?{urllib.parse.urlencode(_flatten(data))}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text.strip()


async def build_onetime_payment_url(
    tg_id: int,
    name: str,
    price: int | None,
    prodamus_url: str,
    webhook_base_url: str,
    secret: str,
    order_prefix: str,
) -> str:
    """Request a signed Prodamus one-time payment link.

    price=None means no fixed price (user enters amount on payment page).
    order_prefix is used to distinguish payment types in order_id (e.g. 'training', 'tip').
    """
    order_id = f"tg_{tg_id}_{order_prefix}_{int(datetime.now().timestamp())}"
    product_entry: dict = {"name": name, "quantity": "1"}
    if price is not None:
        product_entry["price"] = str(price)
    data: dict = {
        "do": "link",
        "order_id": order_id,
        "products": [product_entry],
        "_param_telegram_id": str(tg_id),
        "urlSuccess": f"{webhook_base_url}/payment/success",
        "urlNotification": f"{webhook_base_url}/payment/webhook",
    }
    data["signature"] = _sign(data, secret)
    url = f"{prodamus_url}?{urllib.parse.urlencode(_flatten(data))}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text.strip()


# ── webhook signature verification ────────────────────────────────────────────


def verify_signature(
    post_data: dict[str, str], secret: str, incoming_sign: str
) -> bool:
    """Verify Prodamus webhook HMAC-SHA256 signature.

    Webhook POST fields are already flat strings — just sort, JSON-encode
    (with / escaping), and compare HMAC.
    """
    if not secret or not incoming_sign:
        return False
    return hmac.compare_digest(
        _sign(_unflatten(post_data), secret).lower(),
        incoming_sign.lower(),
    )
