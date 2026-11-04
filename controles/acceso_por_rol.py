"""Control de la amenaza «fuga del corpus interno»: solo el rol personal recibe fragmentos internos.

Actúa sobre los fragmentos recuperados, antes de que lleguen al modelo de lenguaje.
El rol sale de la sesión, no del texto de la consulta.
"""
from controles.base import Control


class AccesoPorRol(Control):
    nombre = "acceso_por_rol"

    def filtrar_fragmentos(self, fragmentos, sesion):
        if sesion.rol == "personal":
            return fragmentos, []
        permitidos = [(f, s) for f, s in fragmentos if f.nivel == "publico"]
        descartados = [f.id for f, _ in fragmentos if f.nivel != "publico"]
        return permitidos, descartados
