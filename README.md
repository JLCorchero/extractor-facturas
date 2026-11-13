# Extractor de facturas con IA

Herramienta que lee facturas en PDF, de formatos muy distintos, y devuelve sus datos estructurados (número, fecha, emisor, cliente, NIF, bases, IVA y total), con una validación que detecta cuándo hay que revisar a mano.

## Por qué existe

[Tu motivación: por qué facturas, qué problema real resuelve.]

## Cómo funciona

1. **PDF a texto** con `pypdf` (modo layout, que conserva las columnas).
2. **Extracción con Claude Haiku 5.5**, forzando una salida estructurada con un esquema Pydantic.
3. **Validación** de los datos extraídos: coherencia aritmética (bases, cuotas y total), campos obligatorios y dígito de control de los NIF/CIF.
4. **Evaluación** automática contra respuestas conocidas, para medir cada cambio.

## Resultados

Evaluado con 36 facturas sintéticas de tres formatos (A: simple, B: ticket de tienda, C: factura densa con varios tipos de IVA y descuentos).

| Versión | Facturas perfectas | Coste por factura | Tiempo medio |
|---|---|---|---|
| v1 (prompt inicial) | 35/36 | 0,00042 $ | 1,8 s |
| v2 (regla del NIF del cliente + validación de NIF) | 36/36 | 0,00043$ | 2,0 s |

### Prueba con una factura real

Factura de un mayorista (formato denso: varias fechas con hora, números de pedido y de cliente que pueden confundirse, tres tipos de IVA). Los datos personales de la copia usada son ficticios.

| Campo | Resultado |
|---|---|
| Número de factura | Correcto (ignoró los demás códigos del documento) |
| Fecha de emisión | Correcta (eligió la fecha de venta entre varias) |
| Emisor y NIF | Correctos |
| Cliente y NIF | Copiados tal como figuran en el documento |
| Base, IVA y total | Correctos (163,34 + 19,45 = 182,79) |
| Desglose de IVA | Las 3 líneas correctas (10 %, 21 % y 4 %) |

- **Coherencia aritmética:** las bases, las cuotas y el total cuadran entre sí.
- **Validación:** un único aviso. El NIF del cliente impreso en el documento no tiene un dígito de control válido, así que la factura se marcaría para revisión humana. El extractor lo copió fielmente y la validación lo detectó.
- **Coste:** 3.808 tokens de entrada y 414 de salida, unos 0,0006 $ por factura.

Es una sola factura de un solo proveedor, así que este resultado no demuestra el rendimiento sobre facturas reales en general. Ampliar la muestra es el siguiente paso.

**Qué falló y qué aprendí:** [El fallo del caso 19: el modelo devolvió `None` en un NIF que sí estaba en el texto, sin marcador de cliente. Cómo lo diagnostiqué y cómo lo corregí.]

**Límites honestos:** las facturas de prueba son sintéticas, generadas por mí a partir de dos facturas reales, así que el resultado no demuestra el rendimiento sobre facturas reales. [Añade aquí lo que midas con facturas reales.]

## Privacidad

Las facturas reales nunca se suben al repositorio ni a la API sin anonimizar. Tapar datos con un recuadro negro no basta, porque el texto sigue en el PDF; por eso el repositorio solo contiene facturas sintéticas.

## Cómo ejecutarlo

```bash
git clone git@github.com:JLCorchero/extractor-facturas.git
cd extractor-facturas
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # añade tu ANTHROPIC_API_KEY
python generar_datos.py && python generar_pdfs.py
python evaluar.py
```

## Limitaciones conocidas

- La validación de NIF no cubre empresas extranjeras ni NIF-IVA intracomunitarios.
- Solo trabaja con PDF con capa de texto; los escaneados necesitarían OCR.
- [Tus propias limitaciones.]

## Próximos pasos

API con FastAPI, interfaz con Streamlit y despliegue. [Lo que decidas.]