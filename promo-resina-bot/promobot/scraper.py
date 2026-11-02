"""Lê título e fotos direto da página do anúncio (quando não há API ou para completar dados)."""
import json
import re

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def _clean(url: str) -> str:
    url = url.replace("\\u002F", "/").replace("\\/", "/")
    if url.startswith("//"):
        url = "https:" + url
    # remove o sufixo de miniatura (_220x220.jpg etc.) para pegar a foto grande
    return re.sub(r"(\.(?:jpg|jpeg|png|webp))_\d+x\d+.*$", r"\1", url, flags=re.I)


def scrape_listing(url: str) -> dict:
    """Retorna {"url", "title", "images"} a partir do link do anúncio (curto ou completo)."""
    resp = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=30)
    resp.raise_for_status()
    html = resp.text
    images: list[str] = []

    m = re.search(r'"imagePathList"\s*:\s*(\[[^\]]*\])', html)
    if m:
        try:
            images += json.loads(m.group(1))
        except ValueError:
            pass
    images += re.findall(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
    if not images:  # último recurso: fotos do CDN do AliExpress na página
        images += re.findall(r'(?:https?:)?//ae0\d\.alicdn\.com/kf/[^"\'\s]+?\.(?:jpg|jpeg|png|webp)', html)

    title = ""
    t = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', html) or re.search(
        r"<title>(.*?)</title>", html, re.S
    )
    if t:
        title = re.sub(r"\s*[-|]\s*AliExpress.*$", "", t.group(1)).strip()

    return {
        "url": resp.url,
        "title": title,
        "images": list(dict.fromkeys(_clean(u) for u in images if u)),
    }
