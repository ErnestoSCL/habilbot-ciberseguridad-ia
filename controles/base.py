"""Interfaz común de los controles.

El asistente llama a cada control activo en tres puntos: la entrada del usuario, los fragmentos
recuperados y la respuesta. Un control que no actúa en un punto deja pasar todo sin cambios.
Cada método devuelve también la decisión, que queda en el registro.
"""


class Control:
    nombre = "base"

    def revisar_entrada(self, texto, sesion):
        """Devuelve (texto, motivo_de_bloqueo o None)."""
        return texto, None

    def filtrar_fragmentos(self, fragmentos, sesion):
        """Devuelve (fragmentos_permitidos, ids_descartados)."""
        return fragmentos, []

    def revisar_salida(self, texto, sesion):
        """Devuelve (texto, motivo_de_bloqueo o None)."""
        return texto, None
