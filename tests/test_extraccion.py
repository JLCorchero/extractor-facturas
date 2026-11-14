from types import SimpleNamespace

from extraer_factura import extraer_factura


class ClienteSimulado:
    # Imita a client.messages.create: devuelve lo que le digamos, sin llamar a la API ni gastar nada.
    def __init__(self, datos):
        self.datos = datos
        self.llamadas = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.llamadas.append(kwargs)
        bloque = SimpleNamespace(type="tool_use", input=self.datos)
        uso = SimpleNamespace(input_tokens=1000, output_tokens=100)
        return SimpleNamespace(content=[bloque], usage=uso)

def test_la_respuesta_del_modelo_se_convierte_en_factura():
    cliente = ClienteSimulado({"numero_factura": "F/1", "total": 121.0, "emisor_nif": "b-12.345.674"})
    factura, uso = extraer_factura("texto de prueba", cliente=cliente)
    assert factura.numero_factura == "F/1"
    assert factura.emisor_nif == "B12345674"  # Normalizado
    assert uso.input_tokens == 1000


def test_se_envia_la_herramienta_forzada_y_el_texto_de_la_factura():
    cliente = ClienteSimulado({})
    extraer_factura("texto de prueba", cliente=cliente)
    llamada = cliente.llamadas[0]
    assert llamada["tool_choice"] == {"type": "tool", "name": "registrar_factura"}
    assert "texto de prueba" in llamada["messages"][0]["content"]
