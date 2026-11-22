"""Clasifica una solicitud: tipo de trámite, confianza y ruta (automática o revisión humana).

Antes de cargar el modelo se compara su huella SHA-256 con la registrada al entrenarlo:
joblib usa pickle, y cargar un archivo alterado puede ejecutar código (amenaza A7).
"""
import hashlib
import json
from functools import lru_cache

import joblib

from src import config

# Trámites que el agente puede atender solo; los demás pasan a revisión del personal.
RUTA_AUTOMATICA = {"consulta_general", "constancia_habilitacion", "pago_cuotas"}


class ModeloAlterado(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _modelo():
    esperado = json.loads(config.FICHA_CLASIFICADOR.read_text(encoding="utf-8"))["sha256"]
    real = hashlib.sha256(config.MODELO_CLASIFICADOR.read_bytes()).hexdigest()
    if real != esperado:
        raise ModeloAlterado("La huella del modelo no coincide con la registrada; no se carga.")
    return joblib.load(config.MODELO_CLASIFICADOR)


def predecir(texto: str) -> dict:
    modelo = _modelo()
    probabilidades = modelo.predict_proba([texto])[0]
    i = probabilidades.argmax()
    clase, confianza = str(modelo.classes_[i]), float(probabilidades[i])
    ruta = "automatica" if clase in RUTA_AUTOMATICA and confianza >= config.UMBRAL_CONFIANZA else "revision"
    return {"clase": clase, "confianza": round(confianza, 3), "ruta": ruta}
