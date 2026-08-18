"""Quickstart de fast-graphrag: un PDF por documento, con metadata de origen."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent


def _resolve_dir(env_key: str, default_relative: str) -> str:
    raw = (os.getenv(env_key) or default_relative).strip() or default_relative
    p = Path(raw)
    if p.is_absolute():
        return str(p)
    return str((_ROOT / p).resolve())


try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

from fast_graphrag import GraphRAG
from fast_graphrag._llm import OpenAIEmbeddingService, OpenAILLMService

from app.ingest import cargar_documentos

DOMAIN = (
    "Analiza instrumentos internacionales y documentos de derechos humanos como un sistema integrado. "
    "Identifica estructuras jerárquicas: categorías generales (poblaciones, derechos) y sus desgloses "
    "a instrumentos, organismos, mecanismos y casos concretos. Facilita drill-down de lo general a lo específico."
)

EXAMPLE_QUERIES = [
    "¿Qué poblaciones vulnerables y derechos se cubren en los documentos?",
    "¿Qué instrumentos protegen a personas indígenas?",
    "¿Cuáles son los mecanismos de la ONU para migrantes y refugiados?",
    "¿Cómo se relacionan los tratados con resoluciones específicas por tema?",
    "¿Qué obligaciones de los Estados se mencionan para adultos mayores?",
]

ENTITY_TYPES = [
    "Población",
    "Derecho",
    "Tratado",
    "Resolución",
    "Organismo",
    "Mecanismo",
    "Concepto_Jurídico",
    "País",
    "Órgano",
]

_WORKDIR = _resolve_dir("GRAPH_WORKING_DIR", "grafo_libros")
_LIBROS = _resolve_dir("LIBROS_DIR", "libros")


def crear_grag(working_dir: str) -> GraphRAG:
    return GraphRAG(
        working_dir=working_dir,
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


def bucle_consultas(grag: GraphRAG) -> None:
    print("\n" + "=" * 60)
    print("Modo drill-down: explora de lo general a lo específico.")
    print("Ejemplos: pregunta general → luego consultas más concretas.")
    print("Escribe 'salir' para terminar.")
    print("=" * 60)

    while True:
        try:
            consulta = input("\nTu consulta: ").strip()
            if not consulta:
                continue
            if consulta.lower() in ("salir", "exit", "quit"):
                print("Hasta luego.")
                break

            print("\nAnalizando...")
            respuesta = grag.query(consulta)
            print("\n--- Respuesta ---\n")
            print(respuesta.response)
            print("\n" + "-" * 40)

        except KeyboardInterrupt:
            print("\nHasta luego.")
            break
        except Exception as e:
            print(f"\nError: {e}")


def _borrar_grafo(working_dir: str) -> None:
    path = Path(working_dir)
    if path.exists():
        shutil.rmtree(path)
        print(f"Se eliminó {path} para reindexar con metadata por PDF.")
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingesta de PDFs de libros/ (un documento por archivo, con metadata)."
    )
    parser.add_argument(
        "--reingestar",
        action="store_true",
        help="Borra grafo_libros/ y vuelve a indexar. Necesario para que los chunks antiguos tengan origen por PDF.",
    )
    args = parser.parse_args()

    documentos = cargar_documentos(_LIBROS)
    if not documentos:
        raise RuntimeError(f"No se encontró texto para ingesta en {_LIBROS}. Verifica que existan PDFs válidos.")

    workdir = Path(_WORKDIR)
    if args.reingestar:
        _borrar_grafo(_WORKDIR)
    elif (workdir / "graph_igraph_data.pklz").exists():
        print(
            "\n⚠️  Ya existe un grafo en "
            f"{workdir}. Los chunks viejos no tienen metadata de archivo.\n"
            "   Los PDF nuevos sí se citarán; para citar TODO el corpus ejecuta:\n"
            "   python run_quickstart.py --reingestar\n"
        )

    textos = [d["texto"] for d in documentos]
    metas = [d["metadata"] for d in documentos]
    print(f"Insertando {len(textos)} PDF(s) como documentos independientes:")
    for meta in metas:
        print(f"  • {meta['archivo']}  →  {meta['instrumento']}")

    grag = crear_grag(_WORKDIR)
    grag.insert(textos, metadata=metas)
    print("\n¡Grafos cargados con origen por documento!")

    if sys.stdin.isatty():
        print("Iniciando modo consulta...")
        bucle_consultas(grag)
    else:
        print("Entorno no interactivo detectado; se omite el modo consulta.")


if __name__ == "__main__":
    main()
