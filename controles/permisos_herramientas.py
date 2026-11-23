"""Control del agente: diccionario de permisos aplicado en el arnés, fuera del modelo.

Para cada rol dice qué herramientas puede usar y con qué condiciones. El agente actúa con los
permisos de quien pide (mediación completa), no con los suyos:
  - solo_propio:     el colegiado_id se toma de la sesión, aunque el modelo pida otro (A4, A10);
  - requiere_habil:  la constancia solo se emite si el padrón dice hábil, diga lo que diga el
                     modelo o el documento adjunto (A1).
Una herramienta que no figura para el rol, se bloquea.
"""
from controles.base import Control
from src.agente.herramientas import leer_padron

PERMISOS = {
    "colegiado": {
        "consultar_estado": {"solo_propio": True},
        "emitir_constancia": {"solo_propio": True, "requiere_habil": True},
        "abrir_expediente": {"solo_propio": True},
    },
    "personal": {
        "consultar_estado": {},
        "abrir_expediente": {},
    },
}


class PermisosHerramientas(Control):
    nombre = "permisos_herramientas"

    def autorizar_herramienta(self, herramienta, args, sesion):
        reglas = PERMISOS.get(sesion.rol, {}).get(herramienta)
        if reglas is None:
            return args, f"el rol {sesion.rol} no puede usar {herramienta}"
        args = dict(args)
        if reglas.get("solo_propio"):
            args["colegiado_id"] = sesion.colegiado_id
        if reglas.get("requiere_habil"):
            fila = leer_padron().get(args["colegiado_id"])
            if fila is None or fila["habil"] != "True":
                return args, f"{args['colegiado_id']} no está hábil en el padrón"
        return args, None
