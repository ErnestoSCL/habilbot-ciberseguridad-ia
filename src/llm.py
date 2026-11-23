"""Cliente del modelo de lenguaje.

    generar(sistema, usuario) -> texto                       respuesta simple (asistente)
    conversar(mensajes, herramientas) -> {texto, llamadas}   respuesta con herramientas (agente)

El proveedor se elige con LLM_PROVEEDOR en .env: "openai", "gemini" o "simulado".
Con "simulado" no se llama a ninguna API: devuelve el contexto recibido.
Sirve para probar el flujo y el registro sin gastar cuota.
El agente (conversar) necesita OpenAI: usa su interfaz de herramientas (tool calling).
"""
from src import config

_clientes = {}


def _cliente_openai():
    if "openai" not in _clientes:
        if not config.OPENAI_API_KEY:
            raise RuntimeError("Falta OPENAI_API_KEY en .env (o use LLM_PROVEEDOR=simulado)")
        from openai import OpenAI
        _clientes["openai"] = OpenAI(api_key=config.OPENAI_API_KEY)
    return _clientes["openai"]


def _gemini(sistema: str, usuario: str) -> str:
    from google import genai
    from google.genai import types
    if "gemini" not in _clientes:
        if not config.GEMINI_API_KEY:
            raise RuntimeError("Falta GEMINI_API_KEY en .env (o use LLM_PROVEEDOR=simulado)")
        _clientes["gemini"] = genai.Client(api_key=config.GEMINI_API_KEY)
    respuesta = _clientes["gemini"].models.generate_content(
        model=config.GEMINI_MODELO,
        contents=usuario,
        config=types.GenerateContentConfig(system_instruction=sistema, temperature=0),
    )
    return respuesta.text or ""


def generar(sistema: str, usuario: str) -> str:
    if config.LLM_PROVEEDOR == "simulado":
        return "[respuesta simulada]\n" + usuario
    if config.LLM_PROVEEDOR == "openai":
        respuesta = _cliente_openai().chat.completions.create(
            model=config.OPENAI_MODELO,
            temperature=0,
            messages=[{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
        )
        return respuesta.choices[0].message.content or ""
    if config.LLM_PROVEEDOR == "gemini":
        return _gemini(sistema, usuario)
    raise ValueError(f"LLM_PROVEEDOR desconocido: {config.LLM_PROVEEDOR}")


def conversar(mensajes: list[dict], herramientas: list[dict]) -> dict:
    """Un turno del agente. Devuelve el texto, las herramientas que el modelo pide y el mensaje para el historial."""
    if config.LLM_PROVEEDOR == "simulado":
        texto = "[respuesta simulada del agente]\n" + mensajes[-1]["content"]
        return {"texto": texto, "llamadas": [], "mensaje": {"role": "assistant", "content": texto}}
    if config.LLM_PROVEEDOR != "openai":
        raise RuntimeError("El agente necesita LLM_PROVEEDOR=openai (o simulado para pruebas)")

    m = _cliente_openai().chat.completions.create(
        model=config.OPENAI_MODELO, temperature=0, messages=mensajes, tools=herramientas,
    ).choices[0].message
    llamadas = [{"id": c.id, "nombre": c.function.name, "argumentos": c.function.arguments} for c in m.tool_calls or []]
    mensaje = {"role": "assistant", "content": m.content}
    if llamadas:
        mensaje["tool_calls"] = [{"id": c["id"], "type": "function",
                                  "function": {"name": c["nombre"], "arguments": c["argumentos"]}} for c in llamadas]
    return {"texto": m.content or "", "llamadas": llamadas, "mensaje": mensaje}
