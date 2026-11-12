from modelos import Factura

f = Factura(numero_factura="2026-0142", fecha_emision="2026-03-15",
            base_imponible="1000.00")
print(f)
print(f.fecha_emision.year)