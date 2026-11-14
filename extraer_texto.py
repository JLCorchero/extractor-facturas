import sys

from pypdf import PdfReader


def extraer_texto(ruta: str) -> str:
    lector = PdfReader(ruta)
    paginas = [
        pagina.extract_text(extraction_mode="layout") or ""
        for pagina in lector.pages
    ]
    return "\n".join(paginas)

if __name__ == "__main__":
    ruta = sys.argv[1]
    texto = extraer_texto(ruta)
    print(texto)
    print(f"---{len(texto)} caracteres ---")