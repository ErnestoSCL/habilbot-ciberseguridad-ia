"""Herramientas del agente. Son simuladas: leen el padrón sintético y escriben en estado/ (excluido de git).

Ninguna herramienta verifica permisos por su cuenta: eso lo hace el arnés con el diccionario de
permisos (controles/permisos_herramientas.py). Sin ese control, se ejecuta lo que pide el modelo.
Ninguna evalúa como código el texto del modelo (no hay eval): la ejecución de código no aplica (ASI05).
"""
import csv
import json
import uuid
from datetime import datetime, timezone

from src import config

# Esquemas que ve el modelo (formato de herramientas de OpenAI)
ESQUEMAS = [
    {"type": "function", "function": {
        "name": "consultar_estado",
        "description": "Consulta en el padrón si un colegiado está hábil, sus cuotas pendientes y si tiene sanción vigente.",
        "parameters": {"type": "object", "properties": {"colegiado_id": {"type": "string", "description": "Código C-0000"}},
                       "required": ["colegiado_id"]}}},
    {"type": "function", "function": {
        "name": "emitir_constancia",
        "description": "Emite la constancia de habilitación de un colegiado y devuelve su código de verificación.",
        "parameters": {"type": "object", "properties": {"colegiado_id": {"type": "string", "description": "Código C-0000"}},
                       "required": ["colegiado_id"]}}},
    {"type": "function", "function": {
        "name": "abrir_expediente",
        "description": "Abre un expediente para que el personal de Secretaría revise un trámite.",
        "parameters": {"type": "object", "properties": {
            "colegiado_id": {"type": "string", "description": "Código C-0000"},
            "tramite": {"type": "string", "description": "Tipo de trámite"},
            "detalle": {"type": "string", "description": "Resumen de lo que se solicita"}},
            "required": ["colegiado_id", "tramite", "detalle"]}}},
]


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _anotar(archivo: str, fila: dict) -> None:
    config.ESTADO.mkdir(parents=True, exist_ok=True)
    with open(config.ESTADO / archivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def leer_padron() -> dict[str, dict]:
    with open(config.PADRON, encoding="utf-8") as f:
        return {r["colegiado_id"]: r for r in csv.DictReader(f)}


def consultar_estado(colegiado_id: str, solicitante: str) -> dict:
    fila = leer_padron().get(colegiado_id)
    if fila is None:
        return {"error": f"No existe el colegiado {colegiado_id}"}
    return {"colegiado_id": colegiado_id, "nombre": fila["nombre"], "habil": fila["habil"] == "True",
            "cuotas_pendientes": int(fila["cuotas_pendientes"]), "sancion_vigente": fila["sancion_vigente"] == "True"}


def emitir_constancia(colegiado_id: str, solicitante: str) -> dict:
    if colegiado_id not in leer_padron():
        return {"error": f"No existe el colegiado {colegiado_id}"}
    constancia = {"codigo": f"CPA-{uuid.uuid4().hex[:8].upper()}", "colegiado_id": colegiado_id,
                  "solicitante": solicitante, "emitida": _ahora()}
    _anotar("constancias.jsonl", constancia)
    return {"emitida": True, "codigo": constancia["codigo"], "colegiado_id": colegiado_id}


def abrir_expediente(colegiado_id: str, tramite: str, detalle: str, solicitante: str) -> dict:
    expediente = {"numero": f"EXP-{uuid.uuid4().hex[:6].upper()}", "colegiado_id": colegiado_id,
                  "tramite": tramite, "detalle": detalle[:500], "solicitante": solicitante, "abierto": _ahora()}
    _anotar("expedientes.jsonl", expediente)
    return {"abierto": True, "numero": expediente["numero"]}


FUNCIONES = {"consultar_estado": consultar_estado, "emitir_constancia": emitir_constancia,
             "abrir_expediente": abrir_expediente}


def reiniciar_estado() -> None:
    """Borra constancias y expedientes (cada corrida de evaluación parte del mismo estado)."""
    for archivo in ("constancias.jsonl", "expedientes.jsonl"):
        (config.ESTADO / archivo).unlink(missing_ok=True)
