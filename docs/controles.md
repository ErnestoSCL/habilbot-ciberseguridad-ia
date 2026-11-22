# Controles y riesgo residual

!!! note "Estado: hito 2"
    Están descritos los controles implementados. La medición con control, la tasa de falsos positivos de cada uno y el riesgo residual se completan en la sesión 7.

Siguiendo la sesión 5, se prefieren **reglas fijas fuera del modelo** (un permiso da el mismo resultado cada vez) sobre controles que dependen de que un modelo acierte.

## Implementados

| Control | Dónde actúa | Amenazas | Qué detecta o impide | Qué deja pasar |
|---|---|---|---|---|
| **Acceso por rol** (`controles/acceso_por_rol.py`) | Sobre los fragmentos recuperados, antes de que lleguen al modelo | A2, A4 | Que un colegiado reciba cualquier fragmento del corpus interno, sin importar cómo formule la pregunta | Información interna que esté copiada en un documento público; permisos mal etiquetados en el corpus (sesión 4) |
| **Diccionario de permisos** (`controles/permisos_herramientas.py`) | En el arnés del agente, antes de ejecutar cada herramienta | A1, A10, A4 | Constancias a colegiados no hábiles (consulta el padrón por su cuenta) y acciones a nombre de otro colegiado (toma el código de la sesión) | Lo que el modelo **dice** en la respuesta: una orden escondida todavía puede cambiar el texto aunque no logre la acción |
| **Verificación de huella** (`src/clasificador/predecir.py`) | Al cargar el modelo del clasificador | A7 | Un archivo de modelo cambiado después de entrenarlo | Un modelo envenenado antes de calcular la huella (sesión 2) |
| **Umbral de confianza** (`src/config.py`, 0,6) | En la decisión de ruta del clasificador | A6 | Textos ambiguos: van a revisión humana | Pedidos sensibles redactados con mucha confianza hacia una clase automática; además manda a revisión algunas consultas legítimas |
| **Registro de ingesta** (`src/asistente.py`) | Al recibir un adjunto | A11 | Quién subió cada adjunto, cuándo y su huella | El contenido del adjunto, que no se guarda |

## Propuestos

| Control | Amenazas | Idea |
|---|---|---|
| Detector de inyección sobre adjuntos, como alerta | A1, A3 | Clasificador que marca texto con forma de orden; según la sesión 4, como alerta registrada y no como barrera, por sus falsos positivos en español |
| Palabras clave que fuerzan revisión | A6 | «sanción», «suspensión», «levantar», «rehabilitación» → revisión humana aunque la clase sea automática |
| Límite de consultas por usuario y minuto | A9 | Evita la saturación y el gasto de cuota |
| Validación de salida | A12 | Si la interfaz pasa a web: no cargar imágenes ni enlaces de otros sitios |
