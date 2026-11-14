from io import BytesIO

import pytest
from fpdf import FPDF
from pypdf import PdfWriter

from errores import ErrorExtraccion
from extraer_texto import extraer_texto


def pdf_con_texto(texto: str) -> BytesIO:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, texto)
    return BytesIO(bytes(pdf.output()))


def pdf_en_blanco() -> BytesIO:
    escritor = PdfWriter()
    escritor.add_blank_page(width=200, height=200)
    salida = BytesIO()
    escritor.write(salida)
    salida.seek(0)
    return salida


def pdf_protegido() -> BytesIO:
    escritor = PdfWriter()
    escritor.add_blank_page(width=200, height=200)
    escritor.encrypt("secreto", algorithm="RC4-128")
    salida = BytesIO()
    escritor.write(salida)
    salida.seek(0)
    return salida


def test_un_pdf_con_texto_devuelve_su_texto():
    assert "Factura de prueba" in extraer_texto(pdf_con_texto("Factura de prueba"))


def test_un_pdf_sin_texto_da_error_sin_texto():
    with pytest.raises(ErrorExtraccion) as error:
        extraer_texto(pdf_en_blanco())
    assert error.value.codigo == "sin_texto"


def test_un_archivo_que_no_es_pdf_da_error_pdf_ilegible():
    with pytest.raises(ErrorExtraccion) as error:
        extraer_texto(BytesIO(b"esto no es un pdf"))
    assert error.value.codigo == "pdf_ilegible"


def test_un_pdf_con_contrasena_da_error_pdf_protegido():
    with pytest.raises(ErrorExtraccion) as error:
        extraer_texto(pdf_protegido())
    assert error.value.codigo == "pdf_protegido"