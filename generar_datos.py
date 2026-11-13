import json
import random
from datetime import date
from pathlib import Path

from faker import Faker

from modelos import Factura, LineaIVA
from validacion import comprobar_coherencia

fake = Faker("es_ES")
Faker.seed(42)
random.seed(42)

FORMATOS = {"A": 12, "B": 12, "C": 12}
TIPOS_IVA = [4, 10, 21]


def crear_factura(numero: int, formato: str) -> Factura:
    fecha = fake.date_between(start_date=date(2025, 1, 1), end_date=date(2026, 10, 31))

    if formato == "C":
        tipos = random.sample(TIPOS_IVA, k=random.choice([2, 3]))
    else:
        tipos = [random.choice(TIPOS_IVA)]

    desglose = []
    for tipo in sorted(tipos):
        base = round(random.uniform(20, 1500), 2)
        cuota = round(base * tipo / 100, 2)
        desglose.append(LineaIVA(base=base, porcentaje=tipo, cuota=cuota))

    base_total = round(sum(linea.base for linea in desglose), 2)
    iva_total = round(sum(linea.cuota for linea in desglose), 2)

    if formato == "A":
        numero_factura = f"{fecha.year}-{numero:04d}"
    elif formato == "B":
        numero_factura = f"018-{random.randint(1, 9999):04d}-{random.randint(100000, 999999)}"
    else:
        numero_factura = f"F/{fecha.year}/{numero:06d}"

    cliente_nombre = fake.name()
    if formato == "B":
        cliente_nombre = cliente_nombre.upper()

    cliente_nif = None if random.random() < 0.25 else random.choice([fake.nif, fake.cif])()

    return Factura(
        numero_factura=numero_factura,
        fecha_emision=fecha,
        emisor_nombre=fake.company(),
        emisor_nif=fake.cif(),
        cliente_nombre=cliente_nombre,
        cliente_nif=cliente_nif,
        base_imponible=base_total,
        iva_total=iva_total,
        total=round(base_total + iva_total, 2),
        desglose_iva=desglose,
    )


if __name__ == "__main__":
    registros = []
    numero = 0
    for formato, cantidad in FORMATOS.items():
        for _ in range(cantidad):
            numero += 1
            factura = crear_factura(numero, formato)
            assert not comprobar_coherencia(factura), f"Factura incoherente: {factura}"
            registros.append(
                {
                    "archivo": f"factura_{numero:02d}_{formato}.pdf",
                    "formato": formato,
                    "datos": factura.model_dump(mode="json"),
                }
            )

    Path("datos").mkdir(exist_ok=True)
    with open("datos/respuestas.json", "w", encoding="utf-8") as archivo:
        json.dump(registros, archivo, ensure_ascii=False, indent=2)

    print(f"Generadas {len(registros)} facturas")
    for formato in FORMATOS:
        ejemplo = next(r for r in registros if r["formato"] == formato)
        print(ejemplo["archivo"], ejemplo["datos"]["numero_factura"], ejemplo["datos"]["total"])