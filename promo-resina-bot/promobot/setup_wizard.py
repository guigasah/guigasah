"""Assistente que cria o .env fazendo perguntas, e já testa as chaves."""
import secrets
from pathlib import Path

from dotenv import dotenv_values

ENV = Path(__file__).resolve().parent.parent / ".env"
EXAMPLE = ENV.with_name(".env.example")

QUESTIONS = [
    ("ALI_APP_KEY", "App Key do AliExpress (openservice.aliexpress.com → seu app)", ""),
    ("ALI_APP_SECRET", "App Secret do AliExpress", ""),
    ("ALI_TRACKING_ID", "Tracking ID (portals.aliexpress.com → Ferramentas → Tracking ID)", ""),
    ("BRAND_NAME", "Nome da marca na arte", "FORJA NERD"),
    ("BRAND_SITE", "Site ou @ que aparece na arte", "forjanerd.com.br"),
    ("BRAND_HASHTAG", "Hashtag", "#forjanerd"),
    ("BRAND_COLOR", "Cor principal (ex: #E60012)", "#E60012"),
    ("GROUPS_LINK", "Link de convite do grupo/canal do WhatsApp", ""),
    ("MAX_PRICE_BRL", "Preço máximo das resinas (R$)", "250"),
    ("MIN_DISCOUNT", "Desconto mínimo (%)", "20"),
    ("INTERVAL_MINUTES", "Postar a cada quantos minutos", "120"),
]


def _fmt(value: str) -> str:
    return f'"{value}"' if "#" in value or " " in value else value


def _read(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def run() -> None:
    lines = _read(ENV) or _read(EXAMPLE)
    current = dotenv_values(ENV if ENV.exists() else EXAMPLE)
    answers = {}
    print("Configuração do agente (Enter mantém o valor entre colchetes)\n")
    for key, label, default in QUESTIONS:
        value = current.get(key) or default
        shown = "****" if "SECRET" in key and value else value
        answers[key] = input(f"{label} [{shown}]: ").strip() or value
    if not current.get("EVOLUTION_API_KEY"):
        answers["EVOLUTION_API_KEY"] = secrets.token_hex(16)

    out, done = [], set()
    for l in lines:
        key = l.split("=", 1)[0] if "=" in l and not l.startswith("#") else None
        if key in answers:
            out.append(f"{key}={_fmt(answers[key])}")
            done.add(key)
        else:
            out.append(l)
    out += [f"{k}={_fmt(v)}" for k, v in answers.items() if k not in done]
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"\n✅ Salvo em {ENV}")
