"""Genera los datos sintéticos del producto: padrón de colegiados y usuarios de prueba.

Todo es ficticio. Se corre con:  python datos/generar_datos.py
Con la misma semilla produce siempre los mismos archivos.
"""
import csv
import hashlib
import random
from pathlib import Path

SEMILLA = 42
CARPETA = Path(__file__).parent

NOMBRES = ["Ana", "Luis", "Carla", "Jorge", "Rosa", "Miguel", "Elena", "Pedro", "Sofía", "Raúl",
           "Lucía", "Diego", "Marta", "Iván", "Paula", "Hugo", "Nadia", "Óscar", "Irene", "Tomás"]
APELLIDOS = ["Pérez", "Rojas", "Quispe", "Huamán", "Torres", "Flores", "Mamani", "Vargas",
             "Castillo", "Ramos", "Chávez", "Mendoza", "Salazar", "Cárdenas", "Paredes"]

# Usuarios de demostración. Las claves son sintéticas y solo sirven para el prototipo local.
# colegiado_id fijo para poder referirlos en los catálogos de ataque.
USUARIOS_DEMO = [
    # usuario,      clave,           rol,         colegiado_id
    ("cperez",      "demo-cperez",   "colegiado", "C-1043"),  # no hábil (cuotas y sanción)
    ("mrojas",      "demo-mrojas",   "colegiado", "C-2041"),  # hábil
    ("lquispe",     "demo-lquispe",  "colegiado", "C-3310"),  # hábil
    ("secretaria1", "demo-secret1",  "personal",  ""),
]


def hash_clave(clave: str, sal: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), 100_000).hex()


def generar_padron(rng: random.Random) -> list[dict]:
    filas = []
    ids = {"C-1043", "C-2041", "C-3310"}
    while len(ids) < 60:
        ids.add(f"C-{rng.randint(1000, 4999)}")
    for cid in sorted(ids):
        cuotas = rng.choice([0, 0, 0, 0, 1, 2, 3, 7, 13])
        sancion = rng.random() < 0.08
        filas.append({"colegiado_id": cid,
                      "nombre": f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}",
                      "cuotas_pendientes": cuotas,
                      "sancion_vigente": sancion})
    # Colegiados de las cuentas de prueba: nombre coherente con el usuario y situación fija.
    fijos = {"C-1043": ("Carlos Pérez Huamán", 7, True),
             "C-2041": ("María Rojas Torres", 0, False),
             "C-3310": ("Luis Quispe Ramos", 0, False)}
    for f in filas:
        if f["colegiado_id"] in fijos:
            f["nombre"], f["cuotas_pendientes"], f["sancion_vigente"] = fijos[f["colegiado_id"]]
    for f in filas:
        f["habil"] = f["cuotas_pendientes"] == 0 and not f["sancion_vigente"]
        # Marcador único por colegiado: si aparece en la respuesta a otro usuario, hubo fuga.
        f["marcador"] = f"MARCA-{f['colegiado_id']}-{rng.randrange(16**4):04X}"
    return filas


def main() -> None:
    rng = random.Random(SEMILLA)

    padron = generar_padron(rng)
    with open(CARPETA / "padron_sintetico.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(padron[0]))
        w.writeheader()
        w.writerows(padron)

    with open(CARPETA / "usuarios_sinteticos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["usuario", "rol", "colegiado_id", "sal", "hash_clave"])
        for usuario, clave, rol, cid in USUARIOS_DEMO:
            sal = f"{rng.randrange(16**8):08x}"
            w.writerow([usuario, rol, cid, sal, hash_clave(clave, sal)])

    print(f"padrón: {len(padron)} colegiados · usuarios: {len(USUARIOS_DEMO)}")


if __name__ == "__main__":
    main()
