Extractor de facturas con IA

Le das una factura en PDF y te devuelve sus datos ordenados: número, fecha, emisor y su NIF, cliente y su NIF, base imponible, IVA, total y el desglose de IVA por tipo. Además revisa su propio resultado y te avisa cuando conviene que una persona lo mire.

Lo he construido justo después de terminar un curso de Python desde cero. Es uno de mis proyectos de portfolio para trabajar como Product Manager o Ingeniero de IA, y aquí cuento qué hice, qué medí y en qué me equivoqué.

[Por qué facturas: escribe en 2-3 frases qué te llevó a este problema. Por ejemplo, si lo has vivido de cerca, a quién le ahorraría tiempo y qué se hace hoy a mano.]

Demo: [URL de la demo cuando esté desplegada]

[GIF corto: subir un PDF en la web y ver los datos extraídos y el aviso de "revisar"]

Cómo funciona
PDF a texto. Uso pypdf en modo layout, que conserva las columnas. En facturas con tablas eso importa mucho.
Extracción con Claude Haiku 5.5 (claude-haiku-5-5). Obligo al modelo a responder con una herramienta (tool use obligatorio) que sigue un esquema Pydantic. Así siempre recibo los mismos campos con el mismo formato.
Validación sin conocer la respuesta. El sistema no sabe cuál es el resultado correcto, pero sí puede comprobar si tiene sentido:
que las bases del desglose sumen la base imponible y las cuotas sumen el IVA;
que cada cuota sea base x porcentaje y que base + IVA = total;
que estén los campos obligatorios (número, fecha, total, NIF del emisor);
que el dígito de control de los NIF, CIF y NIE españoles sea válido.
Si salta cualquier aviso, la factura sale marcada como "revisar".
API con FastAPI (POST /extraer). Pide una clave en la cabecera X-API-Key y limita cada PDF a 5 MB y a 30.000 caracteres de texto, para que nadie me dispare el gasto.
Interfaz web con Streamlit, que llama a esa API por HTTP con httpx.
Evaluación automática contra respuestas conocidas. Guardo las predicciones en caché, y la caché se invalida con una huella (hash) del modelo + prompt + esquema: si cambia cualquiera de los tres, se vuelve a ejecutar.
Cómo lo he medido

No tenía un montón de facturas reales que pudiera usar, así que las generé. Tomé dos facturas reales como modelo y escribí código (Faker + fpdf2, con semilla fija) que crea 36 facturas sintéticas en tres formatos, 12 de cada uno:

A: factura sencilla.
B: ticket de tienda con datos que despistan: números de ticket, de pedido y de tarjeta, una fecha larga en la cabecera y un anticipo escrito con punto decimal.
C: factura densa en letra monoespaciada, con 2 o 3 tipos de IVA, tres fechas con hora, descuentos con el signo menos detrás, una fila de totales sin etiqueta y cifras que distraen.

El mismo código que crea cada PDF genera su respuesta correcta. Comparo 10 campos por factura: los importes con un céntimo de tolerancia, los nombres sin distinguir tildes ni mayúsculas, el resto de forma exacta, y el desglose de IVA ordenado por porcentaje.

Resultados
Versión	Pasadas por factura	Ejecuciones perfectas	Coste por ejecución	Tiempo medio
v1	1	35 de 36	0,00042 $	1,8 s
v2 (regla nueva para el NIF del cliente)	1	36 de 36	0,00043 $	[completar]
v3 (prompt corregido tras la regresión)	3	108 de 108	0,00044 $	1,9 s

En la v3 las 108 ejecuciones salieron bien en los tres formatos, sin fallos intermitentes ni fallos fijos. La evaluación completa costó 0,048 $.

Ese 100 % hay que leerlo con cuidado: las facturas las he generado yo. Demuestra que el sistema funciona y no se rompe con los casos que diseñé, no que acierte con cualquier factura real.

Lo que me salió mal
El NIF que el modelo no veía

En la v1 falló una sola factura, el ticket factura_19_B. El modelo devolvió null en el NIF del cliente. El NIF estaba en el texto, pero como un "Numero NIF" suelto, sin ninguna etiqueta que dijera que era del cliente, y el emisor ya estaba identificado.

Lo que me preocupó fue que era un fallo silencioso. Las cuentas cuadraban, así que la validación aritmética no tenía forma de detectarlo. Solo lo vi porque comparaba contra la respuesta correcta. Lo arreglé con una regla en el prompt y la v2 sacó 36 de 36.

La regresión que no cazó la evaluación

Más tarde, editando el prompt, uní por error dos líneas y dejé una frase cortada. A partir de ahí, la factura factura_25_C empezó a devolver como base imponible la base de la primera línea de IVA (738,41) en lugar de la suma de todas las bases (1.170,56). Pasó en 5 de 5 intentos, tanto desde la web como por script.

Lo detectaron dos cosas: la validación aritmética, porque las bases del desglose ya no sumaban la base imponible, y mi propia prueba a mano en la web. La evaluación automática no lo vio, porque la había ejecutado antes de ese cambio. La huella de modelo + prompt + esquema sí delató que algo había cambiado respecto a lo que estaba en caché.

Qué cambié:

Completé la frase y reforcé las reglas de base_imponible (es la suma de todas las bases, suele estar en la fila de totales y a veces no lleva etiqueta) y de iva_total.
Ahora la evaluación hace varias pasadas por factura. El modelo no responde siempre igual, y con una sola pasada no se distingue un fallo que aparece a veces de uno que aparece siempre.
Y la lección principal: ejecutar la evaluación después de cada cambio en el prompt, por pequeño que parezca.
Prueba con una factura real

Probé también con una factura real de un mayorista: formato denso, IVA mixto (10 %, 21 % y 4 %), varias fechas con hora y códigos que despistan. Los datos personales de la copia que usé son ficticios.

Qué	Resultado
Campos extraídos	Todos correctos
Desglose de IVA	Completo
Base imponible	163,34
IVA	19,45
Total	182,79
Avisos de la validación	1: el NIF del cliente (ficticio) no tiene un dígito de control válido
Coste	Unos 0,0006 $

La probé varias veces, también después de corregir el prompt. El aviso es correcto: el NIF impreso en esa copia no es válido, así que en un uso real esa factura iría a revisión humana, que es justo lo que quiero que pase.

Es una sola factura de un solo proveedor. Me sirve como señal, no como prueba.

Seguridad y privacidad
La API exige una clave (X-API-Key) y limita el tamaño del PDF y del texto para controlar el gasto.
Nunca he subido facturas reales sin anonimizar ni al repositorio ni a la API. Aquí solo hay facturas sintéticas.
Algo que aprendí por el camino: tapar datos con recuadros negros en un PDF no basta, porque el texto sigue dentro del archivo.
Cómo ejecutarlo

Necesitas Python 3.11 y una clave de la API de Anthropic.

bash
git clone https://github.com/JLCorchero/extractor-facturas.git
cd extractor-facturas
pip install -r requirements.txt
cp .env.example .env   # rellena ANTHROPIC_API_KEY y CLAVE_API

Arranca la API y, en otra terminal, la web:

bash
uvicorn api:app --reload
bash
python -m streamlit run app_web.py

Para lanzar la evaluación (el número indica cuántas veces se procesa cada factura):

bash
python evaluar.py 3
Qué hay en cada archivo
Archivo	Para qué sirve
modelos.py	Esquema Pydantic de la factura
extraer_texto.py	PDF a texto con pypdf
extraer_factura.py	Llamada a Claude con salida estructurada
validacion.py	Comprobaciones aritméticas, campos obligatorios y NIF
api.py	API con FastAPI
app_web.py	Interfaz con Streamlit
evaluar.py	Evaluación contra las respuestas correctas
generar_datos.py, generar_pdfs.py	Generación de las facturas sintéticas y sus respuestas
probar_real.py	Procesa un PDF concreto desde la terminal y muestra el JSON extraído, los avisos de la validación y los tokens gastados
datos/	Respuestas esperadas e informes de evaluación
facturas/	Los 36 PDF sintéticos

Una nota por si te pasa lo mismo: en mi Mac con macOS Big Sur no pude instalar la última versión de pyarrow, y st.dataframe de Streamlit cerraba el proceso. Por eso el desglose de IVA se muestra con una tabla Markdown construida a mano.

Limitaciones
Las 36 facturas de la evaluación son sintéticas y las he generado yo. No miden el rendimiento con facturas reales en general.
Solo lo he probado con una factura real, de un único proveedor.
El modelo no responde siempre igual. Por eso evalúo con varias pasadas, pero eso reduce el riesgo, no lo elimina.
Solo funciona con PDF que tengan capa de texto. Para facturas escaneadas haría falta OCR.
La validación de NIF no cubre empresas extranjeras ni NIF-IVA intracomunitarios.
Todavía no hay una demo pública desplegada.
Próximos pasos
Desplegar la demo y añadir aquí la URL y el GIF.
Probar con más facturas reales, de proveedores distintos y bien anonimizadas.
[Añade aquí 1-2 pasos más que tengas pensados, por ejemplo OCR para escaneados o validación de NIF extranjeros.]