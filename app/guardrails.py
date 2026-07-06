"""Guardrails de entrada y salida para consultas GraphRAG en derechos humanos."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

MAX_QUERY_LENGTH = int(__import__("os").getenv("MAX_QUERY_LENGTH", "2000"))

LEGAL_DISCLAIMER = (
    "\n\n—\n*Esta respuesta es informativa con base en los documentos indexados "
    "y no constituye asesoría jurídica. Verifique siempre con fuentes oficiales "
    "y profesionales calificados.*"
)

_DH_KEYWORDS = re.compile(
    r"\b("
    r"derechos?\s+humanos?|dd\.?\s*hh\.?|tratad[oa]s?|convenci[oó]n|resoluci[oó]n|"
    r"poblaci[oó]n(?:es)?|ind[ií]gena[s]?|migrante[s]?|refugiad[oa]s?|niñ[oa]s?|"
    r"tortura|trata\s+de\s+personas|desaparici[oó]n|discriminaci[oó]n|educaci[oó]n|"
    r"libertad\s+de\s+expresi[oó]n|petici[oó]n|onu|oac|cidh|oit|mecanismo[s]?|"
    r"organismo[s]?|instrumento[s]?|marco\s+normativo|protecci[oó]n|garant[ií]a"
    r")\b",
    re.IGNORECASE,
)

_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"olvida\s+(todas?\s+)?(las\s+)?instrucciones",
        r"you\s+are\s+now\s+",
        r"act\s+as\s+(if\s+you\s+)?(were|are)\s+",
        r"jailbreak",
        r"system\s+prompt",
        r"<\s*/?\s*system\s*>",
        r"```\s*system",
    )
]

_UNSAFE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(c[oó]mo\s+)?(torturar|matar|secuestrar|desaparecer\s+a)\b",
        r"\b(elaborar\s+)?(arma[s]?|explosivo[s]?|veneno)\b",
    )
]


@dataclass
class InputGuardrailResult:
    allowed: bool
    sanitized_query: str = ""
    block_reason: str | None = None
    warnings: list[str] = field(default_factory=list)
    intent: str = "dh_query"  # dh_query | off_topic | unsafe | clarification


@dataclass
class OutputGuardrailResult:
    response_text: str
    structured: dict[str, Any] | None
    warnings: list[str] = field(default_factory=list)
    disclaimer_appended: bool = False


def validate_input(query: str) -> InputGuardrailResult:
    """Valida y clasifica la consulta antes de invocar GraphRAG."""
    sanitized = " ".join(query.split()).strip()
    if not sanitized:
        return InputGuardrailResult(allowed=False, block_reason="La consulta no puede estar vacía.")

    if len(sanitized) > MAX_QUERY_LENGTH:
        return InputGuardrailResult(
            allowed=False,
            block_reason=f"La consulta supera el límite de {MAX_QUERY_LENGTH} caracteres.",
        )

    for pattern in _UNSAFE_PATTERNS:
        if pattern.search(sanitized):
            return InputGuardrailResult(
                allowed=False,
                sanitized_query=sanitized,
                block_reason=(
                    "No puedo procesar consultas que soliciten información para causar daño. "
                    "Si busca información sobre prohibiciones o marcos de protección en derechos humanos, "
                    "reformule su pregunta en ese sentido."
                ),
                intent="unsafe",
            )

    warnings: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(sanitized):
            warnings.append("Se detectó un posible intento de manipulación del sistema; la consulta fue acotada.")
            break

    intent = "dh_query"
    if not _DH_KEYWORDS.search(sanitized) and len(sanitized) < 12:
        intent = "clarification"
        warnings.append(
            "La consulta es muy breve o ambigua. Se intentará responder con el contexto disponible."
        )
    elif not _DH_KEYWORDS.search(sanitized) and len(sanitized) > 40:
        intent = "off_topic"
        warnings.append(
            "La consulta podría estar fuera del dominio de derechos humanos indexado."
        )

    return InputGuardrailResult(
        allowed=True,
        sanitized_query=sanitized,
        warnings=warnings,
        intent=intent,
    )


def validate_output(
    response_text: str,
    structured: dict[str, Any] | None,
    *,
    has_context: bool,
    intent: str = "dh_query",
    append_disclaimer: bool = True,
) -> OutputGuardrailResult:
    """Ajusta la respuesta según evidencia recuperada y reglas de dominio."""
    warnings: list[str] = []
    text = (response_text or "").strip()
    data = dict(structured) if structured else None

    if data:
        confianza = str(data.get("confianza", "")).lower()
        if confianza == "alta" and not has_context:
            data["confianza"] = "baja"
            data["limitaciones"] = _merge_limitacion(
                data.get("limitaciones"),
                "No se recuperó contexto suficiente del grafo para sustentar alta confianza.",
            )
            warnings.append("Confianza degradada: contexto insuficiente en el grafo.")

        if intent == "off_topic" and confianza in ("alta", "media"):
            data["confianza"] = "baja"
            data["limitaciones"] = _merge_limitacion(
                data.get("limitaciones"),
                "La consulta parece estar fuera del dominio principal de los documentos indexados.",
            )

        if not text:
            from app.formatters import format_legal_response
            text = format_legal_response(data).strip()

    if not has_context and not text:
        text = (
            "No se encontró información relevante en los documentos indexados para esta consulta. "
            "Intente reformular usando términos como tratados, derechos, poblaciones o mecanismos."
        )
        if data:
            data["confianza"] = "baja"
            data["limitaciones"] = _merge_limitacion(
                data.get("limitaciones"),
                "Sin contexto recuperado del grafo.",
            )

    disclaimer_appended = False
    if append_disclaimer and text and LEGAL_DISCLAIMER.strip() not in text:
        text = text + LEGAL_DISCLAIMER
        disclaimer_appended = True

    return OutputGuardrailResult(
        response_text=text,
        structured=data,
        warnings=warnings,
        disclaimer_appended=disclaimer_appended,
    )


def _merge_limitacion(actual: Any, extra: str) -> str:
    base = str(actual).strip() if actual else ""
    return f"{base} {extra}".strip() if base else extra
