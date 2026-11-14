from types import SimpleNamespace

from fastapi.testclient import TestClient
from fpdf import FPDF

import api
from errores import ErrorExtraccion
from modelos import Factura

cliente_http = TestClient(api.app)
CABECERA = {"X-API-Key": api.CLAVE_API}


def pdf_con_texto(texto: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, texto)
    return bytes(pdf.output())


def enviar(contenido: bytes, tipo: str = "application/pdf", cabecera=CABECERA):
    return cliente_http.post("/extraer", files={"archivo": ("factura.pdf", contenido, tipo)}, headers=cabecera)


def test_salud():
    respuesta = cliente_http.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_sin_clave_da_401():
    assert enviar(pdf_con_texto("hola"), cabecera={}).status_code == 401


def test_un_archivo_que_no_es_pdf_da_415():
    assert enviar(b"hola", tipo="text/plain").status_code == 415


def test_un_pdf_dañado_da_422_con_mensaje(monkeypatch):
    respuesta = enviar(b"esto no es un pdf")
    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "pdf_ilegible"
    assert "PDF" in respuesta.json()["detail"]


def test_camino_feliz_devuelve_factura_avisos_y_tokens(monkeypatch):
    factura = Factura(numero_factura="F/1", total=121.0)
    uso = SimpleNamespace(input_tokens=10, output_tokens=5)
    monkeypatch.setattr(api, "extraer_factura", lambda texto: (factura, uso))
    respuesta = enviar(pdf_con_texto("Factura de prueba"))
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["factura"]["numero_factura"] == "F/1"
    assert cuerpo["revisar"] is True  # faltan campos obligatorios, así que hay avisos
    assert cuerpo["tokens"] == {"entrada": 10, "salida": 5}


def test_un_fallo_del_servicio_de_ia_da_503(monkeypatch):
    def falla(texto):
        raise ErrorExtraccion("servicio_no_disponible", "El servicio de IA no responde.")

    monkeypatch.setattr(api, "extraer_factura", falla)
    respuesta = enviar(pdf_con_texto("Factura de prueba"))
    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "servicio_no_disponible"