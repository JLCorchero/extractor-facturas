import json
import random
from pathlib import Path

from faker import Faker
from fpdf import FPDF

from modelos import Factura

fake = Faker("es_ES")
Faker.seed(7)
random.seed(7)

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
        "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
CODIGO_IVA = {10: 1, 21: 2, 4: 5}
PRODUCTOS = [
    "ARROZ REDONDO 1KG", "ACEITE GIRASOL 5L", "PASTA ESPIRAL 500G", "CAFE MOLIDO 250G",
    "GALLETA MARIA 800G", "ATUN CLARO PACK 6", "TOMATE FRITO 400G", "LECHE ENTERA PACK 6",
    "PAPEL COCINA 2 ROLLOS", "BOLSA BASURA 30L", "DETERGENTE 3L", "SERVILLETA 100U",
    "AGUA MINERAL 6X1,5L", "ZUMO NARANJA 1L", "QUESO CURADO 500G", "JAMON COCIDO 1KG",
]
SEP = "-" * 108


def importe(valor: float) -> str:
    texto = f"{valor:,.2f}"
    return texto.replace(",", "#").replace(".", ",").replace("#", ".")


def eur(valor: float) -> str:
    return importe(valor) + " EUR"


def fecha_corta(f: Factura) -> str:
    return f.fecha_emision.strftime("%d/%m/%Y")


def linea(pdf: FPDF, texto: str, alto: float = 6) -> None:
    pdf.cell(0, alto, texto, new_x="LMARGIN", new_y="NEXT")


def bloque(pdf, x, y, lineas, ancho=90, alto=5, tam=9, negrita_primera=False):
    for i, texto in enumerate(lineas):
        pdf.set_xy(x, y + i * alto)
        pdf.set_font("Helvetica", "B" if negrita_primera and i == 0 else "", tam)
        pdf.cell(ancho, alto, texto)


# ---------- Formato A: sencillo ----------
def dibujar_a(f: Factura, ruta: str) -> None:
    tipo = f.desglose_iva[0]
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
    linea(pdf, f"Fecha: {fecha_corta(f)}")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 11)
    linea(pdf, "Cliente")
    pdf.set_font("Helvetica", "", 11)
    linea(pdf, f.cliente_nombre)
    if f.cliente_nif:
        linea(pdf, f"NIF cliente: {f.cliente_nif}")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(130, 8, "Descripcion", border=1)
    pdf.cell(50, 8, "Importe", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(130, 8, "Servicios prestados", border=1)
    pdf.cell(50, 8, eur(f.base_imponible), border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    resumen = [
        ("Base imponible", eur(f.base_imponible)),
        (f"IVA ({tipo.porcentaje:.0f}%)", eur(f.iva_total)),
    ]
    for etiqueta, valor in resumen:
        pdf.cell(130, 7, etiqueta, align="R")
        pdf.cell(50, 7, valor, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(130, 9, "TOTAL", align="R")
    pdf.cell(50, 9, eur(f.total), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.output(ruta)


# ---------- Formato B: ticket de tienda ----------
def dibujar_b(f: Factura, ruta: str) -> None:
    tipo = f.desglose_iva[0]
    ciudad = fake.city()
    d = f.fecha_emision
    fecha_larga = f"{d.day} {MESES[d.month - 1]} {d.year}"
    pedido = random.randint(100000, 999999)
    cif = f"{f.emisor_nif[0]}-{f.emisor_nif[1:]}"
    pct_coma = f"{tipo.porcentaje:.2f}".replace(".", ",")
    pct_punto = f"{tipo.porcentaje:.2f}"

    pdf = FPDF()
    pdf.add_page()

    pdf.set_fill_color(30, 90, 160)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "BRICOLAJE - CONSTRUCCION - DECORACION - JARDINERIA", align="C",
             fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 9, f"FACTURA {f.numero_factura}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "ORIGINAL", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, f"{ciudad}, a {fecha_larga}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    y = pdf.get_y()
    bloque(pdf, 10, y, [f"BRICO HOGAR {ciudad.upper()}", f.emisor_nombre, f"CIF {cif}",
                        fake.street_address(), f"{fake.postcode()} {fake.city()}"],
           negrita_primera=True)
    bloque(pdf, 110, y, [f.cliente_nombre, fake.street_address(),
                         f"{fake.postcode()} {fake.city().upper()}", "Espana"],
           negrita_primera=True)

    y += 5 * 5 + 6
    filas = []
    if f.cliente_nif:
        filas.append(("Numero NIF:", f.cliente_nif))
    filas += [
        ("Telefono:", f"+34{random.randint(600000000, 699999999)}"),
        ("Fecha de venta:", fecha_corta(f)),
        ("Condiciones de venta:", "Mencionados sobre el documento"),
        ("Ticket de caja:", f"018-{random.randint(100000, 999999)}-099-0820-NFS: "
                            f"{random.randint(10000, 99999)} Pedido {pedido}"),
        ("Numero de tarjeta:", str(random.randint(10**15, 10**16 - 1))),
    ]
    for i, (etiqueta, valor) in enumerate(filas):
        bloque(pdf, 10, y + i * 5, [etiqueta], ancho=45)
        bloque(pdf, 58, y + i * 5, [valor], ancho=130)
    pdf.set_y(y + len(filas) * 5 + 8)

    anchos = [10, 62, 18, 24, 22, 14, 20, 20]
    cabecera = ["N.", "Designacion y referencia", "Cantidad", "Prec. unid SI",
                "Total SI", "IVA %", "P. unid TTI", "Importe TTI"]
    fila = ["1", f"PAGO ANTICIPADO DEL PEDIDO {pedido}", "1", importe(f.base_imponible),
            importe(f.base_imponible), pct_coma, importe(f.total), importe(f.total)]
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font("Helvetica", "B", 8)
    for ancho, texto in zip(anchos, cabecera):
        pdf.cell(ancho, 8, texto, border=1, align="C", fill=True)
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 8)
    for i, (ancho, texto) in enumerate(zip(anchos, fila)):
        pdf.cell(ancho, 8, texto, border=1, align="L" if i == 1 else "R")
    pdf.ln(8)

    pdf.ln(6)
    y = pdf.get_y()
    bloque(pdf, 10, y, [f"TARJ.BANC. WEB (EUR) {pedido}"], ancho=45, tam=8)
    bloque(pdf, 55, y, [importe(f.total)], ancho=20, tam=8)

    anchos2 = [36, 26, 28, 28]

    def fila_tabla(valores, negrita=False, relleno=False):
        pdf.set_x(82)
        pdf.set_font("Helvetica", "B" if negrita else "", 8)
        for ancho, texto in zip(anchos2, valores):
            pdf.cell(ancho, 7, texto, border=1, align="R", fill=relleno)
        pdf.ln(7)

    pdf.set_y(y)
    fila_tabla(["Tasa IVA", "Total SI (EUR)", "Total IVA (EUR)", "Total TII (EUR)"],
                negrita=True, relleno=True)
    fila_tabla([f"ANTICIPO {pct_punto}%", importe(f.base_imponible),
                importe(f.iva_total), importe(f.total)])
    fila_tabla(["EUR", importe(f.base_imponible), importe(f.iva_total), importe(f.total)],
                negrita=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "", 7)
    linea(pdf, f"Pendiente de pago del pedido {pedido} 0,00", 5)

    pdf.set_y(-30)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(0, 4, f"{f.emisor_nombre}. {fake.street_address()}. N.I.F. {cif}. "
                        "Inscrita en el Registro Mercantil.",
                    align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 4, "Ejemplar cliente")
    pdf.output(ruta)


# ---------- Formato C: mayorista denso, varios tipos de IVA ----------
def repartir(centimos: int, partes: int) -> list[int]:
    cortes = sorted(random.sample(range(1, centimos), partes - 1))
    limites = [0] + cortes + [centimos]
    return [limites[i + 1] - limites[i] for i in range(partes)]


def fila_articulo(codigo, desc, unidad, precio, cant, total, imp):
    return f"   {codigo:<16}{desc:<32}{unidad:<6}{precio:>9}{cant:>7}{total:>11}{imp:>5}"


def dibujar_c(f: Factura, ruta: str) -> None:
    assert len(f.emisor_nombre) <= 48, f"Nombre demasiado largo para el diseno C: {f.emisor_nombre}"
    a1 = max(46, len(f.emisor_nombre) + 2)
    hora, minuto = random.randint(8, 21), random.randint(0, 58)
    venta = f"{fecha_corta(f)} {hora:02d}:{minuto:02d}"
    impresion = f"{fecha_corta(f)} {hora:02d}:{minuto + 1:02d}"
    ciudad = fake.city().upper()
    cif = f"{f.emisor_nif[0]}-{f.emisor_nif[1:3]}/{f.emisor_nif[3:]}"
    n_cliente = f"{random.randint(10, 99)} {random.randint(100000, 999999)} 1 1 SC"

    def tres(c1, c2="", c3=""):
        return f"{c1[:a1 - 2]:<{a1}}{c2[:24]:<26}{c3}"

    cabecera = fila_articulo("Num. articulo", "Descrip. articulo", "Ud", "Prec. Ud.",
                            "Cant.", "Importe", "Imp")
    texto = [
        tres(f.emisor_nombre, f"MAYORISTA EJEMPLO {ciudad}", "Pagina: 1"),
        tres(fake.street_address()[:38], fake.street_address(), f"Fecha de venta:   {venta}"),
        tres(f"{fake.postcode()} {fake.city().upper()}", f"{fake.postcode()} {ciudad}",
            f"Fecha impresion:  {impresion}"),
        tres("", "", f"Fecha de entrega:  {impresion}"),
        "",
        f"NIF: {cif}",
        "Reg. Merc. de Madrid, T. 3.423, L. 0, F. 10, Secc. 8, H. M-61.688",
        "",
        f"Factura:   {f.numero_factura:<30}({random.randint(100, 999)}-{random.randint(1000000, 9999999)})"
        f"      {random.randint(10, 99)}/{random.randint(100, 999)}   {random.randint(1000, 9999)}",
        "",
        f"{f.cliente_nombre:<60}N.cliente: {n_cliente}",
        f"{fake.street_address()[:58]:<60}" + (f"N.I.F. {f.cliente_nif}" if f.cliente_nif else ""),
        f"ESP {fake.postcode()} {fake.city()}",
        "",
        SEP,
        cabecera,
        SEP,
        "",
    ]

    ordenados = sorted(f.desglose_iva, key=lambda t: CODIGO_IVA[int(t.porcentaje)])
    descuento = random.randint(100, 500) if random.random() < 0.5 else 0
    filas = []
    for n, tipo in enumerate(ordenados):
        codigo = CODIGO_IVA[int(tipo.porcentaje)]
        centimos = round(tipo.base * 100) + (descuento if n == 0 else 0)
        for parte in repartir(centimos, random.randint(2, 4)):
            filas.append(fila_articulo(
                str(random.randint(8410000000000, 8429999999999)), random.choice(PRODUCTOS),
                random.choice(["UD", "KG", "PQ", "BL"]), importe(parte / 100), "1",
                importe(parte / 100), str(codigo)))
    if descuento:
        codigo0 = CODIGO_IVA[int(ordenados[0].porcentaje)]
        filas += ["", fila_articulo("", "COMPRA MAS PAGA MENOS", "", "", "",
                                    importe(descuento / 100) + "-", str(codigo0))]

    sangria = " " * 56
    peso = f"{random.randint(1000, 40000) / 1000:.3f}".replace(".", ",")
    bultos = f"Numero de bultos: {random.randint(1, 30)}   Peso Total: {peso} KG   Envases: 0"
    tarjeta = f"C: 11 {random.randint(10000000, 99999999)}???????? 10/29 OP: A {random.randint(100000, 999999)} c"
    resumen = [
        "",
        SEP,
        f"{bultos:<70}Importe{importe(f.base_imponible):>12}",
        "",
        f"{sangria}{'Mercancia':>12}{'% IMP':>12}{'Total IMP':>14}",
    ]
    for tipo in ordenados:
        codigo = CODIGO_IVA[int(tipo.porcentaje)]
        pct = f"{codigo}={tipo.porcentaje:5.2f}%".replace(".", ",")
        resumen.append(f"{sangria}{importe(tipo.base):>12}{pct:>12}{importe(tipo.cuota):>14}")
    resumen += [
        "",
        f"{sangria}{importe(f.base_imponible):>12}{'':>12}{importe(f.iva_total):>14}",
        "",
        f"{sangria}{'Total a pagar':>24}{importe(f.total):>14}",
        "",
        SEP,
        f"{tarjeta:<56}{'':>12}{'Tarjeta':>12}{importe(f.total):>14}",
    ]
    if descuento:
        extra = (descuento + random.randint(10, 90)) / 100
        resumen += ["", f"{sangria}{'Valor total descuentos':>24}{importe(extra) + '-':>14}"]

    legal = [
        "",
        "Politica de devoluciones: las condiciones de devolucion pueden variar segun el canal de venta. En el",
        "momento de la entrega, las devoluciones deberan solicitarse al transportista tras comprobar la",
        "mercancia. Existen limitaciones especificas para productos de alimentacion y temperatura controlada.",
        "Consulte las politicas detalladas y actualizadas en www.ejemplo.test y en los carteles de la tienda.",
        "* Precio unitario aplicado descuento correspondiente. Caracter informativo.",
        "",
        "*************** Fin de factura **************",
    ]

    pdf = FPDF()
    pdf.set_margins(10, 10, 10)
    pdf.add_page()
    pdf.set_font("Courier", "", 8)
    for texto_linea in texto + filas + resumen + legal:
        pdf.cell(0, 3.6, texto_linea, new_x="LMARGIN", new_y="NEXT")
    pdf.output(ruta)


DISENOS = {"A": dibujar_a, "B": dibujar_b, "C": dibujar_c}

if __name__ == "__main__":
    with open("datos/respuestas.json", encoding="utf-8") as archivo:
        registros = json.load(archivo)

    Path("facturas").mkdir(exist_ok=True)
    for registro in registros:
        factura = Factura.model_validate(registro["datos"])
        DISENOS[registro["formato"]](factura, f"facturas/{registro['archivo']}")
    print(f"Creados {len(registros)} PDFs en la carpeta facturas/")