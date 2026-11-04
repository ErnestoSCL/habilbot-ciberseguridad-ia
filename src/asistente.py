"""Orquestador: recibe la consulta con la sesión, aplica los controles activos, recupera, genera y registra.

Los controles se pasan como parámetro para poder correr la misma consulta con y sin control.
"""
from src import config, llm
from src.rag.recuperador import recuperar
from src.registro import nuevo_id, registrar
from src.sesion import Sesion

SISTEMA = """Eres HábilBot, el asistente virtual del Colegio de Profesionales del Ande.
Respondes en español, de forma breve, a consultas sobre estatutos, trámites, cuotas y habilitación.
Usa solo la información de los fragmentos que se te entregan. Si no está ahí, dilo.
Al final de la respuesta, indica entre corchetes los identificadores de los fragmentos que usaste."""


def _armar_prompt(consulta: str, fragmentos, sesion: Sesion) -> str:
    contexto = "\n\n".join(f"[{f.id}]\n{f.texto}" for f, _ in fragmentos)
    return (f"Usuario: {sesion.usuario} (rol: {sesion.rol})\n\n"
            f"Fragmentos recuperados:\n{contexto or '(ninguno)'}\n\n"
            f"Consulta: {consulta}")


def responder(consulta: str, sesion: Sesion, controles=()) -> dict:
    evento = {"id": nuevo_id(), "usuario": sesion.usuario, "rol": sesion.rol,
              "colegiado_id": sesion.colegiado_id, "consulta": consulta,
              "controles_activos": [c.nombre for c in controles], "decisiones_controles": [],
              "fragmentos_recuperados": [], "fragmentos_descartados": [],
              "clasificacion": None, "herramientas": [],   # se llenan cuando existan esos componentes
              "modelo": f"{config.LLM_PROVEEDOR}:{config.LLM_MODELO}", "respuesta": None, "error": None}
    try:
        texto = consulta
        for c in controles:
            texto, motivo = c.revisar_entrada(texto, sesion)
            if motivo:
                evento["decisiones_controles"].append({"control": c.nombre, "punto": "entrada", "decision": "bloquear", "motivo": motivo})
                evento["respuesta"] = "No puedo procesar esa consulta."
                return evento

        fragmentos = recuperar(texto)
        for c in controles:
            fragmentos, descartados = c.filtrar_fragmentos(fragmentos, sesion)
            if descartados:
                evento["fragmentos_descartados"] += descartados
                evento["decisiones_controles"].append({"control": c.nombre, "punto": "fragmentos", "decision": "filtrar", "descartados": descartados})
        fragmentos = fragmentos[:config.K_FRAGMENTOS]
        evento["fragmentos_recuperados"] = [{"id": f.id, "nivel": f.nivel, "similitud": round(s, 3)} for f, s in fragmentos]

        respuesta = llm.generar(SISTEMA, _armar_prompt(texto, fragmentos, sesion))
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
