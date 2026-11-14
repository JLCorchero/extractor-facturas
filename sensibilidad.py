"""¿Qué errores del modelo detecta la validación? Se mide SIN gastar API.

Método ("inyección de errores"): partimos de facturas con la respuesta correcta, estropeamos un dato a propósito,
como se equivocaría un modelo, y miramos si `comprobar_coherencia` lo detecta.

Uso:  python sensibilidad.py            (usa datos/respuestas.json)
"""

import json
import random
import sys
from datetime import timedelta
from pathlib import Path

from modelos import Factura
from validacion import comprobar_coherencia


def cambia_digito(texto: str, rnd: random.Random) -> str | None:
    posiciones = [i for i, c in enumerate(texto) if c.isdigit()]
    if not posiciones:
        return None
    i = rnd.choice(posiciones)
    nuevo = rnd.choice([d for d in "0123456789" if d != texto[i]])
    return texto[:i] + nuevo + texto[i + 1 :]


# Cada mutación devuelve los campos a cambiar, o None si no se puede aplicar a esa factura.
def m_total_con_una_cifra_cambiada(f, rnd):
    nuevo = cambia_digito(f"{f.total:.2f}", rnd) if f.total is not None else None
    return {"total": float(nuevo)} if nuevo else None


def m_base_de_la_primera_linea(f, rnd):
    return {"base_imponible": f.desglose_iva[0].base} if len(f.desglose_iva) > 1 else None


def m_iva_de_la_primera_linea(f, rnd):
    return {"iva_total": f.desglose_iva[0].cuota} if len(f.desglose_iva) > 1 else None


def m_falta_una_linea_del_desglose(f, rnd):
    return {"desglose_iva": f.desglose_iva[:-1]} if len(f.desglose_iva) > 1 else None


def m_total_sin_iva(f, rnd):
    return {"total": f.base_imponible} if f.iva_total else None


def m_emisor_nif_vacio(f, rnd):
    return {"emisor_nif": None} if f.emisor_nif else None


def m_cliente_nif_con_una_cifra_cambiada(f, rnd):
    nuevo = cambia_digito(f.cliente_nif, rnd) if f.cliente_nif else None
    return {"cliente_nif": nuevo} if nuevo else None


def m_cliente_nif_vacio(f, rnd):
    return {"cliente_nif": None} if f.cliente_nif else None


def m_numero_con_una_cifra_cambiada(f, rnd):
    nuevo = cambia_digito(f.numero_factura, rnd) if f.numero_factura else None
    return {"numero_factura": nuevo} if nuevo else None


def m_fecha_un_dia_despues(f, rnd):
    return {"fecha_emision": f.fecha_emision + timedelta(days=1)} if f.fecha_emision else None


def m_emisor_nombre_cortado(f, rnd):
    palabras = f.emisor_nombre.split() if f.emisor_nombre else []
    return {"emisor_nombre": " ".join(palabras[:-1])} if len(palabras) > 2 else None


MUTACIONES = [
    ("total con una cifra cambiada", m_total_con_una_cifra_cambiada),
    ("base_imponible = base de la 1.ª línea (regresión real)", m_base_de_la_primera_linea),
    ("iva_total = cuota de la 1.ª línea", m_iva_de_la_primera_linea),
    ("falta una línea del desglose", m_falta_una_linea_del_desglose),
    ("total = base (olvida el IVA)", m_total_sin_iva),
    ("emisor_nif vacío", m_emisor_nif_vacio),
    ("cliente_nif con una cifra cambiada", m_cliente_nif_con_una_cifra_cambiada),
    ("cliente_nif vacío (fallo real de la v1)", m_cliente_nif_vacio),
    ("numero_factura con una cifra cambiada", m_numero_con_una_cifra_cambiada),
    ("fecha un día después", m_fecha_un_dia_despues),
    ("emisor_nombre incompleto", m_emisor_nombre_cortado),
]


def medir(facturas: list[Factura], rnd: random.Random) -> dict:
    """Devuelve las falsas alarmas y, por cada error inyectado, cuántos casos hubo y cuántos se detectaron."""
    avisos_originales = [set(comprobar_coherencia(f)) for f in facturas]
    resultado = {"facturas": len(facturas), "falsas_alarmas": sum(bool(a) for a in avisos_originales), "errores": []}
    for nombre, mutar in MUTACIONES:
        casos = detectados = 0
        for f, originales in zip(facturas, avisos_originales, strict=True):
            cambios = mutar(f, rnd)
            if cambios is None or all(getattr(f, campo) == valor for campo, valor in cambios.items()):
                continue
            avisos_nuevos = set(comprobar_coherencia(f.model_copy(update=cambios))) - originales
            casos += 1
            detectados += bool(avisos_nuevos)
        if casos:
            resultado["errores"].append((nombre, casos, detectados))
    return resultado


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "datos/respuestas.json"
    registros = json.loads(Path(ruta).read_text(encoding="utf-8"))
    facturas = [Factura.model_validate(r["datos"]) for r in registros]
    resultado = medir(facturas, random.Random(7))

    print(f"{resultado['facturas']} facturas de {ruta}")
    print(f"Falsas alarmas sobre las respuestas correctas: {resultado['falsas_alarmas']} de {resultado['facturas']}\n")
    print(f"{'Error inyectado':56} {'casos':>5} {'detectados':>11}")
    for nombre, casos, detectados in resultado["errores"]:
        print(f"{nombre:56} {casos:5} {detectados / casos:11.0%}")