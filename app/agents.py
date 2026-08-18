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

from app.formatters import completar_observaciones_resoluciones, humanizar_relacion
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

    async def run(self, grag: Any, ctx: AgentContext) -> AgentContext:
        from fast_graphrag import QueryParam

        respuesta = await grag.aquery(
            ctx.query,
            params=QueryParam(with_references=True, structured=True),
        )
        ctx.has_context = _has_retrieved_context(respuesta)

        raw = respuesta.response
        if hasattr(raw, "model_dump"):
            ctx.structured = raw.model_dump()
        elif hasattr(raw, "answer"):
            ctx.response_text = str(getattr(raw, "answer", raw) or "")
        else:
            ctx.response_text = str(raw) if raw is not None else ""

        ctx.nodes_impacted, ctx.edges_impacted = _extract_impacted(respuesta, self.working_dir)
        if ctx.structured is not None:
            ctx.structured["observaciones_resoluciones"] = completar_observaciones_resoluciones(
                ctx.structured,
                ctx.nodes_impacted,
            )
            from app.formatters import format_legal_response
            ctx.response_text = format_legal_response(ctx.structured)
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

    async def aexecute(
        self,
        grag: Any,
        query: str,
        generar_argumentacion_fn: Any,
    ) -> AgentContext:
        _, ctx = self.router.run(query)
        if ctx.blocked:
            return ctx

        ctx = await self.analyst.run(grag, ctx)
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


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _norm_tipo(value: Any) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("_", " ")
        .replace("í", "i")
        .replace("ó", "o")
    )


def _es_instrumento(tipo: Any) -> bool:
    t = _norm_tipo(tipo)
    return t in {"tratado", "resolucion", "convenio", "pacto"} or "tratado" in t


def _recortar(texto: str, limite: int = 700) -> str:
    s = " ".join(str(texto or "").split())
    if len(s) <= limite:
        return s
    return s[: limite - 1].rstrip() + "…"


def _relevancia(score: float, max_score: float) -> str:
    if max_score <= 0:
        return "baja"
    ratio = score / max_score
    if ratio >= 0.65:
        return "alta"
    if ratio >= 0.32:
        return "media"
    return "baja"


def _chunks_desde_contexto(context: Any) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for chunk, score in getattr(context, "chunks", None) or []:
        meta = getattr(chunk, "metadata", None) or {}
        if not isinstance(meta, dict):
            meta = {}
        cid = getattr(chunk, "id", None)
        try:
            cid_key = int(cid) if cid is not None else None
        except (TypeError, ValueError):
            cid_key = cid
        ranked.append({
            "id": cid_key,
            "text": _recortar(getattr(chunk, "content", None) or str(chunk), 800),
            "score": round(_as_float(score), 4),
            "instrumento": str(meta.get("instrumento") or meta.get("source") or "").strip(),
            "archivo": str(meta.get("archivo") or meta.get("ruta") or "").strip(),
        })
    ranked.sort(key=lambda c: c["score"], reverse=True)
    return ranked


def _chunks_para_nodo(
    nombre: str,
    ranked_chunks: list[dict[str, Any]],
    chunk_ids_relacion: set[Any],
) -> list[dict[str, Any]]:
    por_id: list[dict[str, Any]] = []
    if chunk_ids_relacion:
        for chunk in ranked_chunks:
            if chunk.get("id") in chunk_ids_relacion:
                por_id.append(chunk)
    if por_id:
        return por_id[:2]

    nombre_l = nombre.lower()
    if len(nombre_l) < 4:
        return []
    por_texto = [c for c in ranked_chunks if nombre_l in (c.get("text") or "").lower()]
    return por_texto[:2]


def _extract_impacted(respuesta: Any, working_dir: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Subgrafo de la consulta: nodos con score, chunks e instrumentos vecinos.

    No modifica el grafo persistido. Filtra extremos de arista con score bajo
    para no pintar vecinos poco relacionados con la pregunta.
    """
    import os

    import igraph as ig

    context = getattr(respuesta, "context", None)
    if context is None:
        return [], []

    min_ratio = float(os.getenv("GRAPH_MIN_SCORE_RATIO", "0.32"))
    keep_top = int(os.getenv("GRAPH_KEEP_TOP", "12"))
    max_nodes = int(os.getenv("GRAPH_MAX_QUERY_NODES", "36"))

    entity_scores: dict[str, float] = {}
    for entity, score in getattr(context, "entities", None) or []:
        name = str(getattr(entity, "name", "") or "")
        if not name:
            continue
        entity_scores[name] = max(entity_scores.get(name, 0.0), _as_float(score))

    relations_raw = list(getattr(context, "relations", None) or [])
    ranked_chunks = _chunks_desde_contexto(context)
    chunk_ids_por_nodo: dict[str, set[Any]] = {}
    for relation, _score in relations_raw:
        src = str(getattr(relation, "source", "") or "")
        tgt = str(getattr(relation, "target", "") or "")
        ids: set[Any] = set()
        for hid in getattr(relation, "chunks", None) or []:
            try:
                ids.add(int(hid))
            except (TypeError, ValueError):
                ids.add(hid)
        if src:
            chunk_ids_por_nodo.setdefault(src, set()).update(ids)
        if tgt:
            chunk_ids_por_nodo.setdefault(tgt, set()).update(ids)

    graph_attrs: dict[str, dict[str, str]] = {}
    graph_path = Path(working_dir) / "graph_igraph_data.pklz"
    if graph_path.exists():
        g = ig.Graph.Read_Picklez(str(graph_path))
        for v in g.vs:
            name = str(v["name"])
            attrs = v.attributes()
            graph_attrs[name] = {
                "group": str(attrs.get("type") or "Otro"),
                "description": str(attrs.get("description") or ""),
            }

    def tipo_de(nombre: str) -> str:
        if nombre in graph_attrs:
            return graph_attrs[nombre]["group"]
        return "Otro"

    max_score = max(entity_scores.values()) if entity_scores else 0.0
    ranked_names = sorted(entity_scores, key=lambda n: entity_scores[n], reverse=True)
    if max_score > 0:
        keep = {n for n, s in entity_scores.items() if s / max_score >= min_ratio}
    else:
        keep = set(ranked_names[:keep_top])
    if not keep and ranked_names:
        keep = set(ranked_names[: min(keep_top, len(ranked_names))])

    # Instrumentos vecinos de nodos ya retenidos: aportan el marco legal sin abrir el grafo entero.
    for relation, _score in relations_raw:
        src = str(getattr(relation, "source", "") or "")
        tgt = str(getattr(relation, "target", "") or "")
        for a, b in ((src, tgt), (tgt, src)):
            if a in keep and b and _es_instrumento(tipo_de(b)):
                keep.add(b)

    if len(keep) > max_nodes:
        prioridad = sorted(
            keep,
            key=lambda n: (
                1 if _es_instrumento(tipo_de(n)) else 0,
                entity_scores.get(n, 0.0),
            ),
            reverse=True,
        )
        keep = set(prioridad[:max_nodes])

    if not keep and ranked_names:
        keep = set(ranked_names[: min(keep_top, len(ranked_names))])

    edges_impacted: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str]] = set()
    for relation, rel_score in relations_raw:
        src = str(getattr(relation, "source", "") or "")
        tgt = str(getattr(relation, "target", "") or "")
        if not src or not tgt or src not in keep or tgt not in keep:
            continue
        key = (src, tgt)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        desc = humanizar_relacion(str(getattr(relation, "description", "") or ""))
        edges_impacted.append({
            "from": src,
            "to": tgt,
            "label": desc[:100],
            "title": desc,
            "score": round(_as_float(rel_score), 4),
        })

    instrumentos_por_nodo: dict[str, list[dict[str, str]]] = {n: [] for n in keep}
    for edge in edges_impacted:
        for a, b in ((edge["from"], edge["to"]), (edge["to"], edge["from"])):
            if not _es_instrumento(tipo_de(b)):
                continue
            item = {
                "id": b,
                "group": tipo_de(b),
                "relacion": str(edge.get("title") or ""),
            }
            if not any(x["id"] == b for x in instrumentos_por_nodo[a]):
                instrumentos_por_nodo[a].append(item)

    nodes_impacted: list[dict[str, Any]] = []
    for name in keep:
        attrs = graph_attrs.get(name, {})
        tipo = attrs.get("group") or "Otro"
        desc = attrs.get("description") or ""
        score = entity_scores.get(name, 0.0)
        rel = _relevancia(score, max_score)
        chunks = _chunks_para_nodo(name, ranked_chunks, chunk_ids_por_nodo.get(name, set()))
        fuentes: list[dict[str, str]] = []
        vistos: set[tuple[str, str]] = set()
        for ch in chunks:
            inst = str(ch.get("instrumento") or "").strip()
            arch = str(ch.get("archivo") or "").strip()
            key = (inst, arch)
            if not inst and not arch:
                continue
            if key in vistos:
                continue
            vistos.add(key)
            fuentes.append({"instrumento": inst, "archivo": arch})
        pct = int(round(100 * score / max_score)) if max_score > 0 else 0
        title_bits = [str(tipo), f"relevancia {pct}%"]
        if fuentes:
            title_bits.append("Fuente: " + (fuentes[0]["instrumento"] or fuentes[0]["archivo"]))
        if desc:
            title_bits.append(desc)
        nodes_impacted.append({
            "id": name,
            "label": name[:50] + ("..." if len(name) > 50 else ""),
            "title": "\n".join(title_bits)[:500],
            "group": tipo,
            "description": desc,
            "score": round(score, 4),
            "relevance": rel,
            "chunks": chunks,
            "instrumentos": instrumentos_por_nodo.get(name, []),
            "fuentes": fuentes,
        })

    nodes_impacted.sort(key=lambda n: n.get("score", 0.0), reverse=True)

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
                    "score": 0.0,
                    "relevance": "baja",
                    "chunks": [],
                    "instrumentos": [],
                    "fuentes": [],
                })

    return nodes_impacted, edges_impacted
