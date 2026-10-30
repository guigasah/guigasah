"""Monta a legenda no estilo dos canais de promoção."""
from .aliexpress import Product
from .config import config


def _brl(v: float) -> str:
    return f"R${v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_caption(p: Product, title: str, tagline: str, coupon: str | None = None) -> str:
    lines = [f"🔥 *{title}*", "", f"_{tagline}_", ""]
    if coupon:
        lines += ["🎟️ *Use o cupom:*", f"```{coupon}```", ""]
    price = f"- *Preço:* {_brl(p.price)}"
    if p.original_price > p.price:
        price += f" ~{_brl(p.original_price)}~ ({p.discount}% OFF)"
    lines += [price, "- *Loja:* AliExpress", "", f"- *Link de compra:* {p.link}"]
    if config.groups_link:
        lines += ["", "*Entre nos Grupos*", config.groups_link]
    lines += ["", "_Preço sujeito a alteração a qualquer momento._"]
    return "\n".join(lines)
