from app.formatters import humanizar_relacion


def test_humanizar_relacion_is():
    assert humanizar_relacion("is") == "Mismo concepto (variantes del nombre)"
    assert humanizar_relacion("IS") == "Mismo concepto (variantes del nombre)"
    assert humanizar_relacion(" is ") == "Mismo concepto (variantes del nombre)"


def test_humanizar_relacion_is_corta():
    assert humanizar_relacion("is", corta=True) == "Mismo concepto"


def test_humanizar_relacion_pasa_texto_normal():
    desc = "Las personas protegidas serán entregadas con su expediente."
    assert humanizar_relacion(desc) == desc


def test_format_legal_incluye_observaciones():
    from app.formatters import format_legal_response
    texto = format_legal_response({
        "introduccion": "Caso de tortura.",
        "violaciones": [],
        "tratados": [],
        "observaciones_resoluciones": [{
            "tipo": "Observación general",
            "titulo": "Observación general N.º 20 del Comité de Derechos Humanos",
            "organismo": "Comité de Derechos Humanos",
            "relevancia": "Prohíbe la tortura de forma absoluta.",
            "fuentes": [1],
        }],
        "conclusion": "Hay vías de protección.",
    })
    assert "III. Observaciones generales, resoluciones, reportes e informes" in texto
    assert "Observación general N.º 20" in texto


def test_wrap_y_extract_mermaid_con_delimitadores():
    from app.formatters import extract_mermaid_from_text, wrap_mermaid

    wrapped = wrap_mermaid("flowchart TB\n  A --> B", "analisis")
    assert wrapped.startswith("<<MERMAID_START:analisis>>")
    assert wrapped.endswith("<<MERMAID_END>>")
    assert "```mermaid" in wrapped

    texto = "Análisis del caso.\n\n" + wrapped + "\nCierre."
    limpio, bloques = extract_mermaid_from_text(texto)
    assert "Análisis del caso." in limpio
    assert "Cierre." in limpio
    assert "<<MERMAID_START" not in limpio
    assert "```mermaid" not in limpio
    assert len(bloques) == 1
    assert bloques[0]["kind"] == "analisis"
    assert "flowchart TB" in bloques[0]["code"]
    assert "A --> B" in bloques[0]["code"]


def test_sanitize_mermaid_rechaza_script_y_click():
    from app.formatters import sanitize_mermaid_code, wrap_mermaid

    assert sanitize_mermaid_code("flowchart TB\n  click A javascript:alert(1)") == ""
    assert sanitize_mermaid_code("flowchart TB\n  click A Nodo") == "flowchart TB"
    assert wrap_mermaid("<script>alert(1)</script>") == ""
    limpio = sanitize_mermaid_code("%%{init: {'securityLevel':'loose'}}%%\nflowchart TB\n  A --> B")
    assert "init" not in limpio
    assert "flowchart TB" in limpio
    assert wrap_mermaid(limpio).startswith("<<MERMAID_START")


def test_extract_mermaid_valla_markdown_sin_delimitadores():
    from app.formatters import extract_mermaid_from_text

    texto = "Intro.\n```mermaid\nflowchart LR\n  X --> Y\n```\nFin."
    limpio, bloques = extract_mermaid_from_text(texto)
    assert "Intro." in limpio
    assert "Fin." in limpio
    assert len(bloques) == 1
    assert "X --> Y" in bloques[0]["code"]


def test_build_mermaid_analisis_y_grafo():
    from app.formatters import build_mermaid_analisis, build_mermaid_grafo

    analisis = build_mermaid_analisis({
        "introduccion": "Caso de tortura en detención.",
        "violaciones": [{"titulo": "Prohibición de la tortura."}],
        "tratados": [{"instrumento": "CAT", "articulos_clave": "Arts. 1, 2"}],
        "conclusion": "Hay vías de protección internacional.",
    })
    assert "flowchart TB" in analisis
    assert "Prohibición de la tortura" in analisis
    assert "CAT" in analisis

    grafo = build_mermaid_grafo(
        [
            {"id": "CAT", "group": "Tratado", "score": 2.0},
            {"id": "Prohibición de la tortura", "group": "Derecho", "score": 1.5},
        ],
        [{"from": "CAT", "to": "Prohibición de la tortura", "label": "protege"}],
    )
    assert "flowchart LR" in grafo
    assert "protege" in grafo
    assert "subgraph" in grafo


def test_completar_observaciones_desde_nodos():
    from app.formatters import completar_observaciones_resoluciones
    items = completar_observaciones_resoluciones(
        {},
        [{"id": "RESOLUCIÓN 39/46", "group": "Resolución", "description": "Contra la tortura."}],
    )
    assert len(items) == 1
    assert items[0]["tipo"] == "Resolución"
    assert items[0]["titulo"] == "RESOLUCIÓN 39/46"
