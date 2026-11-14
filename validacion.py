import re

from modelos import Factura

LETRAS_DNI = "TRWAGMYFPDXBNJZSQVHLCKE"
LETRAS_CIF = "JABCDEFGHI"


def nif_valido(nif: str) -> bool:
    """Comprueba la letra o dígito de control de un DNI, NIE o CIF español."""
    if re.fullmatch(r"\d{8}[A-Z]", nif):
        return LETRAS_DNI[int(nif[:8]) % 23] == nif[8]
    if re.fullmatch(r"[XYZ]\d{7}[A-Z]", nif):
        numero = "XYZ".index(nif[0]) * 10**7 + int(nif[1:8])
        return LETRAS_DNI[numero % 23] == nif[8]
    if re.fullmatch(r"[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]", nif):
        digitos = [int(d) for d in nif[1:8]]
        pares = sum(digitos[1::2])
        impares = sum(sum(divmod(2 * d, 10)) for d in digitos[0::2])
        control = (10 - (pares + impares) % 10) % 10
        if nif[0] in "PQRSNW":
            return nif[8] == LETRAS_CIF[control]
        if nif[0] in "ABEH":
            return nif[8] == str(control)
        return nif[8] in (str(control), LETRAS_CIF[control])
    return False



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

    for campo in ("numero_factura", "fecha_emision", "total", "emisor_nif"):
        if getattr(f, campo) is None:
            avisos.append(f"Falta el campo obligatorio {campo}")
    for campo in ("emisor_nif", "cliente_nif"):
        valor = getattr(f, campo)
        if valor is not None and not nif_valido(valor):
            avisos.append(f"{campo} '{valor}' no tiene un formato o dígito de control válido")

    return avisos