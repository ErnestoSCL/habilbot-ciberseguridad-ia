"""Registro de eventos en JSONL: una línea por consulta, con todo lo necesario para la «señal en el registro»."""
import json
import uuid
from datetime import datetime, timezone

from src import config


def nuevo_id() -> str:
    return uuid.uuid4().hex[:12]


def registrar(evento: dict) -> None:
    config.REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    evento = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **evento}
    with open(config.REGISTRO, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")
