import random

from modelos import Factura, LineaIVA
from sensibilidad import medir


def factura_de_prueba() -> Factura:
    return Factura(
        numero_factura="F/2025/000025",
        fecha_emision="2025-09-18",
        emisor_nombre="Finanzas Martin S.A.T.",
        emisor_nif="S3194548H",
        cliente_nombre="Eloisa Rocha Torrecilla",
        cliente_nif="H79351698",
        base_imponible=1170.56,
        iva_total=172.36,
        total=1342.92,
        desglose_iva=[
            LineaIVA(base=738.41, porcentaje=21, cuota=155.07),
            LineaIVA(base=432.15, porcentaje=4, cuota=17.29),
        ],
    )


def detectados_de(resultado: dict, nombre: str) -> tuple[int, int]:
    for texto, casos, detectados in resultado["errores"]:
        if texto == nombre:
            return casos, detectados
    raise AssertionError(f"no hay resultados para {nombre!r}")


def test_las_respuestas_correctas_no_dan_falsas_alarmas():
    resultado = medir([factura_de_prueba()] * 5, random.Random(1))
    assert resultado["falsas_alarmas"] == 0


def test_un_total_alterado_se_detecta_casi_siempre():
    """No siempre: si la cifra cambiada es la de los céntimos y la diferencia es de 1 o 2 céntimos,
    queda dentro de la tolerancia. Es el precio de aceptar redondeos legítimos."""
    resultado = medir([factura_de_prueba()] * 200, random.Random(1))
    casos, detectados = detectados_de(resultado, "total con una cifra cambiada")
    assert casos == 200
    assert detectados / casos >= 0.8


def test_un_cliente_nif_vacio_no_se_detecta_y_esta_asumido():
    """Límite conocido: sin NIF de cliente puede ser un ticket legítimo, así que la validación no avisa."""
    resultado = medir([factura_de_prueba()] * 5, random.Random(1))
    casos, detectados = detectados_de(resultado, "cliente_nif vacío (fallo real de la v1)")
    assert casos > 0
    assert detectados == 0