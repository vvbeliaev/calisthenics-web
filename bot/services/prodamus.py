"""Prodamus helpers: build payment URL + verify webhook signature."""

import hashlib
import hmac
import json
import urllib.parse
from datetime import datetime


def build_payment_url(
    tg_id: int,
    product: dict,
    webhook_base_url: str,
    secret: str,
) -> str:
    """Генерирует ссылку на платёжную форму Prodamus.

    tg_id и product_id кодируются в order_id — вебхук их потом парсит из order_num.
    urlNotification не передаётся — вебхук настраивается статически в кабинете Prodamus.
    """
    order_id = f"tg_{tg_id}_{product['product_id']}_{int(datetime.utcnow().timestamp())}"
    params = {
        "order_id": order_id,
        "urlSuccess": f"{webhook_base_url}/payment/success",
    }
    base = product["prodamus_url"]
    sep = "&" if "?" in base else "?"
    return base + sep + urllib.parse.urlencode(params)


def verify_signature(post_data: dict[str, str], secret: str, incoming_sign: str) -> bool:
    """Проверяет HMAC-SHA256 подпись вебхука Prodamus.

    Prodamus подписывает POST-данные: сортирует ключи алфавитно,
    конвертирует в JSON-строку, затем HMAC-SHA256 с секретным ключом.
    """
    if not secret or not incoming_sign:
        return False
    sorted_data = dict(sorted(post_data.items()))
    payload = json.dumps(sorted_data, ensure_ascii=False, separators=(",", ":"))
    expected = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected.lower(), incoming_sign.lower())
