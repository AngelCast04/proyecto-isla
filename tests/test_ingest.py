from app.ingest import metadata_documento, titulo_desde_nombre
from pathlib import Path


def test_titulo_limpia_numero_y_parte():
    assert titulo_desde_nombre("14.- DH A LA LIBERTAD DE EXPRESIÓN.pdf") == "DH A LA LIBERTAD DE EXPRESIÓN"
    assert titulo_desde_nombre("29.- PROHIBICIÓN DE TORTURA-39-1.pdf") == "PROHIBICIÓN DE TORTURA"
    assert titulo_desde_nombre("7.- DH DE LOS NIÑOS-13.pdf") == "DH DE LOS NIÑOS"
    assert titulo_desde_nombre("33. DH AL TRABAJO-24-2.pdf") == "DH AL TRABAJO"
    assert titulo_desde_nombre("40.-DH LINGUISTÍCOS.pdf") == "DH LINGUISTÍCOS"


def test_metadata_documento_usa_nombre_si_no_hay_titulo_pdf():
    meta = metadata_documento(Path("libros/2.- DERECHO A LA NO DISCRIMINACIÓN.pdf"))
    assert meta["archivo"] == "2.- DERECHO A LA NO DISCRIMINACIÓN.pdf"
    assert meta["instrumento"] == "DERECHO A LA NO DISCRIMINACIÓN"
    assert meta["tema"] == meta["instrumento"]


def test_metadata_documento_prefiere_titulo_pdf():
    meta = metadata_documento(Path("x.pdf"), titulo_pdf="Pacto Internacional de Derechos Civiles y Políticos")
    assert meta["instrumento"] == "Pacto Internacional de Derechos Civiles y Políticos"
    assert meta["archivo"] == "x.pdf"
