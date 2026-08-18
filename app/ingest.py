"""Ingesta de PDFs: un documento por archivo, con metadata de origen."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

_NUMERO_INICIAL = re.compile(r"^\s*\d+\s*[-.]+\s*", re.UNICODE)
_SUFIJO_PARTE = re.compile(r"-\d+(-\d+)?\s*$")


def titulo_desde_nombre(nombre: str) -> str:
    """Convierte '14.- DH A LA LIBERTAD DE EXPRESIÓN.pdf' en un título legible."""
    stem = Path(nombre).stem
    stem = _NUMERO_INICIAL.sub("", stem)
    stem = _SUFIJO_PARTE.sub("", stem)
    stem = re.sub(r"\s+", " ", stem).replace(".-", " ").strip(" .-_")
    return stem or Path(nombre).stem


def extraer_texto_pdf(ruta_pdf: str | Path) -> tuple[str, str]:
    """Devuelve (texto, título de metadatos del PDF si existe)."""
    doc = fitz.open(str(ruta_pdf))
    try:
        meta = doc.metadata or {}
        titulo_pdf = str(meta.get("title") or "").strip()
        texto = "".join(pagina.get_text() for pagina in doc)
    finally:
        doc.close()
    return texto, titulo_pdf


def metadata_documento(archivo: Path, titulo_pdf: str = "") -> dict[str, str]:
    """Metadata persistida en cada chunk: instrumento + archivo de origen."""
    titulo = titulo_pdf if titulo_pdf and len(titulo_pdf) > 3 else titulo_desde_nombre(archivo.name)
    return {
        "archivo": archivo.name,
        "instrumento": titulo,
        "tema": titulo,
        "ruta": archivo.name,
    }


def listar_pdfs(carpeta: str | Path) -> list[Path]:
    path = Path(carpeta)
    if not path.is_dir():
        return []
    return sorted(
        p for p in path.glob("*.pdf") if p.is_file() and not p.name.startswith("._")
    )


def cargar_documentos(carpeta: str | Path) -> list[dict[str, Any]]:
    """Un ítem por PDF: texto + metadata. No concatena el corpus."""
    documentos: list[dict[str, Any]] = []
    for archivo in listar_pdfs(carpeta):
        texto, titulo_pdf = extraer_texto_pdf(archivo)
        if not texto.strip():
            continue
        documentos.append({
            "texto": texto,
            "metadata": metadata_documento(archivo, titulo_pdf),
            "archivo": archivo,
        })
    return documentos
