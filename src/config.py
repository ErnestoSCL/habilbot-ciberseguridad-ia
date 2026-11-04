"""Rutas y parámetros del producto. La llave de la API se lee de .env, nunca del código."""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

CORPUS = RAIZ / "datos" / "corpus"
PADRON = RAIZ / "datos" / "padron_sintetico.csv"
USUARIOS = RAIZ / "datos" / "usuarios_sinteticos.csv"
REGISTRO = RAIZ / "registros" / "vivo" / "eventos.jsonl"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODELO = os.getenv("OPENAI_MODELO", "gpt-4o-mini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODELO = os.getenv("GEMINI_MODELO", "gemini-2.5-flash")

# "openai", "gemini" o "simulado". Si no se indica, se usa el proveedor cuya llave esté en .env.
LLM_PROVEEDOR = os.getenv("LLM_PROVEEDOR") or (
    "openai" if OPENAI_API_KEY else "gemini" if GEMINI_API_KEY else "simulado")
LLM_MODELO = {"openai": OPENAI_MODELO, "gemini": GEMINI_MODELO}.get(LLM_PROVEEDOR, "simulado")

# Cantidad de fragmentos que el recuperador entrega al modelo
K_FRAGMENTOS = 4
