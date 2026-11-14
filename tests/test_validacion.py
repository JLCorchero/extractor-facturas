import pytest

from modelos import Factura, LineaIVA
from validacion import comprobar_coherencia, estado_nif, nif_valido


def factura_correcta(**cambios) -> Factura:
    """Una factura coherente de partida. Cada test cambia solo lo que quiere probar."""
    datos = {
        "numero_factura": "F/2025/000025",
        "fecha_emision": "2025-09-18",
        "emisor_nombre": "Finanzas Martin S.A.T.",
        "emisor_nif": "S3194548H",
        "cliente_nombre": "Eloisa Rocha Torrecilla",
        "cliente_nif": "H79351698",
        "base_imponible": 1170.56,
        "iva_total": 172.36,
        "total": 1342.92,
        "desglose_iva": [
            LineaIVA(base=738.41, porcentaje=21, cuota=155.07),
            LineaIVA(base=432.15, porcentaje=4, cuota=17.29),
        ],
    }
    datos.update(cambios)
    return Factura(**datos)


def test_una_factura_correcta_no_da_avisos():
    assert comprobar_coherencia(factura_correcta()) == []


def test_regresion_factura_25_c_base_imponible_de_una_sola_linea():
    """El fallo real del 13-11-2026: el modelo devolvió la base de la primera línea (738,41)
    en lugar de la suma de todas (1.170,56). La validación tiene que cazarlo."""
    avisos = comprobar_coherencia(factura_correcta(base_imponible=738.41))
    assert any("bases del desglose suman 1170.56" in aviso for aviso in avisos)


def test_total_que_no_cuadra():
    avisos = comprobar_coherencia(factura_correcta(total=1300.00))
    assert any("pero total es 1300.00" in aviso for aviso in avisos)


def test_cuota_que_no_corresponde_a_su_base():
    desglose = [LineaIVA(base=200, porcentaje=21, cuota=43)]
    avisos = comprobar_coherencia(factura_correcta(base_imponible=200, iva_total=43, total=243, desglose_iva=desglose))
    assert any("la cuota debería ser 42.00" in aviso for aviso in avisos)


def test_falta_un_campo_obligatorio():
    avisos = comprobar_coherencia(factura_correcta(numero_factura=None))
    assert "Falta el campo obligatorio numero_factura" in avisos


def test_factura_vacia_avisa_de_los_cuatro_campos_obligatorios():
    avisos = comprobar_coherencia(Factura())
    assert len(avisos) == 4


def test_nif_del_cliente_invalido_se_avisa():
    avisos = comprobar_coherencia(factura_correcta(cliente_nif="457329P"))
    assert any("cliente_nif" in aviso for aviso in avisos)


@pytest.mark.parametrize(
    ("nif", "esperado"),
    [
        ("B12345674", "valido"),
        ("ESB12345674", "valido"),  # NIF-IVA español: ES + NIF
        ("A28123456", "invalido"),
        ("ESA28123456", "invalido"),  # con prefijo ES, pero el dígito de control no cuadra
        ("FR12345678901", "no_comprobable"),  # NIF-IVA francés: no lo juzgamos
        ("DE123456789", "no_comprobable"),
        ("457329P", "invalido"),  # no parece de ningún país
    ],
)
def test_estado_nif(nif, esperado):
    assert estado_nif(nif) == esperado


def test_un_nif_de_otro_pais_de_la_ue_no_genera_aviso():
    assert comprobar_coherencia(factura_correcta(emisor_nif="FR12345678901")) == []


def test_un_nif_espanol_con_prefijo_es_se_comprueba():
    assert comprobar_coherencia(factura_correcta(emisor_nif="ESS3194548H")) == []
    avisos = comprobar_coherencia(factura_correcta(emisor_nif="ESA28123456"))
    assert any("emisor_nif" in aviso for aviso in avisos)

@pytest.mark.parametrize(
    ("nif", "esperado"),
    [
        ("12345678Z", True),  # DNI correcto
        ("12345678A", False),  # DNI con la letra cambiada
        ("X1234567L", True),  # NIE correcto
        ("Q5159230A", True),  # CIF con letra de control (la Q la exige)
        ("B12345674", True),  # CIF con dígito de control
        ("A28123456", False),  # CIF con dígito de control incorrecto
        ("457329P", False),  # no tiene forma de NIF
    ],
)
def test_nif_valido(nif, esperado):
    assert nif_valido(nif) is esperado

def test_dos_centimos_de_diferencia_son_aceptables_aunque_los_decimales_digan_otra_cosa():
    """En decimales, 1000.07 - 1000.05 da 0.0200000000000955 (más de 0.02) y daría un aviso falso.
    En céntimos enteros la diferencia es exactamente 2 y entra en la tolerancia."""
    desglose = [LineaIVA(base=1000.07, porcentaje=21, cuota=210.01)]
    factura = factura_correcta(base_imponible=1000.05, iva_total=210.01, total=1210.06, desglose_iva=desglose)
    assert comprobar_coherencia(factura) == []


def test_tres_centimos_de_diferencia_si_dan_aviso():
    desglose = [LineaIVA(base=1000.08, porcentaje=21, cuota=210.02)]
    factura = factura_correcta(base_imponible=1000.05, iva_total=210.02, total=1210.07, desglose_iva=desglose)
    assert any("bases del desglose suman 1000.08" in aviso for aviso in comprobar_coherencia(factura))