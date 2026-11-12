import sys

import anthropic
from dotenv import load_dotenv

from extraer_texto import extraer_texto
from modelos import Factura

load_dotenv()
client = anthropic.Anthropic()

INSTRUCCIONES = """Extrae los datos de la factura que te paso.
Reglas:
- Usa solo lo que aparezca en el texto. Si un dato no aparece, devuelve null. No inventes nada.
- Las fechas, en formato AAAA-MM-DD.
- Los importes, como números con punto decimal, sin moneda ni separador de miles (3.215,16 EUR pasa a 3215.16).
- iva_porcentaje es el porcentaje como número (21, no 0.21).
- El emisor es quien emite la factura; el cliente es quien la recibe."""


def extraer_factura(texto: str) -> tuple:
    respuesta = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=500,
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
