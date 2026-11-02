import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _list(name: str, default: str = "") -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


def _box(name: str):
    parts = _list(name)
    return tuple(int(x) for x in parts) if len(parts) == 4 else None


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


@dataclass
class Config:
    ali_app_key: str = os.getenv("ALI_APP_KEY", "")
    ali_app_secret: str = os.getenv("ALI_APP_SECRET", "")
    ali_tracking_id: str = os.getenv("ALI_TRACKING_ID", "")

    keywords: list[str] = field(default_factory=lambda: _list("SEARCH_KEYWORDS", "resina 3d"))
    max_price: float = float(os.getenv("MAX_PRICE_BRL", 250))
    min_discount: int = _int("MIN_DISCOUNT", 20)
    min_rating: int = _int("MIN_RATING", 90)
    min_sales: int = _int("MIN_SALES", 10)
    posts_per_run: int = _int("POSTS_PER_RUN", 3)
    repost_after_days: int = _int("REPOST_AFTER_DAYS", 7)

    provider: str = os.getenv("WHATSAPP_PROVIDER", "dryrun")
    evolution_url: str = os.getenv("EVOLUTION_URL", "http://localhost:8080").rstrip("/")
    evolution_api_key: str = os.getenv("EVOLUTION_API_KEY", "")
    evolution_instance: str = os.getenv("EVOLUTION_INSTANCE", "promo")
    targets: list[str] = field(default_factory=lambda: _list("WHATSAPP_TARGETS"))
    delay_between_targets: int = _int("DELAY_BETWEEN_TARGETS", 8)

    brand_name: str = os.getenv("BRAND_NAME", "FORJA NERD")
    brand_site: str = os.getenv("BRAND_SITE", "forjanerd.com.br")
    brand_hashtag: str = os.getenv("BRAND_HASHTAG", "#forjanerd")
    brand_color: str = os.getenv("BRAND_COLOR", "#E60012")
    groups_link: str = os.getenv("GROUPS_LINK", "")
    card_photo_box: tuple | None = _box("CARD_PHOTO_BOX")
    card_show_price: bool = os.getenv("CARD_SHOW_PRICE", "true").lower() == "true"

    use_ai_copy: bool = os.getenv("USE_AI_COPY", "false").lower() == "true"
    ai_model: str = os.getenv("AI_MODEL", "claude-opus-5-5")

    interval_minutes: int = _int("INTERVAL_MINUTES", 120)
    quiet_hours: str = os.getenv("QUIET_HOURS", "23-8")

    db_path: str = os.getenv("DB_PATH", "promobot.db")
    output_dir: str = os.getenv("OUTPUT_DIR", "output")


config = Config()
