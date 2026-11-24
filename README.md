# HábilBot

Trabajo integrador de Ciberseguridad de IA (Maestría en Ciencia de Datos, UNI). Asistente de trámites de un colegio profesional **ficticio**: RAG, clasificador ML y agente con herramientas, con su modelo de amenazas y evaluación adversarial. **Solo datos sintéticos.**

Página del proyecto: https://ernestoscl.github.io/habilbot-ciberseguridad-ia/

## Estado

| Componente | Estado |
|---|---|
| Inicio de sesión con roles | Implementado |
| Asistente con recuperación (RAG) | Implementado |
| Clasificador de intención (ML clásico) | Implementado |
| Agente con herramientas | Implementado |
| Registro de eventos (JSONL) | Implementado |
| Controles: acceso por rol, diccionario de permisos, huella del modelo | Implementados |
| Evaluación adversarial | Primera medición sin control |

## Instalación

Requiere Python 3.12.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
```

Complete en `.env` la llave `OPENAI_API_KEY` (modelo por defecto `gpt-4o-mini`). El agente usa la interfaz de herramientas de OpenAI. Para probar sin API, ponga `LLM_PROVEEDOR=simulado`: el flujo y el registro funcionan igual, pero no se redactan respuestas ni se eligen herramientas.

Los datos sintéticos y el modelo del clasificador ya están en el repositorio. Para regenerarlos (misma semilla):

```bash
python datos/generar_datos.py              # padrón y usuarios de prueba
python datos/generar_solicitudes.py        # solicitudes para el clasificador (usa la API; --sin-llm para solo plantillas)
python -m src.clasificador.entrenar        # entrena y guarda modelos/clasificador_v1.joblib con su huella
```

## Uso

```bash
python -m src.app --usuario mrojas
python -m src.app --usuario cperez --sin-controles
```

Los usuarios de prueba y sus claves sintéticas están en `datos/generar_datos.py` (`USUARIOS_DEMO`). Dentro de la consola:

- escriba su consulta; verá el trámite detectado, la ruta y las herramientas que usó el agente;
- `/adjuntar datos/adjuntos/sustento_legitimo.txt` adjunta un documento a la siguiente consulta (pruebe también `sustento_envenenado.txt` con `cperez`, con y sin `--sin-controles`).

Cada consulta queda en `registros/vivo/eventos.jsonl` (excluido del repositorio). Las constancias y expedientes que crea el agente quedan en `estado/` (también excluido).

## Cómo se ve

Sesiones reales de la consola (más capturas y su explicación en la página: [Cómo se usa](https://ernestoscl.github.io/habilbot-ciberseguridad-ia/uso/)).

Un colegiado hábil pide su constancia con un comprobante adjunto: el agente consulta el padrón y la emite.

![Constancia con adjunto](docs/img/uso_02_constancia.png)

Un colegiado no hábil adjunta un comprobante con un resultado falso del padrón. Sin controles, el agente emite la constancia:

![Ataque sin control](docs/img/uso_04_ataque_sin_control.png)

Con el diccionario de permisos, la emisión se bloquea (aunque el texto del modelo todavía repite la mentira del adjunto):

![Ataque con control](docs/img/uso_05_ataque_con_control.png)

## Evaluación adversarial

```bash
python -m evaluacion.correr_evaluacion --controles ninguno     # sin controles
python -m evaluacion.correr_evaluacion --controles todos       # con controles
python -m evaluacion.trazas                                    # las tres trazas: limpia, comprometida, restringida
```

Los catálogos están en `evaluacion/catalogo/`; cada corrida deja un JSON y un gráfico en `evaluacion/resultados/` y una muestra del registro en `registros/`.

## Pruebas

```bash
python -m pytest
```

Corren en modo simulado, sin API.

## Página

```bash
mkdocs serve     # vista local en http://127.0.0.1:8000
```

Se publica sola con GitHub Actions en cada push a `main`.

## Estructura

```
src/          el producto: sesión, asistente, RAG, clasificador, agente, registro, modelo de lenguaje
controles/    controles que se activan o desactivan para medir
datos/        corpus, datos sintéticos y adjuntos de ejemplo, con sus scripts generadores
modelos/      modelo entrenado del clasificador, con métricas y huella SHA-256
evaluacion/   catálogos de ataques, scripts de evaluación y resultados
registros/    trazas del hito 2 y muestra del registro de una corrida de ataque
tests/        pruebas automáticas
docs/         documentación y fuente de la página
```
