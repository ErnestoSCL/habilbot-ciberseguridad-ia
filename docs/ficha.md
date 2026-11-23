# Ficha del sistema

**HábilBot** es el asistente virtual de trámites del *Colegio de Profesionales del Ande* (CPA), una institución **ficticia**. Todo el producto usa datos sintéticos.

## Para qué sirve y a quién

Atiende a los colegiados y al personal de Secretaría. Responde consultas sobre estatutos, requisitos, cuotas y habilitación profesional; clasifica cada solicitud y, si es un trámite simple, la resuelve sin intervención humana (por ejemplo, emite la constancia de habilitación a un colegiado hábil). Los trámites sensibles, como el levantamiento de una sanción, pasan a revisión del personal mediante un expediente.

## Componentes

| Componente | Qué hace | Estado |
|---|---|---|
| Modelo de lenguaje con recuperación (RAG) | Responde con los documentos del Colegio (TF-IDF sobre el corpus; OpenAI `gpt-4o-mini` redacta) | Implementado |
| Clasificador de intención (ML clásico) | Decide el tipo de trámite (6 clases) y la ruta: automática o revisión humana. TF-IDF + regresión logística | Implementado |
| Agente con herramientas | Consulta el padrón, emite constancias y abre expedientes; el modelo propone y el arnés decide | Implementado |
| Inicio de sesión | Fija usuario, rol y código de colegiado | Implementado |
| Registro de eventos | Guarda cada consulta, el adjunto (quién, cuándo, huella), la clasificación, los fragmentos, cada herramienta y la respuesta | Implementado |

## Datos que usa y de dónde vienen

| Dato | Origen | Nivel |
|---|---|---|
| Estatutos, reglamento de habilitación, trámites, cuotas, preguntas frecuentes | Escritos para el proyecto (`datos/corpus/publico/`) | Público |
| Procedimiento de sanciones, reporte de morosidad | Escritos para el proyecto (`datos/corpus/interno/`), con marcadores canario | Interno |
| Padrón de 60 colegiados | Generado por `datos/generar_datos.py` (semilla fija) | Interno |
| Usuarios de prueba | Generados por `datos/generar_datos.py`; claves guardadas como hash | Interno |
| 805 solicitudes etiquetadas para entrenar el clasificador | Generadas por `datos/generar_solicitudes.py` (plantillas + variaciones redactadas una vez por el modelo) | Interno |
| 60 solicitudes de prueba externa | Redactadas a mano (`datos/solicitudes_prueba_externa.csv`) | Interno |
| Constancias y expedientes | Los escriben las herramientas del agente en `estado/` (no se versiona) | Interno |
| Documentos adjuntos | Los sube el colegiado; solo entran al contexto de esa consulta | No confiable |

Ningún dato corresponde a personas o instituciones reales.

## Quién lo usa y con qué permisos

| Rol | Ve | Puede hacer (a través del agente) |
|---|---|---|
| Colegiado | Corpus público y su propia situación | Consultar su estado, pedir su constancia (solo si está hábil), adjuntar documentos, abrir expedientes de sus trámites |
| Personal de Secretaría | Además, el corpus interno | Consultar el estado de cualquier colegiado y abrir expedientes; no emite constancias por el asistente |

La identidad y el rol salen del inicio de sesión, nunca de lo que el usuario escribe. Los permisos de las herramientas los aplica el código (`controles/permisos_herramientas.py`), no el modelo.
