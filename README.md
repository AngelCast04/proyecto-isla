# Redes Semánticas para los Derechos Humanos

Aplicación de **consulta y visualización** sobre un grafo de conocimiento construido a partir de documentos de derechos humanos. Usa el motor [**Fast GraphRAG**](https://github.com/circlemind-ai/fast-graphrag) (Circlemind) para extraer entidades y relaciones, responder preguntas en lenguaje natural y explorar la red semántica en el navegador.

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"/></a>
  <img src="https://img.shields.io/badge/python->=3.10-blue" alt="Python"/>
  <a href="https://github.com/experimentador1/proy-islas"><img src="https://img.shields.io/badge/repositorio-proy--islas-181717?logo=github" alt="GitHub"/></a>
</p>

---

## Descripción del proyecto

Este repositorio integra **GraphRAG** con una **API web (FastAPI)** y una **interfaz** pensada para equipos que trabajan con instrumentos internacionales, poblaciones, tratados, organismos y mecanismos de derechos humanos.

- **Dominio:** análisis de documentos como sistema integrado (poblaciones, derechos, tratados, resoluciones, organismos, mecanismos, conceptos jurídicos, países, órganos).
- **Consultas:** el usuario escribe una pregunta; el sistema recupera contexto del grafo (PageRank y embeddings) y genera una respuesta con **OpenAI** (`gpt-4o-mini` por defecto).
- **Visualización:** grafo interactivo (vis.js) con el subconjunto de nodos y relaciones relevantes para cada consulta; opción de ver la **red completa** almacenada en disco.

---

## Modificaciones respecto al upstream (Fast GraphRAG)

| Área | Cambio |
|------|--------|
| **Branding** | Título y mensajes orientados a *Redes Semánticas para los Derechos Humanos* (sin marcas comerciales del demo original). |
| **API** | `app/main.py`: `POST /api/query`, `GET /api/grafo`, respuesta con explicación, argumentación y subgrafo **impactado** por la consulta. |
| **Frontend** | `visualizer/consulta.html`: layout con header, leyenda **centrada** y **filtros por tipo** de entidad (solo sobre el resultado de la última consulta); **mostrar todos** restaura ese resultado; paneles *Explicación*, *Argumentación*, *Marco normativo*, *Relaciones relevantes*; fondo degradado en el lienzo del grafo; física desactivada tras el layout para que los nodos **permanezcan** al arrastrarlos; botones **Centrar**, **Ver red completa**, **Exportar PDF**, **Nueva consulta**. |
| **Ingesta** | `run_quickstart.py`: un **PDF por documento** desde `libros/` (PyMuPDF) con metadata de origen (`instrumento`, `archivo`); persistencia en `grafo_libros/`. Para recitar el corpus ya indexado: `python run_quickstart.py --reingestar`. |
| **Arranque** | `run_consulta.py`: carga de `.env` por ruta explícita; servidor **Uvicorn** en el puerto **8080**. |
| **Utilidades** | `export_grafo.py` → `visualizer/grafo.json`; `run_visualizer.py` para vista estática sin API; `Iniciar-Servidor.command` (macOS, doble clic). |
| **Documentación local** | `guia-arranque.md` con pasos en español. |

La librería `fast_graphrag/` y los tests originales se mantienen como base del motor RAG.

---

## Requisitos

- Python **3.10–3.12** (recomendado 3.12).
- Cuenta **OpenAI** con API key (`OPENAI_API_KEY`).
- Para construir el grafo desde PDFs: dependencias del proyecto (ver `pyproject.toml`) y **PyMuPDF** (`pymupdf`).

---

## Instalación

```bash
cd fast-graphrag-main   # o el nombre de tu carpeta clonada
python3.12 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install .                # instala fast-graphrag del directorio
pip install pymupdf fastapi uvicorn python-dotenv
```

Copia `.env.example` a `.env` y define tu clave:

```bash
cp .env.example .env
# Edita .env: OPENAI_API_KEY=sk-...
```

---

## Uso rápido

### 1. Construir o actualizar el grafo (PDFs en `libros/`)

```bash
source venv/bin/activate
python run_quickstart.py
```

Genera/actualiza archivos en `grafo_libros/` (grafo igraph, índices vectoriales, chunks). Cada PDF se indexa como documento propio, con el nombre del instrumento y el archivo de origen.

Si el grafo ya existía **sin** esa metadata, recítalo:

```bash
python run_quickstart.py --reingestar
```

### 2. Interfaz web de consultas

```bash
python run_consulta.py
```

Abre **http://localhost:8080**. Escribe una consulta, revisa la respuesta, el grafo impactado y los paneles inferiores.

### 3. Solo visualizar el grafo exportado (sin API key para consultas)

```bash
python export_grafo.py
python run_visualizer.py
```

---

## Estructura relevante

```
├── app/main.py              # API FastAPI
├── visualizer/consulta.html # Interfaz principal
├── libros/                  # PDFs de entrada
├── grafo_libros/            # Grafo y datos persistidos (no versionar secretos)
├── run_consulta.py          # Servidor web
├── run_quickstart.py        # Ingesta desde PDFs
├── export_grafo.py
├── guia-arranque.md
├── fast_graphrag/           # Librería GraphRAG (upstream)
└── Iniciar-Servidor.command # macOS
```

---

## Motor subyacente (Fast GraphRAG)

Fast GraphRAG ofrece grafos interpretables, exploración con **PageRank personalizado**, actualización incremental y pipeline asíncrono tipado. Más detalle en el [repositorio original](https://github.com/circlemind-ai/fast-graphrag) y en la [documentación de Circlemind](https://docs.circlemind.co/quickstart).

Referencias académicas: enfoque relacionado con grafos para RAG, p. ej. [HippoRAG](https://arxiv.org/abs/2405.14831).

---

## Ejemplos de la librería

En la carpeta `examples/` del upstream hay tutoriales (`custom_llm.py`, notebooks de checkpoints y parámetros de consulta).

---

## Despliegue en Render

El repositorio incluye `render.yaml` (Blueprint) listo para crear un servicio web:

- `redes-semanticas-dh` (FastAPI en Python)

La interfaz `visualizer/consulta.html` se sirve desde el mismo backend en `/`.

> Nota: el `render.yaml` actual esta preparado para `plan: free`, por lo que no usa disco persistente.
> Si cambias a un plan pago, puedes volver a agregar `disk` y apuntar `GRAPH_WORKING_DIR` a `/var/data/grafo_libros`.

### Variables de entorno requeridas

En Render debes definir como minimo:

- `OPENAI_API_KEY`.
- `CORS_ORIGINS` (recomendado en produccion), por ejemplo:
  - `https://redes-semanticas-dh.onrender.com`
  - o varios dominios separados por coma.

Para plan gratuito, el backend guarda el grafo en (ruta relativa a la raíz del repo, no al cwd del proceso):

- `GRAPH_WORKING_DIR=grafo_libros` (o `./grafo_libros`; se resuelve igual)

En free tier ese almacenamiento es efimero (puede perderse en reinicios/redeploy), por lo que puede ser necesario volver a desplegar para regenerar el grafo.

### Ingesta en plan gratuito (sin Shell)

En `plan: free` Render no ofrece Shell. Por eso `render.yaml` ejecuta `python run_quickstart.py` al final del **buildCommand**.

- Debes tener **PDFs** en la carpeta `libros/` versionada en el repo (o el build no tendra texto que indexar).
- `OPENAI_API_KEY` debe estar definida en el servicio: en Render suele estar disponible tambien durante el **build** (necesaria para la ingesta).
- El primer build puede tardar bastante (llamadas a OpenAI). Cada redeploy vuelve a ejecutar la ingesta salvo que cambies el flujo (plan Starter con Shell, o disco persistente).

Si pasas a un plan con Shell, puedes quitar `run_quickstart.py` del `buildCommand` y ejecutar la ingesta manualmente cuando quieras.

### Verificacion rapida

Tras desplegar:

- abre `/` para cargar la interfaz.
- prueba `GET /api/grafo` (debe devolver nodos/aristas una vez generado el grafo).
- prueba `POST /api/query` con una consulta.

---

## Despliegue en Vercel (coexiste con Render)

Vercel sirve la misma app FastAPI (`app.main:app`) como Function. **No reemplaza** a Render: `render.yaml` sigue siendo el camino recomendado para ingesta + grafo completo.

1. Conecta el repo en Vercel (Framework Preset: FastAPI / Other).
2. Define variables de entorno: `OPENAI_API_KEY`, y opcionalmente `CORS_ORIGINS`, `CONCURRENT_TASK_LIMIT`.
3. Despliega. El build usa `pyproject.toml` (`[project]`) + `uv`; la entrada está en `[tool.vercel] entrypoint = "app.main:app"`.

Notas:

- `vercel.json` fija `maxDuration` a 60s (consultas GraphRAG pueden ser largas).
- `.vercelignore` excluye `libros/`, tests y `grafo_libros/` para no inflar el bundle.
- Sin `grafo_libros/` en el deploy, `/api/grafo` puede usar el respaldo `visualizer/grafo.json`; las **consultas LLM** requieren el grafo persistido (mejor en Render con disco o build de ingesta).

---

## Licencia

Este proyecto incluye código bajo **MIT License** (ver [LICENSE](LICENSE)), en línea con Fast GraphRAG.

---

## Repositorio

Código publicado en: **[github.com/experimentador1/proy-islas](https://github.com/experimentador1/proy-islas)**
