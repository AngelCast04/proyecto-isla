"""Formateadores de respuesta jurídica para API y UI."""

from __future__ import annotations

from typing import Any

RELACION_MISMO_CONCEPTO = "Mismo concepto (variantes del nombre)"
RELACION_MISMO_CONCEPTO_CORTA = "Mismo concepto"


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
