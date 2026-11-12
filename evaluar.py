import json
import sys
import time
from pathlib import Path

from extraer_factura import extraer_factura
from extraer_texto import extraer_texto
from modelos import Factura

CAMPOS = list(Factura.model_fields)
PREDICCIONES = Path("datos/predicciones.json")

def coincide(esperado, obtenido) -> bool:
    if isinstance(esperado, float) and isinstance(obtenido, float):
        return abs(esperado - obtenido) < 0.01
    return esperado == obtenido


if __name__ == "__main__":
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 30

    with open("datos/respuestas.json", encoding="utf-8") as archivo:
        respuestas = json.load(archivo)[:limite]

    cache = {}
    if PREDICCIONES.exists():
        cache = json.loads(PREDICCIONES.read_text(encoding="utf-8"))
    
    aciertos = {campo: 0 for campo in CAMPOS}
    perfectas = 0
    tokens_in = tokens_out = 0
    segundos = []

    for i, datos in enumerate(respuestas, start=1):
        nombre = f"factura_{i:02d}.pdf"
        esperado = Factura.model_validate(datos)

        try:
            if nombre not in cache:
                inicio = time.time()
                texto = extraer_texto(f"facturas/{nombre}")
                obtenido, uso = extraer_factura(texto)
                cache[nombre] = {
                    "datos": obtenido.model_dump(mode="json"),
                    "in": uso.input_tokens,
                    "out": uso.output_tokens,
                    "seg": round(time.time() - inicio, 2),
                }
                PREDICCIONES.write_text(
                    json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            obtenido = Factura.model_validate(cache[nombre]["datos"])
        except Exception as error:
            print(f"{nombre}: ERROR {error}")
            continue

        tokens_in += cache[nombre]["in"]
        tokens_out += cache[nombre]["out"]
        segundos.append(cache[nombre]["seg"])

        correctos = 0
        for campo in CAMPOS:
            valor_esperado = getattr(esperado, campo)
            valor_obtenido = getattr(obtenido, campo)
            if coincide(valor_esperado, valor_obtenido):
                aciertos[campo] += 1
                correctos += 1
            else:
                print(f"{nombre} · {campo}: esperado {valor_esperado!r}, obtenido {valor_obtenido!r}")
        if correctos == len(CAMPOS):
            perfectas += 1

    total = len(respuestas)
    print("\nPrecisión por campo:")
    for campo, n in aciertos.items():
        print(f"  {campo:16} {n}/{total}  {100 * n / total:.0f}%")
    print(f"\nFacturas con los 8 campos correctos: {perfectas}/{total}")
    coste = tokens_in * 0.10 / 1_000_000 + tokens_out * 0.50 / 1_000_000
    print(f"Coste total: {coste:.5f} $  ·  por factura: {coste / total:.5f} $")
    if segundos:
        print(f"Tiempo medio por factura: {sum(segundos) / len(segundos):.1f} s")