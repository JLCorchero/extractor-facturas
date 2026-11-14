from evaluar import coincide, desglose_igual, normalizar
from modelos import LineaIVA


def test_los_importes_admiten_un_centimo_de_diferencia():
    assert coincide("total", 10.00, 10.004)
    assert not coincide("total", 10.00, 10.02)


def test_los_nombres_no_distinguen_tildes_ni_mayusculas_ni_espacios_de_mas():
    assert coincide("emisor_nombre", "Construcción Cañizares S.A.", "construccion  canizares s.a.")


def test_normalizar_quita_tildes_y_mayusculas():
    assert normalizar("  ÁLVARO   Núñez ") == "alvaro nunez"


def test_none_solo_coincide_con_none():
    assert coincide("cliente_nif", None, None)
    assert not coincide("cliente_nif", None, "A18768283")
    assert not coincide("cliente_nif", "A18768283", None)


def test_el_nif_se_compara_exactamente():
    assert not coincide("emisor_nif", "A28321123", "a28321123")


def test_el_desglose_no_depende_del_orden():
    a = [LineaIVA(base=100, porcentaje=21, cuota=21), LineaIVA(base=50, porcentaje=4, cuota=2)]
    b = [LineaIVA(base=50, porcentaje=4, cuota=2), LineaIVA(base=100, porcentaje=21, cuota=21)]
    assert desglose_igual(a, b)


def test_el_desglose_con_distinto_numero_de_lineas_no_coincide():
    a = [LineaIVA(base=100, porcentaje=21, cuota=21), LineaIVA(base=50, porcentaje=4, cuota=2)]
    assert desglose_igual(a, a[:1]) is False