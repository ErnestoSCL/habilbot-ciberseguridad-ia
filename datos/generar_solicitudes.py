"""Genera las solicitudes sintéticas con que se entrena el clasificador de intención.

Dos fuentes, cada fila marca la suya en la columna `origen`:
  - plantillas: frases base con huecos, combinadas con semilla fija (no usa la API);
  - llm: variaciones redactadas una sola vez por el modelo de lenguaje y guardadas en el CSV.

El entrenamiento solo lee el CSV, nunca llama a la API.

    python datos/generar_solicitudes.py              # plantillas + llm (necesita llave en .env)
    python datos/generar_solicitudes.py --sin-llm    # solo plantillas
"""
import argparse
import csv
import itertools
import json
import random
import sys
from pathlib import Path

SEMILLA = 42
CARPETA = Path(__file__).parent
SALIDA = CARPETA / "solicitudes_sinteticas.csv"
POR_CLASE_PLANTILLAS = 75
POR_CLASE_LLM = 40   # por cada estilo; se piden dos estilos por clase
ESTILOS = ["formal y con contexto", "informal, corto o con errores de tipeo"]

SALUDOS = ["", "", "", "Buenas, ", "Hola, ", "Buenos días, ", "Disculpe, ", "Estimados, "]
CIERRES = ["", "", "", " Gracias.", " Por favor.", " Quedo atento.", " Saludos."]

PLANTILLAS = {
    "consulta_general": (
        ["¿cuál es el horario de atención de {lugar}?", "¿dónde queda {lugar}?",
         "quisiera saber qué requisitos piden para {tema}", "¿qué dicen los estatutos sobre {tema}?",
         "¿cómo funciona {tema}?", "tengo una duda sobre {tema}", "¿me pueden explicar {tema}?",
         "¿qué pasa si me sancionan?", "¿quiénes forman el Consejo Directivo?",
         "¿cuáles son los deberes de un colegiado?", "¿qué derechos tengo como colegiado?"],
        {"lugar": ["Secretaría", "la sede", "la caja", "la oficina del Colegio"],
         "tema": ["la colegiatura", "las elecciones del Consejo", "los cursos de capacitación",
                  "el Tribunal de Ética", "el Código de Ética", "la asesoría profesional",
                  "el trámite de colegiatura", "la vigencia de la constancia"]},
    ),
    "constancia_habilitacion": (
        ["necesito mi {doc} para {uso}", "quiero solicitar mi {doc}", "¿me pueden emitir mi {doc}?",
         "requiero el {doc} porque {uso}", "solicito {doc} vigente", "¿cómo obtengo mi {doc}?",
         "me piden el {doc} para {uso}", "emítanme el {doc} por favor",
         "quiero la constancia, ¿estoy hábil para pedirla?"],
        {"doc": ["constancia de habilitación", "certificado de hábil", "constancia de hábil",
                 "constancia de estar hábil", "certificado de habilitación profesional"],
         "uso": ["una licitación", "firmar planos", "mi nuevo trabajo", "presentarla en una obra",
                 "un concurso público", "renovar mi contrato", "un proceso de contratación"]},
    ),
    "pago_cuotas": (
        ["¿cuánto debo de {cosa}?", "quiero pagar {cosa}", "¿cómo pago {cosa}?",
         "¿tengo {cosa} pendientes?", "¿cuánto es {cosa}?", "¿dónde puedo pagar {cosa}?",
         "¿hay descuento si pago {cosa}?", "¿puedo pagar {cosa} por transferencia?"],
        {"cosa": ["mis cuotas", "la cuota mensual", "la cuota anual", "las cuotas atrasadas",
                  "la cuota de este mes", "mis cuotas vencidas", "la cuota adelantada"]},
    ),
    "actualizacion_datos": (
        ["quiero actualizar mi {dato}", "cambié de {dato}, ¿cómo lo actualizo?",
         "necesito corregir mi {dato} en el padrón", "mi {dato} está mal registrado",
         "me mudé y debo cambiar mi {dato}", "solicito la actualización de mi {dato}",
         "¿cómo modifico mi {dato}?"],
        {"dato": ["domicilio", "dirección", "correo electrónico", "número de teléfono",
                  "apellido", "datos de contacto", "lugar de trabajo"]},
    ),
    "reclamo": (
        ["me cobraron {problema}", "quiero presentar un reclamo porque {problema}",
         "tengo una queja: {problema}", "no estoy conforme porque {problema}",
         "reclamo formal: {problema}", "¿dónde reclamo? {problema}"],
        {"problema": ["dos veces la cuota de octubre", "una cuota que ya había pagado",
                      "no me llegó la constancia que pagué", "me atendieron mal en caja",
                      "el sistema me cobró de más", "la constancia salió con mis datos errados",
                      "no responden mis correos desde hace semanas"]},
    ),
    "levantamiento_sancion": (
        ["solicito el levantamiento de mi {sancion}", "quiero que se levante mi {sancion}",
         "ya cumplí {plazo} de mi {sancion}, ¿qué sigo?", "pido mi rehabilitación porque {razon}",
         "¿cómo pido que me quiten la {sancion}?", "ya {razon}, quiero volver a estar hábil",
         "quiero apelar mi {sancion} ante el Tribunal", "¿cuándo termina mi {sancion}?",
         "necesito que revisen mi {sancion} porque {razon}", "¿qué documentos presento para levantar mi {sancion}?",
         "estoy {estado} y quiero regularizar la {sancion}", "solicito revisión anticipada de mi {sancion}"],
        {"sancion": ["suspensión", "sanción", "inhabilitación", "amonestación", "suspensión temporal"],
         "estado": ["suspendido", "inhabilitado", "sancionado"],
         "plazo": ["la mitad del plazo", "tres meses", "el tiempo indicado"],
         "razon": ["reparé el daño", "cumplí lo que pidió el Tribunal", "ya pasó el plazo de la sanción"]},
    ),
}

# Ruta que sigue cada clase (la misma tabla usa el clasificador).
RUTAS = {"consulta_general": "automatica", "constancia_habilitacion": "automatica", "pago_cuotas": "automatica",
         "actualizacion_datos": "revision", "reclamo": "revision", "levantamiento_sancion": "revision"}


def _desde_plantillas(rng: random.Random) -> list[dict]:
    filas = []
    for clase, (frases, huecos) in PLANTILLAS.items():
        candidatas = set()
        for frase in frases:
            nombres = [n for n in huecos if "{" + n + "}" in frase]
            for valores in itertools.product(*(huecos[n] for n in nombres)):
                candidatas.add(frase.format(**dict(zip(nombres, valores))))
        for texto in rng.sample(sorted(candidatas), min(POR_CLASE_PLANTILLAS, len(candidatas))):
            cierre = rng.choice(CIERRES)
            if cierre and texto[-1] not in "?.!":
                texto += "."
            s = rng.choice(SALUDOS) + texto + cierre
            filas.append({"texto": s[0].upper() + s[1:], "clase": clase, "origen": "plantillas"})
    return filas


def _desde_llm(rng: random.Random) -> list[dict]:
    sys.path.insert(0, str(CARPETA.parent))
    from src import llm
    sistema = ("Generas datos sintéticos para entrenar un clasificador. Respondes solo con una lista JSON de cadenas, "
               "sin texto adicional.")
    descripciones = {
        "consulta_general": "dudas generales sobre el Colegio: horarios, estatutos, requisitos, Tribunal, elecciones",
        "constancia_habilitacion": "pedir la constancia o certificado de habilitación (estar hábil) para algún uso",
        "pago_cuotas": "consultar o pagar cuotas, deudas, medios de pago",
        "actualizacion_datos": "cambiar o corregir datos personales registrados (dirección, correo, teléfono)",
        "reclamo": "quejas por cobros, mala atención, constancias erradas o no recibidas",
        "levantamiento_sancion": "pedir que se levante una sanción o suspensión, o la rehabilitación tras una sanción",
    }
    filas = []
    for clase, desc in descripciones.items():
        for estilo in ESTILOS:
            pedido = (f"Escribe {POR_CLASE_LLM} mensajes distintos que un profesional colegiado peruano escribiría al "
                      f"asistente virtual de su colegio profesional para: {desc}. Estilo: {estilo}. No uses nombres de "
                      f"personas ni direcciones reales. Lista JSON de {POR_CLASE_LLM} cadenas.")
            crudo = llm.generar(sistema, pedido).strip().removeprefix("```json").removesuffix("```").strip()
            for texto in json.loads(crudo):
                filas.append({"texto": str(texto).strip(), "clase": clase, "origen": "llm"})
    return filas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sin-llm", action="store_true", help="genera solo desde plantillas")
    args = parser.parse_args()

    rng = random.Random(SEMILLA)
    filas = _desde_plantillas(rng)
    if not args.sin_llm:
        filas += _desde_llm(rng)

    vistos, unicas = set(), []
    for f in filas:
        clave = f["texto"].lower()
        if f["texto"] and clave not in vistos:
            vistos.add(clave)
            unicas.append(f)

    with open(SALIDA, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["texto", "clase", "origen"])
        w.writeheader()
        w.writerows(unicas)
    conteo = {c: sum(f["clase"] == c for f in unicas) for c in PLANTILLAS}
    print(f"{len(unicas)} solicitudes · {conteo}")


if __name__ == "__main__":
    main()
