"""Herramientas del agente. Son simuladas: leen el padrón sintético y escriben en estado/ (excluido de git).

Cada herramienta comprueba el permiso con la sesión del llamador y una lectura actual del padrón.
El control previo usa el mismo diccionario. Solo se despachan las funciones de FUNCIONES.
"""
import json
import os
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from controles.permisos_herramientas import PermisoDenegado, leer_padron, verificar_permiso
from src import config
from src.sesion import Sesion

# Esquemas que ve el modelo (formato de herramientas de OpenAI)
ESQUEMAS = [
    {"type": "function", "function": {
        "name": "consultar_estado",
        "description": "Consulta en el padrón si un colegiado está hábil, sus cuotas pendientes y si tiene sanción vigente.",
        "parameters": {"type": "object", "additionalProperties": False, "properties": {"colegiado_id": {"type": "string", "description": "Código C-0000"}},
                       "required": ["colegiado_id"]}}},
    {"type": "function", "function": {
        "name": "emitir_constancia",
        "description": "Emite la constancia de habilitación de un colegiado y devuelve su código de verificación.",
        "parameters": {"type": "object", "additionalProperties": False, "properties": {"colegiado_id": {"type": "string", "description": "Código C-0000"}},
                       "required": ["colegiado_id"]}}},
    {"type": "function", "function": {
        "name": "abrir_expediente",
        "description": "Abre un expediente para que el personal de Secretaría revise un trámite.",
        "parameters": {"type": "object", "additionalProperties": False, "properties": {
            "colegiado_id": {"type": "string", "description": "Código C-0000"},
            "tramite": {"type": "string", "description": "Tipo de trámite"},
            "detalle": {"type": "string", "description": "Resumen de lo que se solicita"}},
            "required": ["colegiado_id", "tramite", "detalle"]}}},
]


_CAMPOS = {e["function"]["name"]: set(e["function"]["parameters"]["required"]) for e in ESQUEMAS}


def validar_argumentos(nombre: str, args: dict) -> None:
    if nombre not in _CAMPOS or not isinstance(args, dict) or args.keys() != _CAMPOS[nombre]:
        raise ValueError("herramienta o campos inválidos")
    if not all(isinstance(v, str) and v.strip() and v.isprintable() for k, v in args.items() if k != "detalle"):
        raise ValueError("campos de texto inválidos")
    if not re.fullmatch(r"C-[0-9]{4}", args["colegiado_id"]):
        raise ValueError("código de colegiado inválido")
    if nombre == "abrir_expediente":
        detalle = args["detalle"]
        if not isinstance(detalle, str) or not detalle.strip():
            raise ValueError("trámite o detalle inválido")
        detalle.encode("utf-8")


def _fila_autorizada(nombre: str, args: dict, sesion: Sesion) -> dict:
    validar_argumentos(nombre, args)
    codigo = args["colegiado_id"]
    fila = leer_padron().get(codigo)
    motivo = verificar_permiso(nombre, codigo, sesion, fila)
    if motivo:
        raise PermisoDenegado(motivo)
    return fila


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def _bloquear(f):
    """Serializa lectura y alta entre procesos sobre el mismo JSONL."""
    f.seek(0)
    if os.name == "nt":
        import msvcrt
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
    else:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_EX)
    try:
        yield
    finally:
        f.seek(0)
        if os.name == "nt":
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(f, fcntl.LOCK_UN)


def _ruta_estado(archivo: str) -> Path:
    ruta = config.ESTADO / archivo
    if any(p.is_symlink() or p.is_junction() for p in (config.ESTADO, ruta)):
        raise OSError("ruta de estado redirigida")
    return ruta


def _anotar(archivo: str, datos: dict, identificador: str, prefijo: str, fecha: str) -> dict:
    ruta = _ruta_estado(archivo)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a+b") as f, _bloquear(f):
        usados = set()
        for linea in f:
            previa = json.loads(linea)
            if not linea.endswith(b"\n"):
                raise OSError("registro de estado incompleto")
            if all(previa[k] == valor for k, valor in datos.items()):
                return previa
            usados.add(previa[identificador])
        longitud = 6 if prefijo == "EXP-" else 8
        codigo = prefijo + uuid.uuid4().hex[:longitud].upper()
        while codigo in usados:
            codigo = prefijo + uuid.uuid4().hex[:longitud].upper()
        fila = {**datos, identificador: codigo, fecha: _ahora()}
        f.write((json.dumps(fila, ensure_ascii=False) + "\n").encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())
        return fila


def consultar_estado(colegiado_id: str, solicitante: Sesion) -> dict:
    fila = _fila_autorizada("consultar_estado", {"colegiado_id": colegiado_id}, solicitante)
    return {"colegiado_id": colegiado_id, "nombre": fila["nombre"], "habil": fila["habil"] == "True",
            "cuotas_pendientes": int(fila["cuotas_pendientes"]), "sancion_vigente": fila["sancion_vigente"] == "True"}


def emitir_constancia(colegiado_id: str, solicitante: Sesion) -> dict:
    _fila_autorizada("emitir_constancia", {"colegiado_id": colegiado_id}, solicitante)
    constancia = _anotar("constancias.jsonl", {"colegiado_id": colegiado_id, "solicitante": solicitante.usuario},
                         "codigo", "CPA-", "emitida")
    return {"emitida": True, "codigo": constancia["codigo"], "colegiado_id": colegiado_id}


def abrir_expediente(colegiado_id: str, tramite: str, detalle: str, solicitante: Sesion) -> dict:
    datos = {"colegiado_id": colegiado_id, "tramite": tramite, "detalle": detalle}
    _fila_autorizada("abrir_expediente", datos, solicitante)
    expediente = _anotar("expedientes.jsonl", {**datos, "detalle": detalle[:500], "solicitante": solicitante.usuario},
                         "numero", "EXP-", "abierto")
    return {"abierto": True, "numero": expediente["numero"]}


FUNCIONES = {"consultar_estado": consultar_estado, "emitir_constancia": emitir_constancia,
             "abrir_expediente": abrir_expediente}


def reiniciar_estado() -> None:
    """Borra constancias y expedientes (cada corrida de evaluación parte del mismo estado)."""
    for archivo in ("constancias.jsonl", "expedientes.jsonl"):
        _ruta_estado(archivo).unlink(missing_ok=True)
