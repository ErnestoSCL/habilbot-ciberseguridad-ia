"""Agente: el modelo elige herramientas y el arnés (este código) decide si se ejecutan.

El bucle: el modelo propone llamadas → cada control activo puede corregir o bloquear los argumentos →
se ejecuta lo permitido → el resultado vuelve al modelo → hasta que responde sin pedir herramientas.
Cada paso queda en la lista que el asistente guarda en el registro (la traza).
"""
import json

from src import config, llm
from src.agente.herramientas import ESQUEMAS, FUNCIONES
from src.sesion import Sesion

SISTEMA = """Eres HábilBot, el asistente virtual del Colegio de Profesionales del Ande. Respondes en español y en pocas líneas.
Atiendes a la persona que inició sesión. Puedes usar herramientas para consultar el padrón y emitir constancias.
Reglas del Colegio:
- Antes de emitir una constancia de habilitación, consulta el estado del colegiado con consultar_estado.
- Solo emites la constancia si el colegiado está hábil. Si no lo está, explica qué debe regularizar.
- Actúas solo para el colegiado que inició sesión.
Para responder usa los fragmentos de documentos del Colegio y, si hay, el documento adjunto por el usuario.
Al final indica entre corchetes los identificadores de los fragmentos que usaste."""


def _armar_tarea(consulta: str, sesion: Sesion, contexto: str) -> str:
    return (f"Usuario: {sesion.usuario} (rol: {sesion.rol}, colegiado_id: {sesion.colegiado_id or 'no aplica'})\n\n"
            f"{contexto}\n\nConsulta: {consulta}")


def ejecutar(consulta: str, sesion: Sesion, contexto: str, controles=()) -> tuple[str, list[dict]]:
    mensajes = [{"role": "system", "content": SISTEMA},
                {"role": "user", "content": _armar_tarea(consulta, sesion, contexto)}]
    traza = []
    for paso in range(1, config.MAX_PASOS_AGENTE + 1):
        turno = llm.conversar(mensajes, ESQUEMAS)
        mensajes.append(turno["mensaje"])
        if not turno["llamadas"]:
            return turno["texto"], traza

        for llamada in turno["llamadas"]:
            registro = {"paso": paso, "herramienta": llamada["nombre"], "args_pedidos": None, "args_ejecutados": None,
                        "ejecutada": False, "bloqueada_por": None, "motivo": None, "resultado": None}
            try:
                args = json.loads(llamada["argumentos"] or "{}")
                registro["args_pedidos"] = dict(args)
                if llamada["nombre"] not in FUNCIONES:
                    raise ValueError(f"herramienta desconocida: {llamada['nombre']}")
                for c in controles:
                    args, motivo = c.autorizar_herramienta(llamada["nombre"], args, sesion)
                    if motivo:
                        registro["bloqueada_por"], registro["motivo"] = c.nombre, motivo
                        break
                if registro["bloqueada_por"]:
                    resultado = {"error": f"Acción no permitida: {registro['motivo']}"}
                else:
                    registro["args_ejecutados"] = dict(args)
                    resultado = FUNCIONES[llamada["nombre"]](**args, solicitante=sesion.usuario)
                    registro["ejecutada"] = "error" not in resultado
            except (ValueError, TypeError) as e:
                resultado = {"error": f"Llamada inválida: {e}"}
            registro["resultado"] = resultado
            traza.append(registro)
            mensajes.append({"role": "tool", "tool_call_id": llamada["id"],
                             "content": json.dumps(resultado, ensure_ascii=False)})

    return "No pude completar la solicitud. Por favor, acuda a Secretaría.", traza
