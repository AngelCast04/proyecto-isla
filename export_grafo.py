"""Exporta el grafo de fast-graphrag a JSON para visualización web.

No requiere OPENAI_API_KEY: lee el grafo directamente del disco.
"""

import json
from pathlib import Path
from typing import Any

import igraph as ig  # pyright: ignore[reportMissingTypeStubs]

WORKING_DIR = "./grafo_libros"
GRAPH_FILE = "graph_igraph_data.pklz"
OUTPUT_JSON = "./visualizer/grafo.json"


def exportar_grafo():
    graph_path = Path(WORKING_DIR) / GRAPH_FILE
    if not graph_path.exists():
        raise FileNotFoundError(
            f"No se encontró el grafo en {graph_path}. "
            "Ejecuta primero run_quickstart.py para crear el grafo."
        )

    g: Any = ig.Graph.Read_Picklez(str(graph_path))  # pyright: ignore[reportUnknownMemberType]

    nodes: list[dict[str, str]] = []
    for v in g.vs:
        attrs = v.attributes()
        name = str(attrs.get("name", ""))
        tipo = str(attrs.get("type", "Otro"))
        desc = str(attrs.get("description", ""))
        nodes.append({
            "id": name,
            "label": name[:50] + ("..." if len(name) > 50 else ""),
            "title": f"{tipo}\n{desc}"[:500],
            "group": tipo,
            "description": desc,
        })

    edges: list[dict[str, str]] = []
    for e in g.es:
        attrs = e.attributes()
        desc = attrs.get("description", "") or ""
        edges.append({
            "from": g.vs[e.source]["name"],
            "to": g.vs[e.target]["name"],
            "label": desc[:100],
            "title": desc,
        })

    output = {"nodes": nodes, "edges": edges}
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Exportado: {len(nodes)} nodos, {len(edges)} aristas → {OUTPUT_JSON}")


def main():
    exportar_grafo()


if __name__ == "__main__":
    main()
