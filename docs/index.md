# HábilBot

Asistente de trámites de un colegio profesional **ficticio**, construido para el trabajo integrador del curso Ciberseguridad de Inteligencia Artificial (Maestría en Ciencia de Datos, UNI). El grupo lo construye, lo ataca y lo defiende, y mide el efecto de cada control.

!!! warning "Solo datos sintéticos"
    Ninguna institución, persona ni dato de este proyecto es real.

## Qué hace

Un colegiado inicia sesión y escribe su solicitud, con un documento adjunto si quiere. Un **clasificador** decide qué trámite es y si el sistema lo atiende solo o pasa a revisión humana. El asistente recupera los documentos del Colegio y, en los trámites simples, un **agente** consulta el padrón y emite la constancia de habilitación. Todo queda en un registro.

## Primeros resultados (sin control)

| Amenaza | Tasa de éxito del ataque |
|---|---|
| A2 · Fuga del corpus interno | 77 % (IC95 59 %–88 %) |
| A1 · Inyección indirecta por adjunto | 23 % (IC95 12 %–41 %) |
| A6 · Evasión del clasificador | 10 % (IC95 3 %–26 %) |

Detalle en [Evaluación adversarial](evaluacion.md).

## Contenido

| Sección | Estado |
|---|---|
| [Ficha del sistema](ficha.md) | Hito 2 |
| [Arquitectura](arquitectura.md) | Hito 2 |
| [Modelo de amenazas](modelo-de-amenazas.md) | 12 amenazas, con capa MAESTRO |
| [Priorización](priorizacion.md) | Pendiente (sesión 7) |
| [Controles y riesgo residual](controles.md) | Controles implementados descritos |
| [Evaluación adversarial](evaluacion.md) | Primera medición sin control y tres trazas |
| [Clasificación regulatoria](regulatorio.md) | Pendiente (sesión 7) |

## Cómo reproducirlo

Las instrucciones están en el [README del repositorio](https://github.com/ErnestoSCL/habilbot-ciberseguridad-ia#readme).
