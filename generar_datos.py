import json
import random
from datetime import date
from pathlib import Path

from faker import Faker

from modelos import Factura

fake = Faker("es_ES")
Faker.seed(42)
random.seed(42)


def crear_factura(numero: int) -> Factura:
    base = round(random.uniform(50, 5000), 2)
    iva = random.choice([4, 10, 21])
    total = round(base * (1 + iva / 100), 2)
    fecha = fake.date_between(start_date=date(2025, 1, 1), end_date=date(2026, 10, 31))
    return Factura(
        numero_factura=f"{fecha.year}-{numero:04d}",
        fecha_emision=fecha,
        emisor_nombre=fake.company(),
        emisor_nif=fake.cif(),
        cliente_nombre=fake.name(),
        base_imponible=base,
        iva_porcentaje=iva,
        total=total,
    )

if __name__ == "__main__":
    facturas = [crear_factura(n) for n in range(1, 31)]
    Path("datos").mkdir(exist_ok=True)
    salida = [f.model_dump(mode="json") for f in facturas]
    with open("datos/respuestas.json", "w", encoding="utf-8") as archivo:
        json.dump(salida, archivo, ensure_ascii=False, indent=2)
    print(f"Generadas {len(facturas)} facturas")
    print(facturas[0])
