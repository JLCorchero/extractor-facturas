import re
from datetime import date

from pydantic import BaseModel, field_validator


class LineaIVA(BaseModel):
    base: float | None = None
    porcentaje: float | None = None
    cuota: float | None = None


class Factura(BaseModel):
    numero_factura: str | None = None
    fecha_emision: date | None = None
    emisor_nombre: str | None = None
    emisor_nif: str | None = None
    cliente_nombre: str | None = None
    cliente_nif: str | None = None
    base_imponible: float | None = None
    iva_total: float | None = None
    total: float | None = None
    desglose_iva: list[LineaIVA] = []

    @field_validator("emisor_nif", "cliente_nif")
    @classmethod
    def limpiar_nif(cls, valor):
        if valor is None:
            return None
        return re.sub(r"[^A-Za-z0-9]", "", valor).upper() or None