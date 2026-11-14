from types import SimpleNamespace

import anthropic
import httpx
import pytest

from errores import ErrorExtraccion
from extraer_factura import extraer_factura


class ClienteSimulado:
    """Imita a client.messages.create: devuelve lo que le digamos, sin llamar a la API ni gastar nada."""

    def __init__(self, datos=None, stop_reason="tool_use", bloques=None, error=None):
        self.datos = datos if datos is not None else {}
        self.stop_reason = stop_reason
        self.bloques = bloques
        self.error = error
        self.llamadas = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.llamadas.append(kwargs)
        if self.error:
            raise self.error
        bloques = self.bloques if self.bloques is not None else [SimpleNamespace(type="tool_use", input=self.datos)]
        uso = SimpleNamespace(input_tokens=1000, output_tokens=100)
        return SimpleNamespace(content=bloques, usage=uso, stop_reason=self.stop_reason)


def codigo_del_error(cliente) -> str:
    with pytest.raises(ErrorExtraccion) as error:
        extraer_factura("texto de prueba", cliente=cliente)
    return error.value.codigo


def test_la_respuesta_del_modelo_se_convierte_en_factura():
    cliente = ClienteSimulado({"numero_factura": "F/1", "total": 121.0, "emisor_nif": "b-12.345.674"})
    factura, uso = extraer_factura("texto de prueba", cliente=cliente)
    assert factura.numero_factura == "F/1"
    assert factura.emisor_nif == "B12345674"  # el validador de Pydantic limpia el NIF
    assert uso.input_tokens == 1000


def test_se_envia_la_herramienta_forzada_y_el_texto_de_la_factura():
    cliente = ClienteSimulado()
    extraer_factura("texto de prueba", cliente=cliente)
    llamada = cliente.llamadas[0]
    assert llamada["tool_choice"] == {"type": "tool", "name": "registrar_factura"}
    assert "texto de prueba" in llamada["messages"][0]["content"]


def test_respuesta_cortada_por_max_tokens():
    assert codigo_del_error(ClienteSimulado(stop_reason="max_tokens")) == "respuesta_cortada"


def test_respuesta_sin_herramienta():
    bloques = [SimpleNamespace(type="text", text="no sé")]
    assert codigo_del_error(ClienteSimulado(bloques=bloques)) == "sin_respuesta"


def test_datos_con_formato_invalido():
    assert codigo_del_error(ClienteSimulado({"total": "mucho dinero"})) == "datos_invalidos"


def test_sin_conexion_con_el_servicio():
    peticion = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    error = anthropic.APIConnectionError(request=peticion)
    assert codigo_del_error(ClienteSimulado(error=error)) == "servicio_no_disponible"


def test_el_servicio_responde_con_error():
    peticion = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    respuesta = httpx.Response(429, request=peticion)
    error = anthropic.RateLimitError("demasiadas peticiones", response=respuesta, body=None)
    assert codigo_del_error(ClienteSimulado(error=error)) == "servicio_no_disponible"