import sys

from extraer_factura import extraer_factura
from extraer_texto import extraer_texto
from validacion import comprobar_coherencia

texto = extraer_texto(sys.argv[1])
factura, uso = extraer_factura(texto)

print(factura.model_dump_json(indent=2))
print("\nAvisos de la validación:", comprobar_coherencia(factura) or "ninguno")
print(f"Tokens: {uso.input_tokens} entrada, {uso.output_tokens} salida")