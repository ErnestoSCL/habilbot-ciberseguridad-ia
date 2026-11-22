# Arquitectura

Cada límite de confianza es un `subgraph` con borde discontinuo. Los controles (en rojo) se pueden activar o desactivar para medir el producto con y sin ellos.

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
        CL["Clasificador de intención<br/><small>src/clasificador/</small>"]
        MOD[("Modelo .joblib<br/>+ huella SHA-256")]
        R["Recuperador TF-IDF<br/><small>src/rag/</small>"]
        ACL["Control: acceso por rol<br/><small>controles/acceso_por_rol.py</small>"]
        AG["Agente: arnés de herramientas<br/><small>src/agente/</small>"]
        PER["Control: diccionario de permisos<br/><small>controles/permisos_herramientas.py</small>"]
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
        M["Modelo de lenguaje<br/>OpenAI<br/><small>src/llm.py</small>"]
    end

    CO -->|usuario y clave| LG
    SE -->|usuario y clave| LG
    LG --- US
    LG -->|sesión + consulta| E
    DOC -->|ingesta: quién, cuándo, hash| E

    E <-->|texto / trámite, confianza, ruta| CL
    CL -. verifica huella .- MOD
    E --->|consulta| R
    R --> CP
    R --> CI
    R -->|fragmentos| ACL
    ACL -->|solo lo que el rol puede ver| E

    E -->|ruta automática| AG
    E -->|ruta revisión| EXP
    AG <-->|herramientas pedidas / resultados| M
    E <-->|prompt / respuesta| M
    AG -->|cada llamada| PER
    PER -->|consultar_estado| PAD
    PER -->|abrir_expediente| EXP
    PER -->|emitir_constancia| CON

    E ---->|cada paso| L

    classDef actor fill:#e8eef7,stroke:#4a6fa5,color:#1c2b40
    classDef control fill:#fdecec,stroke:#8b1a1a,stroke-width:2px,color:#5a1010
    class CO,SE,DOC actor
    class ACL,PER control
    style P fill:#fdf7f7,stroke:#8b1a1a,stroke-width:2px,stroke-dasharray:6 4
    style INT fill:#fffaf0,stroke:#b26b00,stroke-width:2px,stroke-dasharray:6 4
    style EXT fill:#f7f7f7,stroke:#555,stroke-width:2px,stroke-dasharray:6 4
```

## Recorrido de una consulta

1. **Inicio de sesión:** fija usuario, rol y código de colegiado. Todo lo demás usa la sesión, nunca lo que el usuario escribe.
2. **Adjunto (opcional):** su texto entra solo al contexto de esta consulta; no se agrega al índice. En el registro queda quién lo subió, cuándo y su huella SHA-256.
3. **Clasificador de intención:** decide el trámite y la ruta. Por debajo de 0,6 de confianza, o si el trámite es sensible, la ruta es **revisión humana**.
4. **Recuperador:** trae los fragmentos más parecidos; el control de acceso por rol quita los internos si quien pregunta es colegiado.
5. **Ruta automática:** el agente conversa con el modelo, que **propone** herramientas; el arnés las pasa por el diccionario de permisos y **decide** si se ejecutan.
   **Ruta revisión:** el código abre un expediente para Secretaría y el modelo redacta la respuesta.
6. **Registro:** una línea por consulta con la clasificación, los fragmentos (entregados y descartados), cada herramienta (pedida, ejecutada o bloqueada y por qué), el adjunto y la respuesta.

## Límites de confianza

| Límite | Qué cruza | Por qué importa |
|---|---|---|
| Usuario → producto | Credenciales y consultas | Aquí se fija la identidad; entrada de la inyección directa y de la evasión del clasificador |
| Documento adjunto → producto | Texto no confiable que llega al contexto del modelo | Entrada de la inyección indirecta (A1) |
| Producto → datos internos | Fragmentos del corpus interno, lecturas del padrón, escritura de constancias y expedientes | Si no se respeta el rol o los permisos, hay fuga o emisión indebida |
| Producto → proveedor del modelo (OpenAI) | Todo el prompt: fragmentos, adjunto y resultados de herramientas | Es un tercero: lo que se envía sale del producto |

## Decisiones de diseño

- **El modelo propone y el código decide.** Los permisos se aplican en el arnés del agente (`controles/permisos_herramientas.py`), fuera del modelo: una inyección puede cambiar lo que el modelo pide, no lo que el arnés permite.
- **Los controles son enchufables.** El recuperador busca en todo el corpus y el agente acepta cualquier llamada; los controles actúan aparte. Así el mismo catálogo se mide con y sin control.
- **El adjunto no persiste.** Al no entrar al índice, una carga maliciosa no afecta a otros usuarios ni a consultas futuras.
- **Ninguna herramienta ejecuta texto del modelo como código** (no hay `eval`).
- **El modelo del clasificador se verifica antes de cargarse:** `joblib` usa `pickle`, que puede ejecutar código al cargar un archivo alterado.
