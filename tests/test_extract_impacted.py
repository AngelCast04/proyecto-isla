from types import SimpleNamespace

from app.agents import _extract_impacted


def _entity(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name)


def _relation(source: str, target: str, description: str = "", chunks=None) -> SimpleNamespace:
    return SimpleNamespace(source=source, target=target, description=description, chunks=chunks or [])


def _chunk(text: str, cid: int = 1, metadata=None) -> SimpleNamespace:
    return SimpleNamespace(id=cid, content=text, metadata=metadata or {})


def _respuesta(entities, relations=(), chunks=()):
    return SimpleNamespace(
        context=SimpleNamespace(entities=list(entities), relations=list(relations), chunks=list(chunks))
    )


def test_filtra_vecinos_con_score_bajo(tmp_path):
    resp = _respuesta(
        entities=[
            (_entity("TORTURA"), 1.0),
            (_entity("PIDCP"), 0.8),
            (_entity("ESTADO GENERICO"), 0.05),
        ],
        relations=[
            (_relation("TORTURA", "PIDCP", "prohibida por el pacto"), 0.9),
            (_relation("TORTURA", "ESTADO GENERICO", "obligacion estatal"), 0.1),
        ],
        chunks=[(_chunk("La tortura está prohibida por el PIDCP artículo 7.", 11), 0.7)],
    )

    nodes, edges = _extract_impacted(resp, str(tmp_path))
    ids = {n["id"] for n in nodes}

    assert "TORTURA" in ids
    assert "PIDCP" in ids
    assert "ESTADO GENERICO" not in ids
    assert all(e["from"] in ids and e["to"] in ids for e in edges)


def test_nodo_incluye_chunk_e_score(tmp_path):
    resp = _respuesta(
        entities=[(_entity("TORTURA"), 0.9)],
        chunks=[(_chunk("Prohibición absoluta de la tortura en el PIDCP.", 3), 0.6)],
    )
    nodes, _edges = _extract_impacted(resp, str(tmp_path))
    assert len(nodes) == 1
    nodo = nodes[0]
    assert nodo["score"] == 0.9
    assert nodo["relevance"] == "alta"
    assert nodo["chunks"]
    assert "tortura" in nodo["chunks"][0]["text"].lower()


def test_nodo_cita_instrumento_del_pdf(tmp_path):
    resp = _respuesta(
        entities=[(_entity("TORTURA"), 0.9)],
        chunks=[(
            _chunk(
                "Prohibición absoluta de la tortura en el PIDCP.",
                3,
                {"instrumento": "PROHIBICIÓN DE TORTURA", "archivo": "29.- PROHIBICIÓN DE TORTURA-39-1.pdf"},
            ),
            0.6,
        )],
    )
    nodo = _extract_impacted(resp, str(tmp_path))[0][0]
    assert nodo["fuentes"][0]["instrumento"] == "PROHIBICIÓN DE TORTURA"
    assert nodo["fuentes"][0]["archivo"] == "29.- PROHIBICIÓN DE TORTURA-39-1.pdf"
    assert nodo["chunks"][0]["archivo"].endswith(".pdf")


def test_relacion_is_se_muestra_en_lenguaje_claro(tmp_path):
    resp = _respuesta(
        entities=[
            (_entity("DERECHO HUMANOS DE LOS MIGRANTES"), 1.0),
            (_entity("DERECHOS HUMANOS DE LOS MIGRANTES"), 0.9),
        ],
        relations=[(_relation("DERECHO HUMANOS DE LOS MIGRANTES", "DERECHOS HUMANOS DE LOS MIGRANTES", "is"), 0.8)],
    )
    _nodes, edges = _extract_impacted(resp, str(tmp_path))
    assert edges[0]["title"] == "Mismo concepto (variantes del nombre)"
