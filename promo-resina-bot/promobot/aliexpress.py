"""Cliente mínimo da AliExpress Affiliate API (Open Platform / IOP)."""
import hashlib
import hmac
import time
from dataclasses import dataclass

import requests

from .config import config

GATEWAY = "https://api-sg.aliexpress.com/sync"


@dataclass
class Product:
    id: str
    title: str
    image: str
    price: float
    original_price: float
    discount: int
    rating: float
    sales: int
    link: str


def _sign(params: dict, secret: str) -> str:
    base = "".join(f"{k}{params[k]}" for k in sorted(params))
    return hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest().upper()


def call(method: str, **biz) -> dict:
    if not (config.ali_app_key and config.ali_app_secret):
        raise RuntimeError("Defina ALI_APP_KEY e ALI_APP_SECRET no .env")
    params = {
        "app_key": config.ali_app_key,
        "method": method,
        "sign_method": "sha256",
        "timestamp": str(int(time.time() * 1000)),
        **{k: str(v) for k, v in biz.items() if v not in (None, "")},
    }
    params["sign"] = _sign(params, config.ali_app_secret)
    resp = requests.post(GATEWAY, data=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error_response" in data:
        raise RuntimeError(f"AliExpress API: {data['error_response']}")
    return data


def _num(value, default=0.0) -> float:
    try:
        return float(str(value).replace("%", "").replace(",", "."))
    except (TypeError, ValueError):
        return default


def _to_product(p: dict) -> Product:
    return Product(
        id=str(p["product_id"]),
        title=p.get("product_title", ""),
        image=p.get("product_main_image_url", ""),
        price=_num(p.get("target_sale_price") or p.get("sale_price")),
        original_price=_num(p.get("target_original_price") or p.get("original_price")),
        discount=int(_num(p.get("discount"))),
        rating=_num(p.get("evaluate_rate")),
        sales=int(_num(p.get("lastest_volume"))),
        link=p.get("promotion_link") or p.get("product_detail_url", ""),
    )


def search(keywords: str, page_size: int = 40, sort: str = "LAST_VOLUME_DESC") -> list[Product]:
    data = call(
        "aliexpress.affiliate.product.query",
        keywords=keywords,
        page_size=page_size,
        sort=sort,
        target_currency="BRL",
        target_language="PT",
        ship_to_country="BR",
        tracking_id=config.ali_tracking_id,
    )
    result = data["aliexpress_affiliate_product_query_response"]["resp_result"].get("result") or {}
    items = (result.get("products") or {}).get("product") or []
    return [_to_product(p) for p in items]


def product_details(product_id: str) -> Product | None:
    data = call(
        "aliexpress.affiliate.productdetail.get",
        product_ids=product_id,
        target_currency="BRL",
        target_language="PT",
        country="BR",
        tracking_id=config.ali_tracking_id,
    )
    result = data["aliexpress_affiliate_productdetail_get_response"]["resp_result"].get("result") or {}
    items = (result.get("products") or {}).get("product") or []
    return _to_product(items[0]) if items else None


def affiliate_link(url: str) -> str:
    """Transforma qualquer link do AliExpress em link de afiliado."""
    data = call(
        "aliexpress.affiliate.link.generate",
        promotion_link_type=0,
        source_values=url,
        tracking_id=config.ali_tracking_id,
    )
    result = data["aliexpress_affiliate_link_generate_response"]["resp_result"]["result"]
    return result["promotion_links"]["promotion_link"][0]["promotion_link"]
