from datetime import date
from pydantic import BaseModel


class Factura(BaseModel): 
    numero_factura: str | None = None
    fecha_emision: date | None = None
    emisor_nombre: str | None = None
    emisor_nif: str | None = None
    cliente_nombre: str | None = None
    base_imponible: float | None = None
    iva_porcentaje: float | None = None
    total: float | None = None