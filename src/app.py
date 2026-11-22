"""Punto de entrada por consola.

    python -m src.app --usuario mrojas
    python -m src.app --usuario cperez --sin-controles

Dentro de la consola:
    /adjuntar ruta/al/archivo.txt   adjunta un documento a la siguiente consulta
"""
import argparse
import getpass
from pathlib import Path

from controles.acceso_por_rol import AccesoPorRol
from controles.permisos_herramientas import PermisosHerramientas
from src.asistente import responder
from src.sesion import iniciar_sesion

CONTROLES = [AccesoPorRol(), PermisosHerramientas()]
MAX_ADJUNTO = 20_000  # caracteres


def main() -> None:
    parser = argparse.ArgumentParser(description="HábilBot: asistente de trámites (prototipo con datos sintéticos)")
    parser.add_argument("--usuario", required=True)
    parser.add_argument("--sin-controles", action="store_true", help="desactiva los controles (para comparar)")
    args = parser.parse_args()

    sesion = iniciar_sesion(args.usuario, getpass.getpass("Clave: "))
    controles = [] if args.sin_controles else CONTROLES
    print(f"Sesión iniciada: {sesion.usuario} ({sesion.rol}). Controles: {[c.nombre for c in controles] or 'ninguno'}")
    print("Escriba su consulta (vacío para salir). Para adjuntar un documento: /adjuntar ruta.txt")
    adjunto = None
    while True:
        consulta = input("\n> ").strip()
        if not consulta:
            break
        if consulta.startswith("/adjuntar "):
            ruta = Path(consulta.removeprefix("/adjuntar ").strip().strip('"'))
            try:
                adjunto = {"nombre": ruta.name, "texto": ruta.read_text(encoding="utf-8")[:MAX_ADJUNTO]}
                print(f"Adjunto listo: {ruta.name}. Se enviará con su siguiente consulta.")
            except OSError as e:
                print(f"No se pudo leer el archivo: {e}")
            continue
        evento = responder(consulta, sesion, controles, adjunto)
        adjunto = None
        c = evento["clasificacion"]
        print(f"[trámite: {c['clase']} · confianza {c['confianza']} · ruta {c['ruta']}]")
        for h in evento["herramientas"]:
            estado = "bloqueada: " + h["motivo"] if h["bloqueada_por"] else "ejecutada"
            print(f"[herramienta {h['herramienta']} · {estado}]")
        print(evento["respuesta"])


if __name__ == "__main__":
    main()
