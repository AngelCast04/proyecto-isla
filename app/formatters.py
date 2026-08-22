"""Formateadores de respuesta jurídica para API y UI."""

from __future__ import annotations

import re
from typing import Any

RELACION_MISMO_CONCEPTO = "Mismo concepto (variantes del nombre)"
RELACION_MISMO_CONCEPTO_CORTA = "Mismo concepto"

MERMAID_START = "<<MERMAID_START>>"
MERMAID_END = "<<MERMAID_END>>"
MERMAID_MAX_CHARS = 12_000
MERMAID_MAX_LINES = 80
_MERMAID_ALLOWED_START = re.compile(
    r"^(flowchart|graph|sequencediagram|classdiagram|mindmap)\b",
    re.I,
)
_MERMAID_FORBIDDEN = re.compile(
    r"(<script|</script|javascript:|vbscript:|data:text/html|on\w+\s*=|"
    r"foreignObject|<iframe|eval\s*\(|new\s+Function)",
    re.I,
)
_MERMAID_BAD_LINE = re.compile(r"^\s*(click|call|href)\b", re.I)
_MERMAID_INIT = re.compile(r"%%\{[\s\S]*?\}%%", re.I)
_MERMAID_BLOCK_RE = re.compile(
    r"<<MERMAID_START(?::(?P<kind>[A-Za-z0-9_-]+))?>>\s*"
    r"(?:```(?:mermaid)?\s*)?"
    r"(?P<code>.*?)"
    r"(?:\s*```)?"
    r"\s*<<MERMAID_END>>",
    re.DOTALL | re.IGNORECASE,
)
_MERMAID_FENCE_RE = re.compile(
    r"```mermaid\s*(?P<code>.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def humanizar_relacion(desc: str, *, corta: bool = False) -> str:
    """Convierte etiquetas técnicas del grafo en texto legible para usuarios no expertos."""
    s = str(desc or "").strip()
    if s.lower() == "is":
        return RELACION_MISMO_CONCEPTO_CORTA if corta else RELACION_MISMO_CONCEPTO
    return s


def format_legal_response(structured: dict[str, Any] | None) -> str:
    """Convierte la respuesta estructurada en texto plano legible."""
    if not structured:
        return ""

    lineas: list[str] = []

    intro = str(structured.get("introduccion") or "").strip()
    if intro:
        lineas.append(intro)
        lineas.append("")
        lineas.append("---")
        lineas.append("")

    lineas.append("Análisis jurídico detallado")
    lineas.append("")

    violaciones = structured.get("violaciones") or []
    if violaciones:
        lineas.append("I. Presuntas violaciones de derechos humanos")
        lineas.append("")
        for v in violaciones:
            titulo = str(v.get("titulo") or "").strip()
            analisis = str(v.get("analisis") or "").strip()
            fuentes = v.get("fuentes") or []
            refs = f" [{', '.join(str(f) for f in fuentes)}]" if fuentes else ""
            if titulo and not titulo.endswith("."):
                titulo += "."
            lineas.append(f"{titulo} {analisis}{refs}".strip())
            lineas.append("")

    tratados = structured.get("tratados") or []
    if tratados:
        lineas.append("II. Tratados internacionales aplicables")
        lineas.append("")
        lineas.append("| Instrumento | Artículos clave |")
        lineas.append("|-------------|-----------------|")
        for t in tratados:
            inst = str(t.get("instrumento") or "").replace("|", "/")
            arts = str(t.get("articulos_clave") or "").replace("|", "/")
            obs = str(t.get("observaciones") or "").strip()
            if obs:
                inst = f"{inst} ({obs})"
            lineas.append(f"| {inst} | {arts} |")
        lineas.append("")

    observaciones = structured.get("observaciones_resoluciones") or []
    if observaciones:
        lineas.append("III. Observaciones generales, resoluciones, reportes e informes")
        lineas.append("")
        for item in observaciones:
            tipo = str(item.get("tipo") or "Fuente").strip()
            titulo = str(item.get("titulo") or "").strip()
            organismo = str(item.get("organismo") or "").strip()
            relevancia = str(item.get("relevancia") or "").strip()
            fuentes = item.get("fuentes") or []
            refs = f" [{', '.join(str(f) for f in fuentes)}]" if fuentes else ""
            cabeza = f"{tipo}: {titulo}" if titulo else tipo
            if organismo:
                cabeza += f" ({organismo})"
            lineas.append(f"{cabeza}. {relevancia}{refs}".strip())
            lineas.append("")

    conclusion = str(structured.get("conclusion") or "").strip()
    if conclusion:
        lineas.append(conclusion)

    return "\n".join(lineas).strip()


def _mermaid_slug(text: str, used: set[str], prefix: str = "n") -> str:
    slug = re.sub(r"[^A-Za-z0-9]", "_", str(text or ""))
    slug = re.sub(r"_+", "_", slug).strip("_")[:40]
    if not slug or slug[0].isdigit():
        slug = f"{prefix}_{slug or 'x'}"
    base = slug
    i = 1
    while slug in used:
        i += 1
        slug = f"{base}_{i}"
    used.add(slug)
    return slug


def _mermaid_label(text: str, max_len: int = 48) -> str:
    s = " ".join(str(text or "").split())
    if len(s) > max_len:
        s = s[: max_len - 1].rstrip() + "…"
    for src, dst in (
        ("\\", "/"),
        ('"', "'"),
        ("[", "("),
        ("]", ")"),
        ("{", "("),
        ("}", ")"),
        ("#", ""),
        ("<", ""),
        (">", ""),
        ("|", "/"),
        ("`", "'"),
    ):
        s = s.replace(src, dst)
    return s or "—"


def sanitize_mermaid_code(code: str) -> str:
    """Reduce el código Mermaid a un diagrama estático acotado, sin JS ni init."""
    s = str(code or "").replace("\x00", "").strip()
    s = re.sub(r"^```(?:mermaid)?\s*", "", s, flags=re.I)
    s = re.sub(r"\s*```$", "", s)
    s = _MERMAID_INIT.sub("", s)
    if not s or _MERMAID_FORBIDDEN.search(s):
        return ""
    lines: list[str] = []
    for line in s.splitlines():
        if _MERMAID_BAD_LINE.match(line) or "javascript:" in line.lower():
            continue
        lines.append(line.rstrip())
        if len(lines) > MERMAID_MAX_LINES:
            return ""
    s = "\n".join(lines).strip()
    if not s or len(s) > MERMAID_MAX_CHARS:
        return ""
    first = next((ln.strip() for ln in s.splitlines() if ln.strip()), "")
    if not _MERMAID_ALLOWED_START.match(first):
        return ""
    return s


def wrap_mermaid(code: str, kind: str = "") -> str:
    """Envuelve código Mermaid en delimitadores detectables por la aplicación."""
    body = sanitize_mermaid_code(code)
    if not body:
        return ""
    body = f"```mermaid\n{body}\n```"
    start = f"<<MERMAID_START:{kind}>>" if kind else MERMAID_START
    return f"{start}\n{body}\n{MERMAID_END}"


def extract_mermaid_from_text(text: str) -> tuple[str, list[dict[str, str]]]:
    """Separa el texto visible de los bloques Mermaid embebidos.

    Detecta `<<MERMAID_START>>…<<MERMAID_END>>` y, como respaldo, vallas
    markdown ```mermaid. Devuelve (texto_sin_diagramas, bloques).
    """
    src = str(text or "")
    bloques: list[dict[str, str]] = []
    if not src.strip():
        return "", bloques

    def _tomar(match: re.Match[str]) -> str:
        code = sanitize_mermaid_code(match.group("code") or "")
        if code:
            kind = ""
            if "kind" in match.groupdict() and match.group("kind"):
                kind = str(match.group("kind")).strip().lower()
            bloques.append({"kind": kind, "code": code})
        return "\n"

    limpio = _MERMAID_BLOCK_RE.sub(_tomar, src)
    limpio = _MERMAID_FENCE_RE.sub(_tomar, limpio)
    limpio = re.sub(r"\n{3,}", "\n\n", limpio).strip()
    return limpio, bloques


def build_mermaid_analisis(structured: dict[str, Any] | None) -> str:
    """Diagrama del análisis jurídico: caso → violaciones → tratados → conclusión."""
    if not structured:
        return ""

    lines = ["flowchart TB"]
    intro = _mermaid_label(structured.get("introduccion") or "Consulta", 72)
    lines.append(f'  intro["{intro}"]')
    lines.append("  class intro intro")

    violaciones = list(structured.get("violaciones") or [])[:6]
    v_ids: list[str] = []
    for i, item in enumerate(violaciones, 1):
        if not isinstance(item, dict):
            continue
        vid = f"v{i}"
        titulo = _mermaid_label(item.get("titulo") or f"Violación {i}", 52)
        lines.append(f'  {vid}["{titulo}"]')
        lines.append(f"  intro --> {vid}")
        lines.append(f"  class {vid} viol")
        v_ids.append(vid)

    tratados = list(structured.get("tratados") or [])[:8]
    t_ids: list[str] = []
    for i, item in enumerate(tratados, 1):
        if not isinstance(item, dict):
            continue
        tid = f"t{i}"
        inst = _mermaid_label(item.get("instrumento") or f"Instrumento {i}", 52)
        lines.append(f'  {tid}["{inst}"]')
        src = v_ids[(i - 1) % len(v_ids)] if v_ids else "intro"
        lines.append(f"  {src} --> {tid}")
        lines.append(f"  class {tid} trat")
        t_ids.append(tid)

    conclusion = str(structured.get("conclusion") or "").strip()
    if conclusion:
        lines.append(f'  conc["{_mermaid_label(conclusion, 72)}"]')
        lines.append("  class conc conc")
        for oid in (t_ids or v_ids or ["intro"])[:4]:
            lines.append(f"  {oid} --> conc")

    if len(v_ids) + len(t_ids) == 0 and not conclusion:
        return ""

    lines.extend([
        "  classDef intro fill:#312e81,stroke:#818cf8,color:#e4e4e7",
        "  classDef viol fill:#7f1d1d,stroke:#f87171,color:#fecaca",
        "  classDef trat fill:#4c1d95,stroke:#a78bfa,color:#ddd6fe",
        "  classDef conc fill:#14532d,stroke:#86efac,color:#bbf7d0",
    ])
    return "\n".join(lines)


def build_mermaid_grafo(
    nodes: list[dict[str, Any]] | None,
    edges: list[dict[str, Any]] | None,
    *,
    max_nodes: int = 16,
    max_edges: int = 22,
) -> str:
    """Diagrama del subgrafo impactado agrupado por tipo de entidad."""
    if not nodes:
        return ""

    ranked = sorted(
        [n for n in nodes if isinstance(n, dict)],
        key=lambda n: float(n.get("score") or 0),
        reverse=True,
    )[:max_nodes]
    keep: set[str] = set()
    by_type: dict[str, list[dict[str, Any]]] = {}
    for node in ranked:
        name = str(node.get("id") or node.get("label") or "").strip()
        if not name:
            continue
        keep.add(name)
        tipo = str(node.get("group") or "Otro").strip() or "Otro"
        by_type.setdefault(tipo, []).append(node)

    if not keep:
        return ""

    used_ids: set[str] = set()
    node_ids: dict[str, str] = {}
    lines = ["flowchart LR"]

    def nid(name: str) -> str:
        if name not in node_ids:
            node_ids[name] = _mermaid_slug(name, used_ids)
        return node_ids[name]

    for tipo, group_nodes in by_type.items():
        sg = _mermaid_slug(f"tipo {tipo}", used_ids, prefix="sg")
        lines.append(f'  subgraph {sg}["{_mermaid_label(tipo.replace("_", " "), 28)}"]')
        for node in group_nodes:
            name = str(node.get("id") or node.get("label") or "").strip()
            if not name:
                continue
            lines.append(f'    {nid(name)}["{_mermaid_label(name)}"]')
        lines.append("  end")

    count_e = 0
    for edge in edges or []:
        if not isinstance(edge, dict):
            continue
        src = str(edge.get("from") or "").strip()
        tgt = str(edge.get("to") or "").strip()
        if src not in keep or tgt not in keep or src == tgt:
            continue
        lab = _mermaid_label(
            humanizar_relacion(str(edge.get("label") or edge.get("title") or ""), corta=True),
            32,
        )
        a, b = nid(src), nid(tgt)
        if lab and lab != "—":
            lines.append(f'  {a} -->|"{lab}"| {b}')
        else:
            lines.append(f"  {a} --> {b}")
        count_e += 1
        if count_e >= max_edges:
            break

    return "\n".join(lines)


def append_mermaid_to_text(text: str, code: str, kind: str = "") -> str:
    """Añade un bloque Mermaid delimitado al final de la respuesta textual."""
    wrapped = wrap_mermaid(code, kind)
    if not wrapped:
        return (text or "").strip()
    base = (text or "").rstrip()
    if not base:
        return wrapped
    return f"{base}\n\n{wrapped}"


def clasificar_tipo_observacion(texto: str, group: str = "") -> str | None:
    """Detecta si un nodo o título es observación general, resolución, reporte o informe."""
    blob = f"{group} {texto}".lower()
    blob = blob.replace("_", " ").replace("í", "i").replace("ó", "o")
    if "observacion general" in blob or "observaciones generales" in blob:
        return "Observación general"
    if "resolucion" in blob:
        return "Resolución"
    if "reporte" in blob:
        return "Reporte"
    if "informe" in blob:
        return "Informe"
    return None


def observaciones_desde_nodos(nodes: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Recupera resoluciones e informes del grafo impactado cuando el LLM no los listó."""
    items: list[dict[str, Any]] = []
    vistos: set[str] = set()
    for n in nodes or []:
        titulo = str(n.get("id") or n.get("label") or "").strip()
        if not titulo:
            continue
        tipo = clasificar_tipo_observacion(titulo, str(n.get("group") or ""))
        if not tipo:
            continue
        clave = titulo.casefold()
        if clave in vistos:
            continue
        vistos.add(clave)
        desc = str(n.get("description") or "").strip()
        items.append({
            "tipo": tipo,
            "titulo": titulo,
            "organismo": None,
            "relevancia": desc or "Identificado en el grafo de la consulta.",
            "fuentes": [],
        })
    return items


def completar_observaciones_resoluciones(
    structured: dict[str, Any] | None,
    nodes: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Usa lo que generó el análisis y, si falta, completa con nodos del grafo."""
    items = list((structured or {}).get("observaciones_resoluciones") or [])
    limpios: list[dict[str, Any]] = []
    vistos: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        titulo = str(item.get("titulo") or "").strip()
        if not titulo:
            continue
        clave = titulo.casefold()
        if clave in vistos:
            continue
        vistos.add(clave)
        tipo = str(item.get("tipo") or clasificar_tipo_observacion(titulo) or "Informe").strip()
        limpios.append({
            "tipo": tipo,
            "titulo": titulo,
            "organismo": item.get("organismo") or None,
            "relevancia": str(item.get("relevancia") or "").strip(),
            "fuentes": item.get("fuentes") or [],
        })
    if limpios:
        return limpios
    return observaciones_desde_nodos(nodes)
