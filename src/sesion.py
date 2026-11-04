"""Inicio de sesión. La identidad y el rol salen de aquí, nunca del texto que escribe el usuario."""
import csv
import hashlib
import hmac
from dataclasses import dataclass

from src import config


@dataclass(frozen=True)
class Sesion:
    usuario: str
    rol: str                  # "colegiado" o "personal"
    colegiado_id: str | None


def _cargar_usuarios() -> dict[str, dict]:
    with open(config.USUARIOS, encoding="utf-8") as f:
        return {fila["usuario"]: fila for fila in csv.DictReader(f)}


def iniciar_sesion(usuario: str, clave: str) -> Sesion:
    fila = _cargar_usuarios().get(usuario)
    if fila is None:
        raise PermissionError("Credenciales inválidas")
    calculado = hashlib.pbkdf2_hmac("sha256", clave.encode(), fila["sal"].encode(), 100_000).hex()
    if not hmac.compare_digest(calculado, fila["hash_clave"]):
        raise PermissionError("Credenciales inválidas")
    return Sesion(fila["usuario"], fila["rol"], fila["colegiado_id"] or None)
