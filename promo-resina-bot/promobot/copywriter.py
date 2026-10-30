"""Gera o título curto e a frase de destaque (com IA opcional)."""
import re

from .aliexpress import Product
from .config import config

NOISE = re.compile(
    r"\b(19[0-9]{2}|20[0-9]{2}|new|novo|hot|sale|free shipping|frete grátis|for|para)\b", re.I
)


def short_title(title: str, limit: int = 70) -> str:
    t = re.sub(r"\s+", " ", NOISE.sub("", title)).strip(" -,|")
    return t if len(t) <= limit else t[:limit].rsplit(" ", 1)[0] + "…"


def _fallback_tagline(p: Product) -> str:
    if p.discount >= 50:
        return f"Metade do preço ou menos! {p.discount}% OFF numa resina com {p.sales}+ vendas."
    if p.rating >= 95:
        return f"Resina super bem avaliada ({p.rating:.0f}% positivas) com {p.discount}% de desconto."
    return f"{p.discount}% OFF — ótima oportunidade pra repor o estoque de resina."


def tagline(p: Product) -> str:
    if not config.use_ai_copy:
        return _fallback_tagline(p)
    try:
        import anthropic

        client = anthropic.Anthropic()
        response = client.beta.messages.create(
            model=config.ai_model,
            max_tokens=1024,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=(
                "Você escreve chamadas para um canal de promoções de impressão 3D no WhatsApp. "
                "Responda só com UMA frase em português do Brasil, até 140 caracteres, sem emojis, "
                "sem preço e sem link. Destaque o benefício prático da resina (acabamento, cheiro, "
                "lavável em água, resistência, cor etc.) a partir do título do produto. "
                "Não invente características que não estejam no título."
            ),
            messages=[{"role": "user", "content": f"Produto: {p.title}"}],
        )
        if response.stop_reason == "refusal":
            return _fallback_tagline(p)
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        return text or _fallback_tagline(p)
    except Exception as e:
        print(f"[ia] usando texto padrão: {e}")
        return _fallback_tagline(p)
