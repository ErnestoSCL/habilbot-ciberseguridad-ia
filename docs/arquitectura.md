# Arquitectura

Cada límite de confianza es un `subgraph` con borde discontinuo. Las cajas grises con borde punteado (clasificador, agente, adjuntos, expedientes y constancias) todavía no están implementadas; se activan en las sesiones 5 y 6.

```mermaid
%%{init: {"themeVariables": {"fontSize": "22px"}}}%%
flowchart TB
    CO["Colegiado"]
    SE["Personal de secretaría"]
    DOC["Documento adjunto"]

    subgraph P["Límite 1: producto"]
        LG["Inicio de sesión<br/><small>src/sesion.py</small>"]
        US[("Usuarios<br/>sintéticos")]
        E["Orquestador / asistente<br/><small>src/asistente.py</small>"]
        CT["Controles<br/><small>controles/</small>"]
        CL["Clasificador ML"]
        R["Recuperador TF-IDF<br/><small>src/rag/</small>"]
        AG["Agente con<br/>herramientas"]
        L[("Registro JSONL<br/><small>src/registro.py</small>")]
        CP[("Corpus público")]

        subgraph INT["Límite 2: datos internos"]
            CI[("Corpus<br/>interno")]
            PAD[("Padrón<br/>sintético")]
            EXP[("Expedientes")]
            CON[("Constancias")]
        end
    end

    subgraph EXT["Límite 3: proveedor externo"]
        M["Modelo de lenguaje<br/>OpenAI o Gemini<br/><small>src/llm.py</small>"]
    end

    CO -->|usuario y clave| LG
    SE -->|usuario y clave| LG
    LG --- US
    LG -->|sesión + consulta| E
    DOC -->|ingesta| E

    E <-->|texto / trámite y ruta| CL
    E -->|aplica| CT
    E <-->|prompt / respuesta| M
    E --->|consulta| R
    CL -->|ruta automática| AG
    E ---->|cada paso| L
    AG --> L

    R --> CP
    R --> CI
    AG -->|consultar_estado| PAD
    AG -->|abrir_expediente| EXP
    AG -->|emitir_constancia| CON

    classDef actor fill:#e8eef7,stroke:#4a6fa5,color:#1c2b40
    classDef pendiente fill:#f4f4f4,stroke:#999,stroke-dasharray:4 3,color:#666
    class CO,SE actor
    class CL,AG,DOC,EXP,CON pendiente
    style P fill:#fdf7f7,stroke:#8b1a1a,stroke-width:2px,stroke-dasharray:6 4
    style INT fill:#fffaf0,stroke:#b26b00,stroke-width:2px,stroke-dasharray:6 4
    style EXT fill:#f7f7f7,stroke:#555,stroke-width:2px,stroke-dasharray:6 4
```

## Límites de confianza

| Límite | Qué cruza | Por qué importa |
|---|---|---|
| Usuario → producto | Credenciales y consultas | Aquí se fija la identidad; entrada de la inyección directa |
| Documento adjunto → producto | Texto no confiable que llegará al contexto del modelo | Entrada de la inyección indirecta |
| Producto → datos internos | Fragmentos del corpus interno, lecturas del padrón, escritura de constancias | Si no se respeta el rol, hay fuga o emisión indebida |
| Producto → proveedor del modelo (OpenAI) | Todo el prompt, incluidos los fragmentos recuperados | Es un tercero: lo que se envía sale del producto |

## Decisión de diseño

El recuperador busca en **todo** el corpus. El filtro por rol es un control aparte (`controles/acceso_por_rol.py`) que actúa sobre los fragmentos antes de que lleguen al modelo. Así se puede medir el producto con y sin ese control sobre el mismo catálogo de consultas.

El modelo de lenguaje propone y el código decide: el rol y el código de colegiado salen de la sesión, no del texto que genera el modelo.
