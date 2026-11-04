# HábilBot

Trabajo integrador de Ciberseguridad de IA (Maestría en Ciencia de Datos, UNI). Asistente de trámites de un colegio profesional **ficticio**: RAG, clasificador ML y agente con herramientas, con su modelo de amenazas y evaluación adversarial. **Solo datos sintéticos.**

Página del proyecto: https://ernestoscl.github.io/habilbot-ciberseguridad-ia/

## Estado

| Componente | Estado |
|---|---|
| Inicio de sesión con roles | Implementado |
| Asistente con recuperación (RAG) | Implementado |
| Registro de eventos (JSONL) | Implementado |
| Control de acceso por rol | Implementado |
| Clasificador de intención | Pendiente |
| Agente con herramientas | Pendiente |

## Instalación

Requiere Python 3.12.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
```

Complete en `.env` la llave de un proveedor: `OPENAI_API_KEY` (modelo por defecto `gpt-4o-mini`) o `GEMINI_API_KEY` (nivel gratuito de Google AI Studio). El producto usa el que tenga llave. Para probar sin API, ponga `LLM_PROVEEDOR=simulado`: el flujo y el registro funcionan igual, pero la respuesta repite el contexto en lugar de redactarlo.

Los datos sintéticos ya están en el repositorio. Para regenerarlos (misma semilla, mismo resultado):

```bash
python datos/generar_datos.py
```

## Uso

```bash
python -m src.app --usuario mrojas
python -m src.app --usuario cperez --sin-controles
```

Los usuarios de prueba y sus claves sintéticas están en `datos/generar_datos.py` (`USUARIOS_DEMO`). Cada consulta queda en `registros/vivo/eventos.jsonl` (excluido del repositorio; en `registros/` se versiona solo una muestra).

## Página

```bash
mkdocs serve     # vista local en http://127.0.0.1:8000
```

Se publica sola con GitHub Actions en cada push a `main` (Settings → Pages → Source: GitHub Actions).

## Estructura

```
src/          el producto (sesión, asistente, RAG, registro, modelo de lenguaje)
controles/    controles que se activan o desactivan para medir
datos/        corpus y datos sintéticos, con su script generador
evaluacion/   catálogos de ataques, script de evaluación y resultados
registros/    muestra del registro de una corrida
docs/         documentación y fuente de la página
```
