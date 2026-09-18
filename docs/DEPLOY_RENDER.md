# Despliegue en Render.com

Guía para publicar **Redes Semánticas para los Derechos Humanos** como *Web Service* en [Render](https://render.com).

## Requisitos

- Cuenta en Render (GitHub conectado).
- Repositorio con este código (por ejemplo [proy-islas](https://github.com/experimentador1/proy-islas)).
- API key de OpenAI.

## Opción A — Blueprint (`render.yaml`)

1. En Render: **New +** → **Blueprint**.
2. Conecta el repositorio y selecciona la rama `main`.
3. Render detectará `render.yaml`. Revisa el nombre del servicio y la región.
4. En el paso de variables, introduce **`OPENAI_API_KEY`** (marcada como *secret* en el blueprint con `sync: false`).
5. **Apply** y espera el build. El comando de build usa **Poetry** (`poetry install --only main`) según `poetry.lock`; puede tardar varios minutos por dependencias nativas (`hnswlib`, `igraph`, etc.).

## Opción B — Web Service manual

1. **New +** → **Web Service** → elige el repo.
2. Configuración sugerida:
   - **Runtime:** Python 3
   - **Build command (recomendado, alineado con `render.yaml`):**  
     `pip install --upgrade pip && pip install "poetry>=1.8.3,<2.0" && poetry config virtualenvs.create false && poetry install --only main --no-interaction --no-ansi && pip install fastapi "uvicorn[standard]" pymupdf`  
   - **Alternativa:** `pip install --upgrade pip setuptools wheel && pip install -r requirements.txt` (requiere que el build con `poetry-core` 1.x funcione con `pip install .`).
   - **Start command:**  
     `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **Environment variables:**

   | Clave | Valor / notas |
   |--------|----------------|
   | `PYTHON_VERSION` | `3.12.8` (o la versión que ofrezca Render) |
   | `OPENAI_API_KEY` | Tu clave (secreto) |
   | `GRAPH_WORKING_DIR` | `./grafo_libros` o ruta de un disco persistente (ver abajo) |
   | `CONCURRENT_TASK_LIMIT` | Opcional, ej. `4` |

4. **Create Web Service**.

## Grafo de conocimiento (`grafo_libros/`)

El sistema de archivos del contenedor en Render es **efímero**: al redeploy se pierden los datos que no estén en el repo o en un disco.

Opciones:

1. **Disco persistente (recomendado)**  
   - En el servicio: **Disks** → añade un disco (ej. 1 GB).  
   - Montaje típico: `/var/data`.  
   - Variable de entorno:  
     `GRAPH_WORKING_DIR=/var/data/grafo_libros`  
   - La primera vez la carpeta estará vacía: debes **poblar el grafo** (subir un zip con el contenido de `grafo_libros` y extraerlo vía shell de Render, o ejecutar un job/script que llame a `run_quickstart` con tus PDFs y API key).

2. **Incluir `grafo_libros` en el repositorio (flujo actual)**  
   - El blueprint **no** corre `run_quickstart.py` en el build.  
   - Actualiza el grafo en local y versiona `grafo_libros/` (~21 MB).

3. **Build con datos**  
   - Un script de build que descargue artefactos desde almacenamiento externo (S3, etc.) antes de arrancar — requiere configuración adicional.

Sin archivos válidos en `GRAPH_WORKING_DIR`, la API responderá error en `/api/grafo` y las consultas no tendrán contexto útil hasta que exista `graph_igraph_data.pklz` y el resto de archivos generados por GraphRAG.

## Comprobaciones

- Tras el deploy: abre la URL pública (`https://<servicio>.onrender.com`).
- Debe cargar la interfaz en `/`.
- Si falla el build por compilación de `hnswlib`, revisa los logs; en muchos casos hay *wheels* para Linux. Si no, puede hacer falta imagen Docker propia con herramientas de compilación.

## Costes y límites (plan gratuito)

- El servicio **se duerme** tras inactividad; el primer acceso puede tardar ~30–60 s en “despertar”.
- Límites de CPU/RAM según Render; GraphRAG puede ser exigente en consultas concurrentes.

## Variables opcionales

- `CONCURRENT_TASK_LIMIT` — concurrencia hacia OpenAI (por defecto en código: 4).
