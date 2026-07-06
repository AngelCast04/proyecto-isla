"""Orquestación de agentes especializados para el pipeline de consulta GraphRAG.

Arquitectura recomendada para este proyecto (derechos humanos + grafo semántico):

  ┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
  │   Router    │────▶│  Entity Spotter  │────▶│  Retriever  │
  │ (guardrails)│     │ (extracción NER) │     │ (grafo+VDB) │
  └─────────────┘     └──────────────────┘     └──────┬──────┘
                                                       │
  ┌─────────────┐     ┌──────────────────┐            ▼
  │ Argumentador│◀────│    Verifier      │◀───┌─────────────┐
  │ (grafo UI)  │     │ (grounding)      │    │   Analyst   │
  └─────────────┘     └──────────────────┘    │ (respuesta) │
                                              └─────────────┘

Agentes de ingesta (offline, run_quickstart.py):
  - Indexer: chunking de PDFs
  - Extractor: entidades y relaciones vía LLM
  - Graph Builder: upsert en igraph + índices vectoriales
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.guardrails import InputGuardrailResult, validate_input, validate_output


@dataclass
class AgentContext:
  """Estado compartido entre agentes durante una consulta."""

  query: str
  intent: str = "dh_query"
  input_warnings: list[str] = field(default_factory=list)
  output_warnings: list[str] = field(default_factory=list)
  has_context: bool = False
  response_text: str = ""
  structured: dict[str, Any] | None = None
  nodes_impacted: list[dict[str, Any]] = field(default_factory=list)
  edges_impacted: list[dict[str, Any]] = field(default_factory=list)
  argumentacion: str = ""
  blocked: bool = False
  block_reason: str | None = None


class RouterAgent:
    """Clasifica y filtra la consulta antes del pipeline RAG."""

    def run(self, query: str) -> tuple[InputGuardrailResult, AgentContext | None]:
        result = validate_input(query)
        if not result.allowed:
            return result, AgentContext(
                query=query,
                blocked=True,
                block_reason=result.block_reason,
                intent=result.intent,
            )
        ctx = AgentContext(
            query=result.sanitized_query,
            intent=result.intent,
            input_warnings=list(result.warnings),
        )
        return result, ctx


class AnalystAgent:
    """Genera respuesta estructurada usando GraphRAG + LLM."""

    def __init__(self, working_dir: str) -> None:
        self.working_dir = working_dir

    def run(self, grag: Any, ctx: AgentContext) -> AgentContext:
        from fast_graphrag import QueryParam

        respuesta = grag.query(
            ctx.query,
            params=QueryParam(with_references=True, structured=True),
        )
        ctx.has_context = _has_retrieved_context(respuesta)

        raw = respuesta.response
        if hasattr(raw, "model_dump"):
            ctx.structured = raw.model_dump()
            from app.formatters import format_legal_response
            ctx.response_text = format_legal_response(ctx.structured)
        elif hasattr(raw, "answer"):
            ctx.response_text = str(getattr(raw, "answer", raw) or "")
        else:
            ctx.response_text = str(raw) if raw is not None else ""

        ctx.nodes_impacted, ctx.edges_impacted = _extract_impacted(respuesta, self.working_dir)
        return ctx


class VerifierAgent:
    """Aplica guardrails de salida y ajusta confianza según evidencia."""

    def run(self, ctx: AgentContext) -> AgentContext:
        out = validate_output(
            ctx.response_text,
            ctx.structured,
            has_context=ctx.has_context,
            intent=ctx.intent,
        )
        ctx.response_text = out.response_text
        ctx.structured = out.structured
        ctx.output_warnings.extend(out.warnings)
        return ctx


class ArgumentadorAgent:
    """Sintetiza argumentación a partir del grafo impactado y hallazgos del Analyst."""

    def run(self, ctx: AgentContext, generar_fn: Any) -> AgentContext:
        ctx.argumentacion = generar_fn(
            ctx.nodes_impacted,
            ctx.edges_impacted,
            ctx.structured,
        )
        return ctx


class QueryOrchestrator:
    """Coordina el flujo multi-agente de consulta."""

    def __init__(self, working_dir: str) -> None:
        self.router = RouterAgent()
        self.analyst = AnalystAgent(working_dir)
        self.verifier = VerifierAgent()
        self.argumentador = ArgumentadorAgent()

    def execute(
        self,
        grag: Any,
        query: str,
        generar_argumentacion_fn: Any,
    ) -> AgentContext:
        _, ctx = self.router.run(query)
        if ctx.blocked:
            return ctx

        ctx = self.analyst.run(grag, ctx)
        ctx = self.verifier.run(ctx)
        ctx = self.argumentador.run(ctx, generar_argumentacion_fn)
        return ctx


def _has_retrieved_context(respuesta: Any) -> bool:
    ctx = getattr(respuesta, "context", None)
    if ctx is None:
        return False
    entities = getattr(ctx, "entities", None) or []
    relations = getattr(ctx, "relations", None) or []
    chunks = getattr(ctx, "chunks", None) or []
    return bool(entities or relations or chunks)


def _extract_impacted(respuesta: Any, working_dir: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extrae nodos y aristas impactados del contexto de GraphRAG."""
    import igraph as ig

    node_ids = {e.name for e, _ in respuesta.context.entities}
    edges_impacted: list[dict[str, Any]] = [
        {
            "from": r.source,
            "to": r.target,
            "label": (r.description or "")[:100],
            "title": r.description or "",
        }
        for r, _ in respuesta.context.relations
    ]
    for e in edges_impacted:
        node_ids.add(e["from"])
        node_ids.add(e["to"])

    graph_path = Path(working_dir) / "graph_igraph_data.pklz"
    nodes_impacted: list[dict[str, Any]] = []
    if graph_path.exists():
        g = ig.Graph.Read_Picklez(str(graph_path))
        for v in g.vs:
            name = str(v["name"])
            if name in node_ids:
                attrs = v.attributes()
                tipo = attrs.get("type", "Otro")
                desc = attrs.get("description", "")
                nodes_impacted.append({
                    "id": name,
                    "label": name[:50] + ("..." if len(name) > 50 else ""),
                    "title": f"{tipo}\n{desc}"[:500],
                    "group": tipo,
                    "description": desc,
                })

    if not nodes_impacted and edges_impacted:
        seen: set[str] = set()
        for e in edges_impacted:
            for k in ("from", "to"):
                nid = e.get(k)
                if not nid or nid in seen:
                    continue
                seen.add(nid)
                nodes_impacted.append({
                    "id": nid,
                    "label": nid[:50] + ("..." if len(nid) > 50 else ""),
                    "title": "Otro",
                    "group": "Otro",
                    "description": "",
                })

    return nodes_impacted, edges_impacted
