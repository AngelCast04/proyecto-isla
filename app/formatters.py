"""Formateadores de respuesta jurídica para API y UI."""

from __future__ import annotations

from typing import Any


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

    conclusion = str(structured.get("conclusion") or "").strip()
    if conclusion:
        lineas.append(conclusion)

    limitaciones = str(structured.get("limitaciones") or "").strip()
    if limitaciones:
        lineas.append("")
        lineas.append(f"Limitaciones: {limitaciones}")

    return "\n".join(lineas).strip()
