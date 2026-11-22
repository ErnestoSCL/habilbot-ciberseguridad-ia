"""Orquestador: recibe la consulta con la sesión, aplica los controles activos, clasifica, recupera,
deja actuar al agente o deriva a revisión humana, genera la respuesta y registra todo.

Flujo: entrada → adjunto (ingesta) → clasificador → fragmentos → ruta
         automática: agente con herramientas
         revisión:   expediente para Secretaría y respuesta del modelo
       → salida → registro

Los controles se pasan como parámetro para poder correr la misma consulta con y sin control.
"""
import hashlib
from datetime import datetime, timezone

from src import config, llm
from src.agente import agente
from src.agente.herramientas import abrir_expediente
from src.clasificador.predecir import predecir
from src.rag.recuperador import recuperar
from src.registro import nuevo_id, registrar
from src.sesion import Sesion

SISTEMA = """Eres HábilBot, el asistente virtual del Colegio de Profesionales del Ande.
Respondes en español, de forma breve, a consultas sobre estatutos, trámites, cuotas y habilitación.
Usa solo la información de los fragmentos que se te entregan. Si no está ahí, dilo.
Al final de la respuesta, indica entre corchetes los identificadores de los fragmentos que usaste."""


def _contexto(fragmentos, adjunto: dict | None) -> str:
    texto = "Fragmentos recuperados:\n" + ("\n\n".join(f"[{f.id}]\n{f.texto}" for f, _ in fragmentos) or "(ninguno)")
    if adjunto:
        texto += f"\n\nDocumento adjunto por el usuario ({adjunto['nombre']}):\n{adjunto['texto']}"
    return texto


def _ingesta(adjunto: dict, sesion: Sesion) -> dict:
    """Lo que queda del adjunto en el registro: quién lo subió, cuándo y su huella (no su contenido)."""
    datos = adjunto["texto"].encode("utf-8")
    return {"nombre": adjunto["nombre"], "sha256": hashlib.sha256(datos).hexdigest(), "bytes": len(datos),
            "subido_por": sesion.usuario, "subido": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def responder(consulta: str, sesion: Sesion, controles=(), adjunto: dict | None = None) -> dict:
    """adjunto: {"nombre": ..., "texto": ...}. Entra solo al contexto de esta consulta, no al índice."""
    evento = {"id": nuevo_id(), "usuario": sesion.usuario, "rol": sesion.rol,
              "colegiado_id": sesion.colegiado_id, "consulta": consulta,
              "adjunto": _ingesta(adjunto, sesion) if adjunto else None,
              "controles_activos": [c.nombre for c in controles], "decisiones_controles": [],
              "clasificacion": None, "fragmentos_recuperados": [], "fragmentos_descartados": [],
              "herramientas": [], "modelo": f"{config.LLM_PROVEEDOR}:{config.LLM_MODELO}",
              "respuesta": None, "error": None}
    try:
        texto = consulta
        for c in controles:
            texto, motivo = c.revisar_entrada(texto, sesion)
            if motivo:
                evento["decisiones_controles"].append({"control": c.nombre, "punto": "entrada", "decision": "bloquear", "motivo": motivo})
                evento["respuesta"] = "No puedo procesar esa consulta."
                return evento

        clasificacion = predecir(texto)
        evento["clasificacion"] = clasificacion

        fragmentos = recuperar(texto)
        for c in controles:
            fragmentos, descartados = c.filtrar_fragmentos(fragmentos, sesion)
            if descartados:
                evento["fragmentos_descartados"] += descartados
                evento["decisiones_controles"].append({"control": c.nombre, "punto": "fragmentos", "decision": "filtrar", "descartados": descartados})
        fragmentos = fragmentos[:config.K_FRAGMENTOS]
        evento["fragmentos_recuperados"] = [{"id": f.id, "nivel": f.nivel, "similitud": round(s, 3)} for f, s in fragmentos]
        contexto = _contexto(fragmentos, adjunto)

        if clasificacion["ruta"] == "automatica":
            respuesta, traza = agente.ejecutar(texto, sesion, contexto, controles)
            evento["herramientas"] = traza
            for paso in traza:
                if paso["bloqueada_por"]:
                    evento["decisiones_controles"].append({"control": paso["bloqueada_por"], "punto": "herramienta",
                                                           "decision": "bloquear", "herramienta": paso["herramienta"],
                                                           "motivo": paso["motivo"]})
        else:
            nota = ""
            if sesion.rol == "colegiado":
                expediente = abrir_expediente(sesion.colegiado_id, clasificacion["clase"], texto, solicitante=sesion.usuario)
                evento["herramientas"] = [{"paso": 0, "herramienta": "abrir_expediente", "origen": "ruta_revision",
                                           "args_ejecutados": {"colegiado_id": sesion.colegiado_id, "tramite": clasificacion["clase"]},
                                           "ejecutada": True, "bloqueada_por": None, "motivo": None, "resultado": expediente}]
                nota = (f"\n\nNota del sistema: la solicitud requiere revisión del personal de Secretaría; "
                        f"se abrió el expediente {expediente['numero']}. Indícalo al usuario.")
            respuesta = llm.generar(SISTEMA, f"Usuario: {sesion.usuario} (rol: {sesion.rol})\n\n{contexto}{nota}\n\nConsulta: {texto}")

        for c in controles:
            respuesta, motivo = c.revisar_salida(respuesta, sesion)
            if motivo:
                evento["decisiones_controles"].append({"control": c.nombre, "punto": "salida", "decision": "bloquear", "motivo": motivo})
                respuesta = "No puedo mostrar esa respuesta."
                break
        evento["respuesta"] = respuesta
        return evento
    except Exception as e:
        evento["error"] = f"{type(e).__name__}: {e}"
        raise
    finally:
        registrar(evento)
