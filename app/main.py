"""API FastAPI para consultas GraphRAG con visualización de grafo impactado."""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.formatters import humanizar_relacion

# Raíz del proyecto (no depender del cwd de uvicorn en Render/Docker)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
VISUALIZER_DIR = _PROJECT_ROOT / "visualizer"


def _resolve_working_dir() -> str:
    """GRAPH_WORKING_DIR relativo a la raíz del repo; evita fallos si el cwd no es el proyecto."""
    raw = (os.getenv("GRAPH_WORKING_DIR") or "grafo_libros").strip() or "grafo_libros"
    p = Path(raw)
    if p.is_absolute():
        return str(p)
    return str((_PROJECT_ROOT / p).resolve())


# Configuración (misma que run_quickstart.py). En Render: disco persistente vía GRAPH_WORKING_DIR
WORKING_DIR = _resolve_working_dir()
DOMAIN = (
    "Analiza instrumentos internacionales y documentos de derechos humanos como un sistema integrado. "
    "Identifica estructuras jerárquicas: categorías generales (poblaciones, derechos) y sus desgloses "
    "a instrumentos, organismos, mecanismos y casos concretos."
)
EXAMPLE_QUERIES = [
    "¿Qué poblaciones vulnerables y derechos se cubren en los documentos?",
    "¿Qué instrumentos protegen a personas indígenas?",
    "¿Cuáles son los mecanismos de la ONU para migrantes y refugiados?",
]
ENTITY_TYPES = [
    "Población", "Derecho", "Tratado", "Resolución",
    "Organismo", "Mecanismo", "Concepto_Jurídico", "País", "Órgano",
]


def _get_cors_origins() -> list[str]:
    """Resuelve CORS_ORIGINS desde env (CSV) o usa wildcard por defecto."""
    raw = os.getenv("CORS_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["*"]


CORS_ORIGINS = _get_cors_origins()

app = FastAPI(title="GraphRAG Consultas")


class NoCacheHTMLMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if (
            request.url.path in ("/", "/consulta")
            or request.url.path.endswith(".html")
            or request.url.path.startswith("/l-assets/")
        ):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


app.add_middleware(NoCacheHTMLMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# GraphRAG se carga al iniciar (lazy para evitar errores si no hay API key)
_grag = None
_orchestrator = None


def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from app.agents import QueryOrchestrator
        _orchestrator = QueryOrchestrator(working_dir=WORKING_DIR)
    return _orchestrator


def get_grag():
    global _grag
    if _grag is None:
        from fast_graphrag import GraphRAG
        from fast_graphrag._llm import OpenAIEmbeddingService, OpenAILLMService
        _grag = GraphRAG(
            working_dir=WORKING_DIR,
            domain=DOMAIN,
            example_queries="\n".join(EXAMPLE_QUERIES),
            entity_types=ENTITY_TYPES,
            config=GraphRAG.Config(
                llm_service=OpenAILLMService(
                    model="gpt-4o-mini",
                    max_requests_concurrent=int(os.getenv("CONCURRENT_TASK_LIMIT", "4")),
                    rate_limit_per_minute=True,
                    max_requests_per_minute=30,
                    rate_limit_concurrency=True,
                ),
                embedding_service=OpenAIEmbeddingService(
                    max_requests_concurrent=4,
                    rate_limit_per_minute=True,
                    max_requests_per_minute=60,
                    rate_limit_concurrency=True,
                ),
            ),
        )
    return _grag


@app.on_event("startup")
async def warmup_grag():
    """Crea GraphRAG/Semaphores en el event loop de uvicorn (evita bound to a different event loop)."""
    if not os.getenv("OPENAI_API_KEY"):
        return
    try:
        get_grag()
        get_orchestrator()
    except Exception:
        # Sin grafo o sin key: el endpoint /api/query reportará el error al consultar
        pass


class QueryRequest(BaseModel):
    query: str


def _load_grafo_desde_json(json_path: Path) -> dict:
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "nodes" not in data:
        raise HTTPException(status_code=500, detail="grafo.json tiene un formato inválido.")
    return data


def _load_grafo_desde_pklz(graph_path: Path) -> dict:
    try:
        import igraph as ig
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="igraph no está instalado. Usa el entorno virtual o ejecuta export_grafo.py.",
        ) from exc

    g = ig.Graph.Read_Picklez(str(graph_path))
    nodes = []
    for v in g.vs:
        attrs = v.attributes()
        name = str(attrs.get("name", ""))
        tipo = attrs.get("type", "Otro")
        desc = attrs.get("description", "")
        nodes.append({
            "id": name,
            "label": name[:50] + ("..." if len(name) > 50 else ""),
            "title": f"{tipo}\n{desc}"[:500],
            "group": tipo,
            "description": desc,
        })
    edges = []
    for e in g.es:
        attrs = e.attributes()
        desc = humanizar_relacion(attrs.get("description", "") or "")
        edges.append({
            "from": g.vs[e.source]["name"],
            "to": g.vs[e.target]["name"],
            "label": desc[:100],
            "title": desc,
        })
    return {"nodes": nodes, "edges": edges}


def _humanizar_relaciones_grafo(data: dict) -> dict:
    """Normaliza etiquetas técnicas de aristas (p. ej. «is») en todo el grafo."""
    for edge in data.get("edges") or []:
        desc = humanizar_relacion(edge.get("title") or edge.get("label") or "")
        edge["title"] = desc
        edge["label"] = desc[:100]
    return data


def _load_grafo() -> dict:
    """Fuente canónica: graph_igraph_data.pklz (como en Render). grafo.json solo como respaldo."""
    graph_path = Path(WORKING_DIR) / "graph_igraph_data.pklz"
    if graph_path.exists():
        return _humanizar_relaciones_grafo(_load_grafo_desde_pklz(graph_path))

    json_path = VISUALIZER_DIR / "grafo.json"
    if json_path.exists():
        return _humanizar_relaciones_grafo(_load_grafo_desde_json(json_path))

    raise HTTPException(
        status_code=404,
        detail="Grafo no encontrado. Ejecuta run_quickstart.py o export_grafo.py primero.",
    )


def _grafo_stats(data: dict) -> dict:
    nodes = data.get("nodes") or []
    edges = data.get("edges") or []
    groups: dict[str, int] = {}
    for node in nodes:
        group = str(node.get("group") or "Otro")
        groups[group] = groups.get(group, 0) + 1
    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "groups": groups,
    }


@app.get("/api/grafo/stats")
def get_grafo_stats():
    """Estadísticas ligeras del grafo para el landing."""
    return _grafo_stats(_load_grafo())


@app.get("/api/grafo")
def get_grafo_completo():
    """Devuelve el grafo completo en formato JSON para vis.js."""
    return _load_grafo()


@app.post("/api/query")
async def consultar(request: QueryRequest):
    """Ejecuta una consulta vía orquestador multi-agente con guardrails."""
    try:
        grag = get_grag()
        ctx = await get_orchestrator().aexecute(
            grag,
            request.query,
            _generar_argumentacion,
        )
    except Exception as e:
        if "api_key" in str(e).lower() or "OPENAI" in str(e).upper():
            raise HTTPException(
                status_code=503,
                detail="Configura OPENAI_API_KEY antes de consultar.",
            )
        raise HTTPException(status_code=500, detail=str(e))

    if ctx.blocked:
        raise HTTPException(status_code=400, detail=ctx.block_reason or "Consulta no permitida.")

    return {
        "response": ctx.response_text,
        "structured": ctx.structured,
        "argumentacion": ctx.argumentacion,
        "intent": ctx.intent,
        "warnings": ctx.input_warnings + ctx.output_warnings,
        "impacted": {
            "nodes": ctx.nodes_impacted,
            "edges": ctx.edges_impacted,
        },
    }


def _generar_argumentacion(nodes: list, edges: list, structured: dict | None = None) -> str:
    """Resume elementos del grafo impactado (sin repetir el análisis jurídico del LLM)."""
    _ = structured  # el análisis va en Explicación; aquí solo el grafo
    if not nodes:
        return "No se encontraron elementos en el grafo para esta consulta."

    lineas = [
        "Elementos del grafo impactado relevantes para orientar la labor en derechos humanos:\n"
    ]

    orden_tipos = [
        ("Tratado", "Tratados"),
        ("Derecho", "Derechos"),
        ("Mecanismo", "Mecanismos"),
        ("Resolución", "Resoluciones"),
        ("Organismo", "Organismos"),
        ("Población", "Poblaciones"),
        ("Concepto_Jurídico", "Conceptos jurídicos"),
        ("Órgano", "Órganos"),
        ("País", "Países"),
        ("Otro", "Otros"),
    ]

    def normalizar(s: str) -> str:
        return s.lower().replace("_", " ").replace("í", "i").replace("ó", "o").strip()

    for tipo_key, etiqueta in orden_tipos:
        tn = normalizar(tipo_key)
        nodos_tipo = [n for n in nodes if normalizar(str(n.get("group", ""))) == tn]
        if nodos_tipo:
            lineas.append(f"\n{etiqueta}:")
            for n in nodos_tipo:
                nombre = n.get("id", n.get("label", ""))
                desc = (n.get("description") or "").strip()
                if desc and len(desc) < 200:
                    lineas.append(f"  • {nombre} — {desc}")
                else:
                    lineas.append(f"  • {nombre}")

    return "\n".join(lineas).strip()


# Servir frontend estático
LANDING_DIR = VISUALIZER_DIR / "dist"
LANDING_ASSETS = LANDING_DIR / "l-assets"
LANDING_INDEX = LANDING_DIR / "index.html"

app.mount("/assets", StaticFiles(directory=VISUALIZER_DIR / "assets"), name="assets")
_images_dir = VISUALIZER_DIR / "images"
if _images_dir.is_dir():
    app.mount("/images", StaticFiles(directory=_images_dir), name="images")
if LANDING_ASSETS.is_dir():
    app.mount("/l-assets", StaticFiles(directory=LANDING_ASSETS), name="l-assets")
_logos_dir = LANDING_DIR / "logos"
if _logos_dir.is_dir():
    app.mount("/logos", StaticFiles(directory=_logos_dir), name="logos")
_avatars_dir = LANDING_DIR / "avatars"
_avatars_public = VISUALIZER_DIR / "landing" / "public" / "avatars"
if _avatars_dir.is_dir():
    app.mount("/avatars", StaticFiles(directory=_avatars_dir), name="avatars")
elif _avatars_public.is_dir():
    app.mount("/avatars", StaticFiles(directory=_avatars_public), name="avatars")


@app.get("/")
def index():
    if not LANDING_INDEX.exists():
        raise HTTPException(
            status_code=503,
            detail="Landing no compilado. Ejecuta: cd visualizer/landing && npm run build",
        )
    return FileResponse(LANDING_INDEX)


@app.get("/consulta")
def consulta():
    return FileResponse(VISUALIZER_DIR / "consulta.html")


_MERMAID_SANDBOX_CSP = (
    "default-src 'none'; "
    "script-src https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js 'nonce-gisco-mermaid-sandbox' 'unsafe-eval'; "
    "style-src 'unsafe-inline'; "
    "img-src data:; "
    "font-src data:; "
    "connect-src 'none'; "
    "worker-src 'none'; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'self'"
)


@app.get("/mermaid-sandbox.html")
def mermaid_sandbox():
    """Entorno aislado para pintar Mermaid: sin red propia, sin almacenamiento ni padre DOM."""
    path = VISUALIZER_DIR / "mermaid-sandbox.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Sandbox de diagramas no disponible.")
    return FileResponse(
        path,
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Security-Policy": _MERMAID_SANDBOX_CSP,
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "X-Frame-Options": "SAMEORIGIN",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
            "Cross-Origin-Resource-Policy": "same-origin",
        },
    )


@app.get("/config.js")
def visualizer_config():
    return FileResponse(VISUALIZER_DIR / "config.js", media_type="application/javascript")


@app.get("/grafo.json")
def grafo_json():
    """Para el visualizador estático que carga grafo.json."""
    p = VISUALIZER_DIR / "grafo.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="grafo.json no existe. Ejecuta export_grafo.py primero.")
    return FileResponse(p)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
