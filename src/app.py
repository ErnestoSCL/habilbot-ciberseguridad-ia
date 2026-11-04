"""Punto de entrada por consola.

    python -m src.app --usuario mrojas
    python -m src.app --usuario cperez --sin-controles
"""
import argparse
import getpass

from controles.acceso_por_rol import AccesoPorRol
from src.asistente import responder
from src.sesion import iniciar_sesion

CONTROLES = [AccesoPorRol()]


def main() -> None:
    parser = argparse.ArgumentParser(description="HábilBot: asistente de trámites (prototipo con datos sintéticos)")
    parser.add_argument("--usuario", required=True)
    parser.add_argument("--sin-controles", action="store_true", help="desactiva los controles (para comparar)")
    args = parser.parse_args()

    sesion = iniciar_sesion(args.usuario, getpass.getpass("Clave: "))
    controles = [] if args.sin_controles else CONTROLES
    print(f"Sesión iniciada: {sesion.usuario} ({sesion.rol}). Controles: {[c.nombre for c in controles] or 'ninguno'}")
    print("Escriba su consulta (vacío para salir).")
    while True:
        consulta = input("\n> ").strip()
        if not consulta:
            break
        evento = responder(consulta, sesion, controles)
        print(evento["respuesta"])


if __name__ == "__main__":
    main()
