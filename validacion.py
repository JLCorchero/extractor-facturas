from modelos import Factura

TOLERANCIA = 0.02


def comprobar_coherencia(f: Factura) -> list[str]:
    avisos = []

    if f.desglose_iva:
        suma_bases = sum(linea.base or 0 for linea in f.desglose_iva)
        suma_cuotas = sum(linea.cuota or 0 for linea in f.desglose_iva)

        if f.base_imponible is not None and abs(suma_bases - f.base_imponible) > TOLERANCIA:
            avisos.append(
                f"Las bases del desglose suman {suma_bases:.2f}, pero base_imponible es {f.base_imponible:.2f}"
            )
        if f.iva_total is not None and abs(suma_cuotas - f.iva_total) > TOLERANCIA:
            avisos.append(
                f"Las cuotas del desglose suman {suma_cuotas:.2f}, pero iva_total es {f.iva_total:.2f}"
            )

        for linea in f.desglose_iva:
            if None not in (linea.base, linea.porcentaje, linea.cuota):
                esperada = linea.base * linea.porcentaje / 100
                if abs(esperada - linea.cuota) > TOLERANCIA:
                    avisos.append(
                        f"Con base {linea.base:.2f} y {linea.porcentaje:g}% la cuota debería ser "
                        f"{esperada:.2f}, pero es {linea.cuota:.2f}"
                    )

    if None not in (f.base_imponible, f.iva_total, f.total):
        if abs(f.base_imponible + f.iva_total - f.total) > TOLERANCIA:
            avisos.append(
                f"base + IVA es {f.base_imponible + f.iva_total:.2f}, pero total es {f.total:.2f}"
            )

    return avisos