"""Envio para o WhatsApp.

- dryrun: só salva a arte + legenda em output/ (para testar).
- evolution: Evolution API (https://doc.evolution-api.com), conecta um número
  de WhatsApp via QR code e envia para grupos (...@g.us) ou canais (...@newsletter).
"""
import base64
import time
from pathlib import Path

import requests

from .config import config


def _send_evolution(target: str, image_path: str, caption: str) -> None:
    url = f"{config.evolution_url}/message/sendMedia/{config.evolution_instance}"
    media = base64.b64encode(Path(image_path).read_bytes()).decode()
    resp = requests.post(
        url,
        headers={"apikey": config.evolution_api_key},
        json={
            "number": target,
            "mediatype": "image",
            "mimetype": "image/jpeg",
            "caption": caption,
            "media": media,
            "fileName": Path(image_path).name,
        },
        timeout=60,
    )
    resp.raise_for_status()


def send(image_path: str, caption: str) -> None:
    if config.provider == "dryrun":
        txt = Path(image_path).with_suffix(".txt")
        txt.write_text(caption, encoding="utf-8")
        print(f"[dryrun] {image_path}\n{caption}\n{'-' * 40}")
        return
    if config.provider != "evolution":
        raise ValueError(f"WHATSAPP_PROVIDER inválido: {config.provider}")
    if not config.targets:
        raise RuntimeError("Defina WHATSAPP_TARGETS no .env (use: python -m promobot grupos)")
    for i, target in enumerate(config.targets):
        if i:
            time.sleep(config.delay_between_targets)
        _send_evolution(target, image_path, caption)
        print(f"[whatsapp] enviado para {target}")


def list_groups() -> list[dict]:
    url = f"{config.evolution_url}/group/fetchAllGroups/{config.evolution_instance}"
    resp = requests.get(
        url, headers={"apikey": config.evolution_api_key}, params={"getParticipants": "false"}, timeout=60
    )
    resp.raise_for_status()
    return resp.json()
