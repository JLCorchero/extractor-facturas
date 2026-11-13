import hashlib
import json
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

from extraer_factura import INSTRUCCIONES, MODELO, extraer_factura
from extraer_texto import extraer_texto
from modelos import Factura
from validacion import comprobar_coherencia

CAMPOS = list(Factura.model_fields)
CAMPOS_NOMBRE = {"emisor_nombre", "cliente_nombre"}
PREDICCIONES = Path("datos/predicciones.json")
HUELLA = hashlib.sha256(
    (MODELO + INSTRUCCIONES + json.dumps(Factura.model_json_schema(), sort_keys=True)).encode()
).hexdigest()[:12]


def sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    return " ".join(sin_acentos(texto).casefold().split())


def coincide(campo, esperado, obtenido) -> bool:
    if esperado is None or obtenido is None:
        return esperado is None and obtenido is None
    if isinstance(esperado, float):
        return abs(esperado - obtenido) < 0.01
    if campo in CAMPOS_NOMBRE:
        return normalizar(esperado) == normalizar(obtenido)
    return esperado == obtenido


def desglose_igual(esperado, obtenido) -> bool:
    if len(esperado) != len(obtenido):
        return False
    a = sorted(esperado, key=lambda linea: linea.porcentaje or 0)
    b = sorted(obtenido, key=lambda linea: linea.porcentaje or 0)
    return all(
        coincide("num", x.porcentaje, y.porcentaje)
        and coincide("num", x.base, y.base)
        and coincide("num", x.cuota, y.cuota)
        for x, y in zip(a, b)
    )


def cargar_cache() -> dict:
    if PREDICCIONES.exists():
        contenido = json.loads(PREDICCIONES.read_text(encoding="utf-8"))
        if contenido.get("huella") == HUELLA:
            return contenido["resultados"]
    return {}


def guardar_cache(resultados: dict) -> None:
    PREDICCIONES.write_text(
        json.dumps({"huella": HUELLA, "resultados": resultados}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    rapido = len(sys.argv) > 1 and sys.argv[1] == "rapido"

    with open("datos/respuestas.json", encoding="utf-8") as archivo:
        registros = json.load(archivo)

    if rapido:
        vistos = defaultdict(int)
        seleccion = []
        for r in registros:
            if vistos[r["formato"]] < 2:
                vistos[r["formato"]] += 1
                seleccion.append(r)
        registros = seleccion

    resultados = cargar_cache()
    stats = {}
    tokens_in = tokens_out = 0
    segundos = []

    for r in registros:
        nombre, formato = r["archivo"], r["formato"]
        esperado = Factura.model_validate(r["datos"])
        s = stats.setdefault(
            formato,
            {"n": 0, "aciertos": {c: 0 for c in CAMPOS}, "perfectas": 0, "con_error": 0, "detectadas": 0},
        )
        s["n"] += 1

        try:
            if nombre not in resultados:
                inicio = time.time()
                texto = extraer_texto(f"facturas/{nombre}")
                obtenido, uso = extraer_factura(texto)
                resultados[nombre] = {
                    "datos": obtenido.model_dump(mode="json"),
                    "in": uso.input_tokens,
                    "out": uso.output_tokens,
                    "seg": round(time.time() - inicio, 2),
                }
                guardar_cache(resultados)
            obtenido = Factura.model_validate(resultados[nombre]["datos"])
        except Exception as error:
            print(f"{nombre}: ERROR {error}")
            s["con_error"] += 1
            continue

        tokens_in += resultados[nombre]["in"]
        tokens_out += resultados[nombre]["out"]
        segundos.append(resultados[nombre]["seg"])

        fallos = []
        for campo in CAMPOS:
            v_esp, v_obt = getattr(esperado, campo), getattr(obtenido, campo)
            if campo == "desglose_iva":
                ok = desglose_igual(v_esp, v_obt)
            else:
                ok = coincide(campo, v_esp, v_obt)
            if ok:
                s["aciertos"][campo] += 1
            else:
                fallos.append(campo)
                print(f"{nombre} · {campo}: esperado {v_esp!r}, obtenido {v_obt!r}")

        if not fallos:
            s["perfectas"] += 1
        else:
            s["con_error"] += 1
            if comprobar_coherencia(obtenido):
                s["detectadas"] += 1

    for formato in sorted(stats):
        s = stats[formato]
        print(f"\nFormato {formato} ({s['n']} facturas)")
        for campo in CAMPOS:
            n = s["aciertos"][campo]
            print(f"  {campo:16} {n}/{s['n']}  {100 * n / s['n']:.0f}%")
        print(f"  Facturas perfectas: {s['perfectas']}/{s['n']}")
        if s["con_error"]:
            print(f"  Con algún error: {s['con_error']} · avisadas por la validación: {s['detectadas']}")

    total = sum(s["n"] for s in stats.values())
    coste = tokens_in * 0.10 / 1_000_000 + tokens_out * 0.50 / 1_000_000
    print(f"\nCoste total: {coste:.5f} $  ·  por factura: {coste / total:.5f} $")
    if segundos:
        print(f"Tiempo medio por factura: {sum(segundos) / len(segundos):.1f} s")