"""Entrena el clasificador de intención y guarda el modelo con sus métricas y su huella SHA-256.

    python -m src.clasificador.entrenar

Datos: datos/solicitudes_sinteticas.csv (entrenamiento y prueba interna, 80/20 con semilla fija)
y datos/solicitudes_prueba_externa.csv (textos redactados a mano, distintos de las plantillas).
"""
import csv
import hashlib
import json
from datetime import datetime, timezone

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

from src import config

SEMILLA = 42
CLASES = ["consulta_general", "constancia_habilitacion", "pago_cuotas",
          "actualizacion_datos", "reclamo", "levantamiento_sancion"]


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    return [r["texto"] for r in filas], [r["clase"] for r in filas]


def _metricas(modelo, textos, clases) -> dict:
    pred = modelo.predict(textos)
    return {"n": len(textos),
            "exactitud": round(accuracy_score(clases, pred), 4),
            "f1_macro": round(f1_score(clases, pred, average="macro"), 4),
            "f1_por_clase": {c: round(v["f1-score"], 4) for c, v in
                             classification_report(clases, pred, labels=CLASES, output_dict=True, zero_division=0).items()
                             if c in CLASES},
            "matriz_confusion": {"orden": CLASES, "filas_real_columnas_predicho":
                                 confusion_matrix(clases, pred, labels=CLASES).tolist()}}


def main() -> None:
    textos, clases = _leer(config.SOLICITUDES)
    x_ent, x_prueba, y_ent, y_prueba = train_test_split(textos, clases, test_size=0.2, random_state=SEMILLA, stratify=clases)

    modelo = Pipeline([
        ("rasgos", FeatureUnion([
            # palabras y pares de palabras
            ("palabras", TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2), sublinear_tf=True)),
            # trozos de 3 a 5 letras: toleran errores de tipeo
            ("letras", TfidfVectorizer(strip_accents="unicode", lowercase=True, analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
        ])),
        ("clasificador", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEMILLA)),
    ])
    modelo.fit(x_ent, y_ent)

    config.MODELO_CLASIFICADOR.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, config.MODELO_CLASIFICADOR)
    huella = hashlib.sha256(config.MODELO_CLASIFICADOR.read_bytes()).hexdigest()

    x_ext, y_ext = _leer(config.SOLICITUDES_EXTERNA)
    ficha = {"modelo": config.MODELO_CLASIFICADOR.name, "sha256": huella, "semilla": SEMILLA,
             "entrenado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "algoritmo": "TF-IDF (palabras 1-2 + letras 3-5) + regresión logística balanceada",
             "clases": CLASES, "n_entrenamiento": len(x_ent),
             "prueba_interna": _metricas(modelo, x_prueba, y_prueba),
             "prueba_externa": _metricas(modelo, x_ext, y_ext)}
    config.FICHA_CLASIFICADOR.write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Modelo guardado: {config.MODELO_CLASIFICADOR.name} · sha256 {huella[:16]}…")
    for nombre in ("prueba_interna", "prueba_externa"):
        m = ficha[nombre]
        print(f"{nombre:15} n={m['n']:4} exactitud={m['exactitud']:.3f} f1_macro={m['f1_macro']:.3f}")


if __name__ == "__main__":
    main()
