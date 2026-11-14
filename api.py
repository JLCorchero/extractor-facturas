import os
import secrets
from io import BytesIO

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Security, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from errores import ErrorExtraccion
from extraer_factura import extraer_factura
from extraer_texto import extraer_texto
from validacion import comprobar_coherencia

load_dotenv()
CLAVE_API = os.getenv("CLAVE_API")
if not CLAVE_API:
    raise RuntimeError("Falta CLAVE_API en el archivo .env")

MAX_BYTES = 5_000_000
MAX_CARACTERES = 30_000

cabecera_clave = APIKeyHeader(name="X-API-Key", auto_error=False)


def comprobar_clave(clave: str | None = Security(cabecera_clave)):
    if clave is None or not secrets.compare_digest(clave.encode(), CLAVE_API.encode()):
        raise HTTPException(status_code=401, detail="Clave de API no válida")


app = FastAPI(title="Extractor de facturas")

ESTADO_HTTP = {
    "pdf_ilegible": 422,
    "pdf_protegido": 422,
    "sin_texto": 422,
    "respuesta_cortada": 502,
    "sin_respuesta": 502,
    "datos_invalidos": 502,
    "servicio_no_disponible": 503,
}


@app.exception_handler(ErrorExtraccion)
async def error_de_extraccion(peticion: Request, error: ErrorExtraccion):
    estado = ESTADO_HTTP.get(error.codigo, 500)
    return JSONResponse(status_code=estado, content={"detail": error.mensaje, "codigo": error.codigo})


@app.post("/extraer", dependencies=[Depends(comprobar_clave)])
def extraer(archivo: UploadFile):
    if archivo.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Solo se aceptan archivos PDF")

    contenido = archivo.file.read(MAX_BYTES + 1)
    if len(contenido) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="El PDF supera los 5 MB")

    texto = extraer_texto(BytesIO(contenido))
    if len(texto) > MAX_CARACTERES:
        raise HTTPException(status_code=422, detail="El documento es demasiado largo")

    factura, uso = extraer_factura(texto)
    avisos = comprobar_coherencia(factura)
    return {
        "factura": factura,
        "avisos": avisos,
        "revisar": bool(avisos),
        "tokens": {"entrada": uso.input_tokens, "salida": uso.output_tokens},
    }



@app.get("/salud")
def salud():
    return {"estado": "ok"}