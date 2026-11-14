import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
URL_API = os.getenv("URL_API", "http://127.0.0.1:8000")
CLAVE_API = os.getenv("CLAVE_API", "")

st.set_page_config(page_title="Extractor de facturas", page_icon="🧾")
st.title("Extractor de facturas")
st.caption("Sube una factura en PDF y obtén sus datos estructurados. No subas facturas con datos reales de terceros.")

archivo = st.file_uploader("Factura en PDF", type="pdf")

if archivo is not None:
    with st.spinner("Leyendo la factura..."):
        try:
            respuesta = httpx.post(
                f"{URL_API}/extraer",
                headers={"X-API-Key": CLAVE_API},
                files={"archivo": (archivo.name, archivo.getvalue(), "application/pdf")},
                timeout=60,
            )
        except httpx.ConnectError:
            st.error("No se puede conectar con la API. ¿Está arrancada?")
            st.stop()

    if respuesta.status_code != 200:
        try:
            detalle = respuesta.json().get("detail", respuesta.text)
        except ValueError:
            detalle = respuesta.text
        st.error(f"La API respondió con un error ({respuesta.status_code}): {detalle}")
        st.stop()

    datos = respuesta.json()
    factura = datos["factura"]

    if datos["revisar"]:
        st.warning("Revisión recomendada")
        for aviso in datos["avisos"]:
            st.write(f"- {aviso}")
    else:
        st.success("Datos coherentes")

    st.subheader("Datos extraídos")
    st.json(factura)

    if factura["desglose_iva"]:
        st.subheader("Desglose de IVA")

        def fmt(valor):
            return "-" if valor is None else f"{valor:g}"

        filas = ["| Base | IVA % | Cuota |", "|---:|---:|---:|"]
        for linea in factura["desglose_iva"]:
            filas.append(f"| {fmt(linea['base'])} | {fmt(linea['porcentaje'])} | {fmt(linea['cuota'])} |")
        st.markdown("\n".join(filas))