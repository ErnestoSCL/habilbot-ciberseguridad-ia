"""Cliente del modelo de lenguaje. Una sola función: generar(sistema, usuario) -> texto.

El proveedor se elige con LLM_PROVEEDOR en .env: "openai", "gemini" o "simulado".
Con "simulado" no se llama a ninguna API: devuelve el contexto recibido.
Sirve para probar el flujo y el registro sin gastar cuota.
"""
from src import config

_cliente = None


def _openai(sistema: str, usuario: str) -> str:
    global _cliente
    if _cliente is None:
        from openai import OpenAI
        _cliente = OpenAI(api_key=config.OPENAI_API_KEY)
    respuesta = _cliente.chat.completions.create(
        model=config.OPENAI_MODELO,
        temperature=0,
        messages=[{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
    )
    return respuesta.choices[0].message.content or ""


def _gemini(sistema: str, usuario: str) -> str:
    global _cliente
    from google import genai
    from google.genai import types
    if _cliente is None:
        _cliente = genai.Client(api_key=config.GEMINI_API_KEY)
    respuesta = _cliente.models.generate_content(
        model=config.GEMINI_MODELO,
        contents=usuario,
        config=types.GenerateContentConfig(system_instruction=sistema, temperature=0),
    )
    return respuesta.text or ""


def generar(sistema: str, usuario: str) -> str:
    if config.LLM_PROVEEDOR == "simulado":
        return "[respuesta simulada]\n" + usuario
    if config.LLM_PROVEEDOR == "openai":
        if not config.OPENAI_API_KEY:
            raise RuntimeError("Falta OPENAI_API_KEY en .env (o use LLM_PROVEEDOR=simulado)")
        return _openai(sistema, usuario)
    if config.LLM_PROVEEDOR == "gemini":
        if not config.GEMINI_API_KEY:
            raise RuntimeError("Falta GEMINI_API_KEY en .env (o use LLM_PROVEEDOR=simulado)")
        return _gemini(sistema, usuario)
    raise ValueError(f"LLM_PROVEEDOR desconocido: {config.LLM_PROVEEDOR}")
