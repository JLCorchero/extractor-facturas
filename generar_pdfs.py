import json
from pathlib import Path

from fpdf import FPDF

from modelos import Factura

def formato_importe(valor: float) -> str:
    texto = f"{valor:,.2f}"
    return texto.replace(",", "#").replace(".", ",").replace("#", ".") + " EUR"

def linea(pdf: FPDF, texto: str, alto: int = 6) -> None:
    pdf.cell(0, alto, texto, new_x="LMARGIN", new_y="NEXT")

def dibujar_factura(f: Factura, ruta: str) -> None:
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    linea(pdf, f.emisor_nombre, 10)
    pdf.set_font("Helvetica", "", 11)
    linea(pdf, f"NIF: {f.emisor_nif}")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 14)
    linea(pdf, "FACTURA", 10)
    pdf.set_font("Helvetica", "", 11)
    linea(pdf, f"Factura n.: {f.numero_factura}")
    linea(pdf, f"Fecha: {f.fecha_emision.strftime('%d/%m/%Y')}")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 11)
    linea(pdf, "Cliente")
    pdf.set_font("Helvetica", "", 11)
    linea(pdf, f.cliente_nombre)
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(130, 8, "Descripcion", border=1)
    pdf.cell(50, 8, "Importe", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(130, 8, "Servicios prestados", border=1)
    pdf.cell(50, 8, formato_importe(f.base_imponible), border=1, align="R",
            new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4) 


    iva_importe = round(f.total - f.base_imponible, 2)
    resumen = [
        ("Base imponible", formato_importe(f.base_imponible)),
        (f"IVA ({f.iva_porcentaje:.0f}%)",formato_importe(iva_importe))
    ]
    for etiqueta, valor in resumen:
        pdf.cell(130, 7, etiqueta, align="R")
        pdf.cell(50, 7, valor, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(130, 9, "TOTAL", align="R")
    pdf.cell(50, 9, formato_importe(f.total), align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.output(ruta)

if __name__ == "__main__":
    with open("datos/respuestas.json", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    Path("facturas").mkdir(exist_ok=True)
    for i, d in enumerate(datos, start=1):
        factura = Factura.model_validate(d)
        dibujar_factura(factura, f"facturas/factura_{i:02d}.pdf")
    print(f"Creados {len(datos)} PDFs en la carpeta facturas/")