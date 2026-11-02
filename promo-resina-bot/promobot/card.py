"""Gera a arte 1000x900 do post (faixa da marca + foto do produto + preço)."""
import io
import os
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from .aliexpress import Product
from .config import config

W, H, BAR = 1000, 900, 120
FONT_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGO = ASSETS / "logo.png"
FRAME = ASSETS / "moldura.png"  # arte pronta da marca; o produto é colado por cima
CUSTOM_FONT = ASSETS / "fonte.ttf"


def _font(size: int):
    for path in [CUSTOM_FONT, *FONT_BOLD]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def _centered(draw, cx, y, text, font, fill):
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def _brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _photo(p: Product, box: tuple[int, int]):
    try:
        if os.path.exists(p.image):
            photo = Image.open(p.image).convert("RGB")
        else:
            photo = Image.open(io.BytesIO(requests.get(p.image, timeout=30).content)).convert("RGB")
        photo.thumbnail(box)
        return photo
    except Exception as e:
        print(f"[card] sem imagem do produto: {e}")
        return None


def _framed_card(p: Product) -> Image.Image:
    """Usa assets/moldura.png e cola a foto em CARD_PHOTO_BOX (x1,y1,x2,y2)."""
    img = Image.open(FRAME).convert("RGB")
    x1, y1, x2, y2 = config.card_photo_box or (
        int(img.width * 0.2), int(img.height * 0.2), int(img.width * 0.8), int(img.height * 0.82)
    )
    d = ImageDraw.Draw(img)
    price_h = 120 if config.card_show_price else 0
    photo = _photo(p, (x2 - x1, y2 - y1 - price_h))
    if photo:
        img.paste(photo, (x1 + (x2 - x1 - photo.width) // 2, y1 + (y2 - y1 - price_h - photo.height) // 2))
    if config.card_show_price:
        cx = (x1 + x2) / 2
        _centered(d, cx, y2 - price_h + 10, _brl(p.price), _font(56), config.brand_color)
        if p.original_price > p.price:
            f_old = _font(26)
            old = _brl(p.original_price)
            ow = d.textlength(old, font=f_old)
            _centered(d, cx, y2 - price_h + 80, old, f_old, "#888888")
            d.line([cx - ow / 2, y2 - price_h + 96, cx + ow / 2, y2 - price_h + 96], fill="#888888", width=3)
    if p.discount:
        r = 70
        bx, by = x2 - r, y1 + r
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=config.brand_color)
        _centered(d, bx, by - 38, f"-{p.discount}%", _font(36), "white")
        _centered(d, bx, by + 10, "OFF", _font(24), "white")
    return img


def make_card(p: Product, path: str) -> str:
    if FRAME.exists():
        img = _framed_card(p)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        img.save(path, "JPEG", quality=90)
        return path

    color = config.brand_color
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    # faixa de cima
    d.rectangle([0, 0, W, BAR], fill=color)
    _centered(d, 130, 78, "PROMOÇÃO", _font(22), "white")
    d.polygon([(121, 35), (151, 22), (151, 66), (121, 53)], outline="white", width=4)  # megafone
    d.rectangle([109, 35, 121, 53], outline="white", width=4)

    f_brand = _font(34)
    bw = d.textlength(config.brand_name, font=f_brand) + 40
    d.rounded_rectangle([W / 2 - bw / 2, 18, W / 2 + bw / 2, 70], radius=14, fill="white")
    _centered(d, W / 2, 24, config.brand_name, f_brand, color)
    _centered(d, W / 2, 82, config.brand_site.upper(), _font(20), "white")

    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        logo.thumbnail((160, 90))
        img.paste(logo, (W - 60 - logo.width, (BAR - logo.height) // 2), logo)

    f_tag = _font(20)
    d.text((W - 25 - d.textlength(config.brand_hashtag, font=f_tag), 132), config.brand_hashtag, font=f_tag, fill=color)

    # foto do produto
    photo = _photo(p, (520, 520))
    if photo:
        img.paste(photo, ((W - photo.width) // 2, 170 + (520 - photo.height) // 2))

    # preço + selo de desconto
    _centered(d, W / 2, 705, _brl(p.price), _font(56), color)
    if p.original_price > p.price:
        f_old = _font(26)
        old = _brl(p.original_price)
        ow = d.textlength(old, font=f_old)
        _centered(d, W / 2, 775, old, f_old, "#888888")
        d.line([W / 2 - ow / 2, 791, W / 2 + ow / 2, 791], fill="#888888", width=3)
    if p.discount:
        d.ellipse([760, 200, 900, 340], fill=color)
        _centered(d, 830, 232, f"-{p.discount}%", _font(36), "white")
        _centered(d, 830, 280, "OFF", _font(24), "white")

    # faixa de baixo
    d.rectangle([0, H - 60, W, H], fill=color)
    _centered(d, W / 2, H - 45, "ENTRE NOS GRUPOS PARA CUPONS E PROMOÇÕES", _font(24), "white")

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "JPEG", quality=90)
    return path
