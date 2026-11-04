# Arquitectura

Cada límite de confianza es un `subgraph`. Las cajas grises con borde punteado todavía no están implementadas; se activan en las sesiones 5 y 6.

```mermaid
flowchart LR
    CO[Colegiado] -->|usuario y clave| LG
    SE[Personal de secretaría] -->|usuario y clave| LG
    DOC[Documento adjunto del colegiado] -->|ingesta| E

    subgraph P["Límite 1: producto"]
        LG[Inicio de sesión<br/>src/sesion.py] -->|sesión + consulta| E
        LG --> US[(Usuarios sintéticos)]
        E[Orquestador / asistente<br/>src/asistente.py] -->|controles activos| CT[Controles<br/>controles/]
        E -->|texto| CL[Clasificador ML]
        CL -->|trámite, ruta, confianza| E
        E -->|consulta| R[Recuperador TF-IDF<br/>src/rag/recuperador.py]
        R --> CP[(Corpus público)]
        E -->|si ruta automática| AG[Agente con herramientas]
        E -->|escribe cada paso| L[(Registro JSONL<br/>src/registro.py)]
        AG -->|escribe| L

        subgraph INT["Límite 2: datos internos"]
            CI[(Corpus interno)]
            PAD[(Padrón sintético)]
            EXP[(Expedientes)]
            CON[(Constancias emitidas)]
        end

        R --> CI
        AG -->|consultar_estado| PAD
        AG -->|abrir_expediente| EXP
        AG -->|emitir_constancia| CON
    end

    subgraph EXT["Límite 3: proveedor externo"]
        M[Modelo de lenguaje<br/>OpenAI o Gemini<br/>src/llm.py]
    end
    E -->|prompt + contexto| M
    M -->|respuesta| E

    classDef pendiente fill:#eeeeee,stroke:#888,stroke-dasharray:4 3,color:#555
    class CL,AG,DOC,EXP,CON pendiente
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
