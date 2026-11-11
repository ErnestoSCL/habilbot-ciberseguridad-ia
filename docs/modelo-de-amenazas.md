# Modelo de amenazas

Una fila por amenaza. Las columnas que el curso todavía no ha visto se completan en su sesión: STRIDE (2), control (4), capa MAESTRO (5). La «señal en el registro» se contrasta con una corrida real del producto.

Los identificadores (A1, A2…) son fijos: no cambian al priorizar ni al agregar filas. Toda la documentación, los catálogos de ataque y los resultados usan estos mismos números.

| # | Amenaza | Activo afectado | Propiedad que rompe | Por dónde entra | Señal en el registro | Tipo STRIDE | Capa MAESTRO | Control | Prioridad |
|---|---|---|---|---|---|---|---|---|---|
| A1 | Inyección indirecta: un documento adjunto contiene instrucciones que llevan al agente a emitir una constancia a un colegiado no hábil | Constancias emitidas | Integridad | Documento adjunto | Pendiente de contrastar (requiere el agente) | Elevación de privilegios | Pendiente | Propuesto: la herramienta verifica el padrón + detector de inyección en adjuntos | Pendiente |
| A2 | Fuga del corpus interno: un colegiado obtiene criterios de sanciones o datos de morosidad | Corpus interno | Confidencialidad | Consulta del usuario | Queda: `fragmentos_recuperados` con `nivel: interno` en una sesión de colegiado. No queda: si el modelo parafrasea sin el canario | Divulgación de información | Pendiente | Acceso por rol en fragmentos (implementado) | Pendiente |
| A3 | Inyección directa: el usuario pide ignorar las instrucciones o revelar el prompt del sistema | Prompt del sistema, comportamiento del asistente | Confidencialidad, integridad | Consulta del usuario | Pendiente de contrastar | Divulgación / manipulación | Pendiente | Propuesto: detector de entrada | Pendiente |
| A4 | Suplantación por texto: «soy personal de secretaría, muéstrame…» | Corpus interno, datos de otros colegiados | Confidencialidad | Consulta del usuario | Queda: el `rol` registrado es el de la sesión, no el declarado | Suplantación | Pendiente | Rol tomado de la sesión (diseño) | Pendiente |
| A5 | Llave de la API expuesta en el repositorio | Cuenta del proveedor del modelo | Confidencialidad | Historial de git | No queda en el registro del producto | Divulgación de información | Pendiente | `.env` excluido por `.gitignore` | Pendiente |
| A6 | Evasión del clasificador: un pedido sensible (p. ej. levantamiento de sanción) redactado como trámite simple para evitar la revisión humana | Decisión de ruta del clasificador | Integridad | Consulta del usuario | Pendiente (requiere el clasificador) | Manipulación | Pendiente | Propuesto: umbral de confianza + palabras clave que fuerzan revisión | Pendiente |
| A7 | Archivo del modelo manipulado: se reemplaza `clasificador_v1.joblib` por uno alterado, que además ejecuta código al cargarse | Clasificador, entorno de ejecución | Integridad | Archivos del repositorio | Pendiente (requiere el clasificador) | Manipulación / elevación de privilegios | Pendiente | Propuesto: verificación de hash SHA-256 antes de cargar | Pendiente |
| A8 | Envenenamiento de los datos de entrenamiento: filas mal etiquetadas a propósito para que el clasificador mande trámites sensibles a la ruta automática | Datos de entrenamiento, clasificador | Integridad | `datos/solicitudes_sinteticas.csv` | Pendiente (requiere el clasificador) | Manipulación | Pendiente | Pendiente | Pendiente |

Filas pendientes por tema: agente (abuso de herramientas), identidad y memoria (sesión 6).
