import sys

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from errores import ErrorExtraccion


def texto_de_pagina(pagina) -> str:
    try:
        return pagina.extract_text(extraction_mode="layout") or ""
    except KeyError:  # una página sin contenido hace que pypdf falle con KeyError
        return ""


def extraer_texto(ruta) -> str:
    try:
        lector = PdfReader(ruta)
        if lector.is_encrypted and lector.decrypt("") == 0:
            raise ErrorExtraccion("pdf_protegido", "El PDF está protegido con contraseña.")
        paginas = [texto_de_pagina(pagina) for pagina in lector.pages]
    except PyPdfError as error:
        raise ErrorExtraccion("pdf_ilegible", "No se ha podido leer el PDF: está dañado o no es un PDF válido.") from error

    texto = "\n".join(paginas)
    if not texto.strip():
        raise ErrorExtraccion("sin_texto", "El PDF no tiene texto (¿está escaneado?).")
    return texto


if __name__ == "__main__":
    ruta = sys.argv[1]
    try:
        texto = extraer_texto(ruta)
    except ErrorExtraccion as error:
        sys.exit(error.mensaje)
    print(texto)
    print(f"---{len(texto)} caracteres ---")