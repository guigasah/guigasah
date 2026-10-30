"""Busca e escolhe as melhores promoções de resina 3D."""
import re

from . import aliexpress, storage
from .aliexpress import Product
from .config import config

RESIN = re.compile(r"resin|resina", re.I)
PRINT_3D = re.compile(
    r"3d|uv|405|lcd|dlp|msla|sla|printer|impressora|elegoo|anycubic|sunlu|phrozen|esun|siraya|jamghe|creality",
    re.I,
)
EXCLUDE = re.compile(r"epox|epóx|molde|mold|bijou|jewel|art resin", re.I)


def is_3d_resin(p: Product) -> bool:
    return bool(RESIN.search(p.title) and PRINT_3D.search(p.title) and not EXCLUDE.search(p.title))


def passes_filters(p: Product) -> bool:
    return (
        is_3d_resin(p)
        and 0 < p.price <= config.max_price
        and p.discount >= config.min_discount
        and (config.min_rating == 0 or p.rating >= config.min_rating)
        and p.sales >= config.min_sales
        and bool(p.link)
    )


def score(p: Product) -> float:
    # desconto pesa mais; vendas e avaliação desempatam
    return p.discount * 2 + min(p.sales, 1000) / 50 + p.rating / 10


def find_deals() -> list[Product]:
    seen: dict[str, Product] = {}
    for kw in config.keywords:
        try:
            for p in aliexpress.search(kw):
                seen.setdefault(p.id, p)
        except Exception as e:  # uma palavra-chave falhar não derruba as outras
            print(f"[busca] '{kw}' falhou: {e}")
    deals = [p for p in seen.values() if passes_filters(p) and storage.can_post(p.id, p.price)]
    deals.sort(key=score, reverse=True)
    return deals[: config.posts_per_run]
