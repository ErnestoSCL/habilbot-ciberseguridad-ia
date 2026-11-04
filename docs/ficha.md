# Ficha del sistema

**HábilBot** es el asistente virtual de trámites del *Colegio de Profesionales del Ande* (CPA), una institución **ficticia**. Todo el producto usa datos sintéticos.

## Para qué sirve y a quién

Atiende a los colegiados y al personal de Secretaría. Responde consultas sobre estatutos, requisitos, cuotas y habilitación profesional; clasifica cada solicitud y, si es un trámite simple, la resuelve sin intervención humana (por ejemplo, emite la constancia de habilitación a un colegiado hábil). Los trámites sensibles, como el levantamiento de una sanción, pasan a revisión del personal.

## Componentes

| Componente | Qué hace | Estado |
|---|---|---|
| Modelo de lenguaje con recuperación (RAG) | Responde con los documentos del Colegio | Implementado |
| Clasificador de intención (ML clásico) | Decide el tipo de trámite y la ruta: automática o revisión humana | Pendiente (hito 2) |
| Agente con herramientas | Consulta el padrón, abre expedientes y emite constancias | Pendiente (sesión 5) |
| Inicio de sesión | Fija usuario, rol y código de colegiado | Implementado |
| Registro de eventos | Guarda cada consulta, fragmentos, decisiones de controles, herramientas y respuesta | Implementado |

## Datos que usa y de dónde vienen

| Dato | Origen | Nivel |
|---|---|---|
| Estatutos, reglamento de habilitación, trámites, cuotas, preguntas frecuentes | Escritos para el proyecto (`datos/corpus/publico/`) | Público |
| Procedimiento de sanciones, reporte de morosidad | Escritos para el proyecto (`datos/corpus/interno/`), con marcadores canario | Interno |
| Padrón de 60 colegiados | Generado por `datos/generar_datos.py` (semilla fija) | Interno |
| Usuarios de prueba | Generados por `datos/generar_datos.py`; claves guardadas como hash | Interno |

Ningún dato corresponde a personas o instituciones reales.

## Quién lo usa y con qué permisos

| Rol | Ve | Puede |
|---|---|---|
| Colegiado | Corpus público y su propia situación | Consultar, solicitar trámites, adjuntar documentos |
| Personal de Secretaría | Además, el corpus interno | Revisar expedientes y trámites sensibles |

La identidad y el rol salen del inicio de sesión, nunca de lo que el usuario escribe.
