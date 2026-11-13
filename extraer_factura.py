import sys

import anthropic
from dotenv import load_dotenv

from extraer_texto import extraer_texto
from modelos import Factura

load_dotenv()
client = anthropic.Anthropic()
MODELO = "claude-haiku-5-5"

INSTRUCCIONES = INSTRUCCIONES = """Extrae los datos de la factura que te paso.

Reglas generales:
- Usa solo lo que aparezca en el texto. Si un dato no aparece, devuelve null (o una lista vacía en desglose_iva). No inventes nada.
- Fechas en formato AAAA-MM-DD, sin la hora.
- Importes como números con punto decimal, sin moneda ni separador de miles (3.215,16 EUR pasa a 3215.16). Un signo menos detrás de la cifra (1,98-) significa importe negativo.
- Los porcentajes, como número (21, no 0.21).

Qué dato elegir cuando hay varios candidatos:
- numero_factura: el que acompaña a la palabra "Factura", copiado tal como aparece. Ignora números de ticket, pedido, cliente, tarjeta u otros códigos.
- fecha_emision: la fecha de emisión o de venta. Ignora fechas de impresión o de entrega.
- emisor_nombre: la razón social de quien emite la factura (S.A., S.L., S.L.U., etc.), no el nombre comercial de la tienda ni de la sucursal.
- emisor_nif: el NIF o CIF que aparece junto a los datos del emisor.
- cliente_nombre y cliente_nif: los del destinatario de la factura. El NIF del cliente es el que está junto a sus datos; no lo confundas con un número de cliente,
En tickets de tienda, un campo suelto "Numero NIF" o "N. NIF" separado de los bloques de dirección, cuando el emisor ya tiene su propio CIF identificado, es el NIF del cliente.
- base_imponible: el total antes de impuestos (suma de todas las bases).
- iva_total: el importe total del IVA (suma de todas las cuotas).
- total: el importe total a pagar, con impuestos incluidos.
- desglose_iva: una entrada por cada tipo de IVA con su base, su porcentaje y su cuota. Si solo hay un tipo, una sola entrada."""


def extraer_factura(texto: str) -> tuple:
    respuesta = client.messages.create(
        model=MODELO,
        max_tokens=1000,
        system=INSTRUCCIONES,
        tools=[
            {
                "name": "registrar_factura",
                "description": "Registra los datos extraídos de una factura",
                "input_schema": Factura.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "registrar_factura"},
        messages=[{"role": "user", "content": f"Texto de la factura\n\n{texto}"}],
    )
    bloque = next(b for b in respuesta.content if b.type == "tool_use")
    return Factura.model_validate(bloque.input), respuesta.usage


if __name__ == "__main__":
    texto = extraer_texto(sys.argv[1])
    factura, uso = extraer_factura(texto)
    print(factura)
    print(uso)
