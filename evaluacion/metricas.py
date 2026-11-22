"""Tasas con intervalo de Wilson al 95 %, en total y por categoría."""
import math
from collections import defaultdict

Z95 = 1.959964


def wilson(exitos: int, n: int, z: float = Z95) -> tuple[float, float, float]:
    """Devuelve (tasa, límite inferior, límite superior)."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = exitos / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    margen = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return p, max(0.0, centro - margen), min(1.0, centro + margen)


def tasa(exitos: int, n: int) -> dict:
    p, bajo, alto = wilson(exitos, n)
    return {"exitos": exitos, "n": n, "tasa": round(p, 4), "ic95": [round(bajo, 4), round(alto, 4)]}


def resumen(resultados: list[dict], clave: str = "exito") -> dict:
    """resultados: filas con 'categoria' y un booleano en `clave`."""
    por_categoria = defaultdict(list)
    for r in resultados:
        por_categoria[r["categoria"]].append(r[clave])
    return {"total": tasa(sum(r[clave] for r in resultados), len(resultados)),
            "por_categoria": {c: tasa(sum(v), len(v)) for c, v in sorted(por_categoria.items())}}
