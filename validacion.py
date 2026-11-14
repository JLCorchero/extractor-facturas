import re

from modelos import Factura

# Tolerancia en céntimos: cada línea de IVA se redondea por separado, así que las sumas pueden diferir 1-2 céntimos.
TOLERANCIA_CENTIMOS = 2

LETRAS_DNI = "TRWAGMYFPDXBNJZSQVHLCKE"
LETRAS_CIF = "JABCDEFGHI"
# Prefijos de NIF-IVA de los demás países de la UE (España, "ES", se trata aparte). EL = Grecia, XI = Irlanda del Norte.
PAISES_UE = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "FI", "FR", "HR", "HU",
    "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "XI",
}


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



def estado_nif(nif: str) -> str:
    # Devuelve "valido", "invalido" (parece español y no cuadra) o "no_comprobable" (NIF-IVA de otro país de la UE)
    if nif.startswith("ES") and len(nif) == 11:
        nif = nif[2:] # NIF-IVA español: quitar el prefijo ES
    if nif[:2] in PAISES_UE:
        return "no_comprobable"
    return "valido" if nif_valido(nif) else "invalido"


def a_centimos(importe: float | None) -> int | None:
    """Pasa euros a céntimos enteros, para comparar sin errores de redondeo de los decimales."""
    return None if importe is None else round(importe * 100)


def euros(centimos: int) -> str:
    return f"{centimos / 100:.2f}"


def comprobar_coherencia(f: Factura) -> list[str]:
    avisos = []
    base_imponible = a_centimos(f.base_imponible)
    iva_total = a_centimos(f.iva_total)
    total = a_centimos(f.total)

    if f.desglose_iva:
        suma_bases = sum(a_centimos(linea.base) or 0 for linea in f.desglose_iva)
        suma_cuotas = sum(a_centimos(linea.cuota) or 0 for linea in f.desglose_iva)

        if base_imponible is not None and abs(suma_bases - base_imponible) > TOLERANCIA_CENTIMOS:
            avisos.append(
                f"Las bases del desglose suman {euros(suma_bases)}, pero base_imponible es {euros(base_imponible)}"
            )
        if iva_total is not None and abs(suma_cuotas - iva_total) > TOLERANCIA_CENTIMOS:
            avisos.append(f"Las cuotas del desglose suman {euros(suma_cuotas)}, pero iva_total es {euros(iva_total)}")

        for linea in f.desglose_iva:
            if None not in (linea.base, linea.porcentaje, linea.cuota):
                base = a_centimos(linea.base)
                cuota = a_centimos(linea.cuota)
                esperada = round(base * linea.porcentaje / 100)
                if abs(esperada - cuota) > TOLERANCIA_CENTIMOS:
                    avisos.append(
                        f"Con base {euros(base)} y {linea.porcentaje:g}% la cuota debería ser "
                        f"{euros(esperada)}, pero es {euros(cuota)}"
                    )

    if None not in (base_imponible, iva_total, total):
        if abs(base_imponible + iva_total - total) > TOLERANCIA_CENTIMOS:
            avisos.append(f"base + IVA es {euros(base_imponible + iva_total)}, pero total es {euros(total)}")

    for campo in ("numero_factura", "fecha_emision", "total", "emisor_nif"):
        if getattr(f, campo) is None:
            avisos.append(f"Falta el campo obligatorio {campo}")
    for campo in ("emisor_nif", "cliente_nif"):
        valor = getattr(f, campo)
        if valor is not None and estado_nif(valor) == "invalido":
            avisos.append(f"{campo} '{valor}' no tiene un formato o dígito de control válido")

    return avisos