"""Agente de promoções de resina 3D do AliExpress para WhatsApp.

Uso:
  python -m promobot run                     # busca e posta as melhores promoções agora
  python -m promobot loop                    # roda sozinho a cada INTERVAL_MINUTES
  python -m promobot link URL [--cupom X]    # posta um produto específico (seu achado manual)
      [--preco 99.9 --preco-antigo 150]      # sem API: título e fotos são lidos do anúncio
      [--titulo T --imagem foto.jpg]         # opcional: sobrescreve o que veio do anúncio
  python -m promobot grupos                  # lista os IDs dos grupos do seu WhatsApp
  python -m promobot demo                    # gera um post de exemplo sem precisar de chaves
  python -m promobot testar-api              # confere se as chaves do AliExpress funcionam
"""
import argparse
import re
import time
from datetime import datetime
from pathlib import Path

import requests

from . import aliexpress, copywriter, storage, whatsapp
from .aliexpress import Product
from .card import download_photo, make_card
from .config import config
from .message import build_caption
from .scraper import scrape_listing
from .selector import find_deals


def post(p: Product, coupon: str | None = None) -> None:
    title = copywriter.short_title(p.title)
    caption = build_caption(p, title, copywriter.tagline(p), coupon)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = Path(config.output_dir) / f"{stamp}-{p.id}"
    image = make_card(p, f"{base}.jpg")
    whatsapp.send(image, caption)
    # fotos extras do anúncio, sem legenda, logo depois do post
    for i, url in enumerate(p.images[1 : 1 + config.extra_photos], start=1):
        try:
            whatsapp.send(download_photo(url, f"{base}-foto{i}.jpg"), "")
        except Exception as e:
            print(f"[fotos] não enviei {url}: {e}")
    storage.mark_posted(p.id, p.price)


def run_once() -> None:
    deals = find_deals()
    print(f"[agente] {len(deals)} promoção(ões) nova(s)")
    for i, p in enumerate(deals):
        if i:
            time.sleep(60)  # espaça os posts no canal
        try:
            post(p)
        except Exception as e:
            print(f"[agente] falha ao postar {p.id}: {e}")


def _quiet_now() -> bool:
    try:
        start, end = (int(x) for x in config.quiet_hours.split("-"))
    except ValueError:
        return False
    h = datetime.now().hour
    return start <= h or h < end if start > end else start <= h < end


def loop() -> None:
    while True:
        if _quiet_now():
            print("[agente] horário silencioso, pulando")
        else:
            try:
                run_once()
            except Exception as e:
                print(f"[agente] erro: {e}")
        time.sleep(config.interval_minutes * 60)


def _product_id(url: str) -> str | None:
    m = re.search(r"/item/(\d+)", url) or re.search(r"(\d{10,})", url)
    if m:
        return m.group(1)
    try:  # link curto (s.click.aliexpress.com / a.aliexpress.com): segue o redirecionamento
        final = requests.get(url, allow_redirects=True, timeout=20).url
    except requests.RequestException as e:
        print(f"[link] não consegui abrir {url}: {e}")
        return None
    m = re.search(r"/item/(\d+)", final) or re.search(r"productIds?=(\d+)", final)
    return m.group(1) if m else None


def _listing(url: str) -> dict:
    try:
        return scrape_listing(url)
    except Exception as e:
        print(f"[link] não consegui ler o anúncio para pegar as fotos: {e}")
        return {"url": url, "title": "", "images": []}


def post_link(url: str, coupon: str | None, manual: dict) -> None:
    """Posta um achado seu. Com --preco funciona sem API: título e fotos vêm do anúncio."""
    if manual.get("price"):
        page = _listing(url)
        title = manual.get("title") or page["title"]
        if not title:
            raise SystemExit("Não consegui ler o título do anúncio. Informe --titulo.")
        images = [manual["image"]] if manual.get("image") else page["images"]
        p = Product(
            id=_product_id(page["url"]) or re.sub(r"\W+", "", url)[-10:], title=title,
            image=images[0] if images else "", images=images,
            price=manual["price"], original_price=manual.get("original_price") or 0,
            discount=0, rating=0, sales=0, link=url,
        )
        if p.original_price > p.price:
            p.discount = round(100 - p.price / p.original_price * 100)
        post(p, coupon)
        return
    pid = _product_id(url)
    if not pid:
        raise SystemExit("Não achei o ID do produto. Informe --preco para postar sem a API.")
    p = aliexpress.product_details(pid)
    if not p:
        raise SystemExit("Produto não encontrado na API de afiliados (pode não ter comissão).")
    if len(p.images) < 2:  # API trouxe poucas fotos: completa com as do anúncio
        p.images = list(dict.fromkeys(p.images + _listing(url)["images"]))
    # link que você já gerou continua sendo o usado (mantém seu rastreio)
    p.link = url if "s.click.aliexpress.com" in url else (p.link or aliexpress.affiliate_link(url))
    post(p, coupon)


def test_api() -> None:
    """Confere as chaves do .env fazendo uma busca real, sem postar nada."""
    missing = [n for n, v in [("ALI_APP_KEY", config.ali_app_key), ("ALI_APP_SECRET", config.ali_app_secret),
                              ("ALI_TRACKING_ID", config.ali_tracking_id)] if not v]
    if missing:
        raise SystemExit(f"Faltando no .env: {', '.join(missing)}")
    kw = config.keywords[0]
    try:
        products = aliexpress.search(kw, page_size=5)
    except Exception as e:
        raise SystemExit(f"❌ A API recusou: {e}")
    print(f"✅ Conectado! {len(products)} resultado(s) para '{kw}':")
    for p in products:
        link = "link de afiliado OK" if "s.click" in p.link else "SEM link de afiliado (confira o Tracking ID)"
        print(f"  R${p.price:.2f} (-{p.discount}%) {p.title[:60]} | {len(p.images)} foto(s) | {link}")


def demo() -> None:
    p = Product(
        id="demo",
        title="ELEGOO Resina Padrão 8K 1kg Lavável em Água Cinza Para Impressora 3D LCD 405nm",
        image=str(Path(__file__).resolve().parent.parent / "assets" / "demo-resina.png"),
        price=89.90, original_price=159.90, discount=44, rating=97.5, sales=1200,
        link="https://s.click.aliexpress.com/e/_exemplo",
    )
    config.provider = "dryrun"
    post(p, coupon="RESINA10")


def main() -> None:
    ap = argparse.ArgumentParser(prog="promobot", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run")
    sub.add_parser("loop")
    sub.add_parser("grupos")
    sub.add_parser("demo")
    sub.add_parser("testar-api")
    lk = sub.add_parser("link")
    lk.add_argument("url")
    lk.add_argument("--cupom")
    lk.add_argument("--titulo", help="título (padrão: o do anúncio)")
    lk.add_argument("--preco", type=float, help="preço atual em R$")
    lk.add_argument("--preco-antigo", type=float, help="preço sem desconto em R$")
    lk.add_argument("--imagem", help="URL ou arquivo da foto (padrão: fotos do anúncio)")
    args = ap.parse_args()

    if args.cmd == "run":
        run_once()
    elif args.cmd == "loop":
        loop()
    elif args.cmd == "link":
        post_link(args.url, args.cupom, {
            "title": args.titulo, "price": args.preco,
            "original_price": args.preco_antigo, "image": args.imagem,
        })
    elif args.cmd == "grupos":
        for g in whatsapp.list_groups():
            print(f"{g.get('id')}  {g.get('subject')}")
    elif args.cmd == "demo":
        demo()
    elif args.cmd == "testar-api":
        test_api()


if __name__ == "__main__":
    main()
