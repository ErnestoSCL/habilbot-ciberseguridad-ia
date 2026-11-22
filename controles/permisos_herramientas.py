"""Control del agente: diccionario de permisos aplicado en el arnés, fuera del modelo.

Para cada rol dice qué herramientas puede usar y con qué condiciones. El agente actúa con los
permisos de quien pide (mediación completa), no con los suyos:
  - solo_propio:     el colegiado_id se toma de la sesión, aunque el modelo pida otro (A4, A10);
  - requiere_habil:  la constancia solo se emite si el padrón dice hábil, diga lo que diga el
                     modelo o el documento adjunto (A1).
Una herramienta que no figura para el rol, se bloquea.
"""
import csv

from controles.base import Control
from src import config
from src.sesion import Sesion

PERMISOS = {
    "colegiado": {
        "consultar_estado": {"solo_propio": True},
        "emitir_constancia": {"solo_propio": True, "requiere_habil": True},
        "abrir_expediente": {"solo_propio": True},
    },
    "personal": {
        "consultar_estado": {},
        "abrir_expediente": {},
    },
}


class PermisoDenegado(PermissionError):
    """Motivo de política apto para la traza y el usuario."""


def leer_padron() -> dict[str, dict]:
    with open(config.PADRON, encoding="utf-8") as f:
        return {r["colegiado_id"]: r for r in csv.DictReader(f)}


def verificar_permiso(herramienta: str, codigo: str, sesion: Sesion, fila: dict | None) -> str | None:
    """Política común a la comprobación previa y al punto de ejecución."""
    if not isinstance(sesion, Sesion) or not sesion.usuario:
        return "se requiere una sesión autenticada"
    reglas = PERMISOS.get(sesion.rol, {}).get(herramienta)
    if reglas is None:
        return "herramienta no permitida para el rol de la sesión"
    if reglas.get("solo_propio") and (not codigo or codigo != sesion.colegiado_id):
        return "el colegiado solo puede actuar sobre su propio código"
    if fila is None:
        return "el colegiado no figura en el padrón"
    if reglas.get("requiere_habil") and fila["habil"] != "True":
        return f"{codigo} no está hábil en el padrón"
    return None


class PermisosHerramientas(Control):
    nombre = "permisos_herramientas"

    def autorizar_herramienta(self, herramienta, args, sesion):
        args = dict(args)
        if sesion.rol == "colegiado":
            args["colegiado_id"] = sesion.colegiado_id
        codigo = args["colegiado_id"]
        return args, verificar_permiso(herramienta, codigo, sesion, leer_padron().get(codigo))
