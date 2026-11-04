"""Recuperador del RAG: divide el corpus en fragmentos por sección y los ordena por similitud TF-IDF.

Cada fragmento lleva su nivel ("publico" o "interno") según la carpeta de origen.
El recuperador NO filtra por rol: ese filtro es un control (controles/acceso_por_rol.py),
para poder medir el producto con y sin él.
"""
from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src import config


@dataclass(frozen=True)
class Fragmento:
    id: str          # "<documento>#<n>"
    nivel: str       # "publico" o "interno"
    titulo: str
    texto: str


def _dividir(nombre: str, nivel: str, contenido: str) -> list[Fragmento]:
    secciones = contenido.split("\n## ")
    encabezado = secciones[0].splitlines()[0].lstrip("# ").strip()
    fragmentos = []
    for n, sec in enumerate(secciones[1:], start=1):
        titulo, _, cuerpo = sec.partition("\n")
        texto = f"{encabezado} — {titulo.strip()}\n{cuerpo.strip()}"
        fragmentos.append(Fragmento(f"{nombre}#{n}", nivel, titulo.strip(), texto))
    return fragmentos


@lru_cache(maxsize=1)
def _indice():
    fragmentos = []
    for nivel in ("publico", "interno"):
        for ruta in sorted((config.CORPUS / nivel).glob("*.md")):
            fragmentos += _dividir(ruta.stem, nivel, ruta.read_text(encoding="utf-8"))
    vectorizador = TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2), sublinear_tf=True)
    matriz = vectorizador.fit_transform(f.texto for f in fragmentos)
    return fragmentos, vectorizador, matriz


def recuperar(consulta: str) -> list[tuple[Fragmento, float]]:
    """Todos los fragmentos con similitud > 0, de mayor a menor."""
    fragmentos, vectorizador, matriz = _indice()
    similitudes = cosine_similarity(vectorizador.transform([consulta]), matriz)[0]
    orden = similitudes.argsort()[::-1]
    return [(fragmentos[i], float(similitudes[i])) for i in orden if similitudes[i] > 0]
