from io import BytesIO

from fastapi import FastAPI, HTTPException, UploadFile

from extraer_factura import extraer_factura
from extraer_texto import extraer_texto
from validacion import comprobar_coherencia

app = FastAPI(title="Extractor de facturas")


@app.post("/extraer")
def extraer(archivo: UploadFile):
    if archivo.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Solo se aceptan archivos PDF")

    texto = extraer_texto(BytesIO(archivo.file.read()))
    if not texto.strip():
        raise HTTPException(status_code=422, detail="El PDF no tiene texto (¿está escaneado?)")

    factura, uso = extraer_factura(texto)
    avisos = comprobar_coherencia(factura)
    return {
        "factura": factura,
        "avisos": avisos,
        "revisar": bool(avisos),
        "tokens": {"entrada": uso.input_tokens, "salida": uso.output_tokens},
    }