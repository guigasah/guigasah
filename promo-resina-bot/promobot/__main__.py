"""Agente de promoções de resina 3D do AliExpress para WhatsApp.

Uso:
  python -m promobot run                     # busca e posta as melhores promoções agora
  python -m promobot loop                    # roda sozinho a cada INTERVAL_MINUTES
  python -m promobot link URL [--cupom X]    # posta um produto específico (seu achado manual)
  python -m promobot grupos                  # lista os IDs dos grupos do seu WhatsApp
  python -m promobot demo                    # gera um post de exemplo sem precisar de chaves
"""
import argparse
import re
import time
from datetime import datetime
from pathlib import Path

from . import aliexpress, copywriter, storage, whatsapp
from .aliexpress import Product
from .card import make_card
from .config import config
from .message import build_caption
from .selector import find_deals


def post(p: Product, coupon: str | None = None) -> None:
    title = copywriter.short_title(p.title)
    caption = build_caption(p, title, copywriter.tagline(p), coupon)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    image = make_card(p, str(Path(config.output_dir) / f"{stamp}-{p.id}.jpg"))
    whatsapp.send(image, caption)
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


def post_link(url: str, coupon: str | None) -> None:
    m = re.search(r"/item/(\d+)", url) or re.search(r"(\d{10,})", url)
    if not m:
        raise SystemExit("Não achei o ID do produto no link. Use o link completo .../item/123456.html")
    p = aliexpress.product_details(m.group(1))
    if not p:
        raise SystemExit("Produto não encontrado na API de afiliados (pode não ter comissão).")
    if not p.link:
        p.link = aliexpress.affiliate_link(url)
    post(p, coupon)


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
    lk = sub.add_parser("link")
    lk.add_argument("url")
    lk.add_argument("--cupom")
    args = ap.parse_args()

    if args.cmd == "run":
        run_once()
    elif args.cmd == "loop":
        loop()
    elif args.cmd == "link":
        post_link(args.url, args.cupom)
    elif args.cmd == "grupos":
        for g in whatsapp.list_groups():
            print(f"{g.get('id')}  {g.get('subject')}")
    elif args.cmd == "demo":
        demo()


if __name__ == "__main__":
    main()
