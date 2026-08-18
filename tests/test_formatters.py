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


def test_completar_observaciones_desde_nodos():
    from app.formatters import completar_observaciones_resoluciones
    items = completar_observaciones_resoluciones(
        {},
        [{"id": "RESOLUCIÓN 39/46", "group": "Resolución", "description": "Contra la tortura."}],
    )
    assert len(items) == 1
    assert items[0]["tipo"] == "Resolución"
    assert items[0]["titulo"] == "RESOLUCIÓN 39/46"
