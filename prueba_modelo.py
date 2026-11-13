from modelos import Factura, LineaIVA
from validacion import comprobar_coherencia

f = Factura(
    numero_factura="F/2026/000123",
    fecha_emision="2026-10-06",
    emisor_nombre="Distribuciones Ejemplo S.A.",
    emisor_nif="A-28/123456",
    cliente_nombre="Cliente de Prueba",
    cliente_nif="12345678z",
    base_imponible=350.00,
    iva_total=54.00,
    total=404.00,
    desglose_iva=[
        LineaIVA(base=100.00, porcentaje=10, cuota=10.00),
        LineaIVA(base=200.00, porcentaje=21, cuota=42.00),
        LineaIVA(base=50.00, porcentaje=4, cuota=2.00),
    ],
)

print(f.emisor_nif, f.cliente_nif)
print(comprobar_coherencia(f))