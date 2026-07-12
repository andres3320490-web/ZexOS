import subprocess
import sys
import os

# --- PARCHE DE COMPILACIÓN OBLIGATORIO ---
try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--only-binary=:all:", "pillow"])

import streamlit as st
import uuid

# Asegurar la importación del módulo local tasks.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tasks import pipeline_procesamiento_masivo

# --- INTERFAZ BASE ---
st.title("Opus Clip Clone")

url_video = st.text_input("URL del video:")
formato = st.selectbox("Formato:", ["9:16", "1:1"])
con_subtitulos = st.checkbox("Subtítulos", value=True)
color_sub_hex = st.color_picker("Color de subtítulos:", "#deff9a")
estilo_subtitulos = st.selectbox("Estilo:", ["hormozi", "estandar"])
diccionario_manual = st.text_input("Palabras clave adicionales:")

if st.button("Procesar"):
    if url_video:
        tarea_id = str(uuid.uuid4())[:8]
        
        with st.spinner("Procesando..."):
            resultado = pipeline_procesamiento_masivo(
                tarea_id=tarea_id,
                ruta_video_master="",
                formato=formato,
                con_subtitulos=con_subtitulos,
                color_sub_hex=color_sub_hex,
                estilo_subtitulos=estilo_subtitulos,
                url_remoto=url_video,
                diccionario_manual=diccionario_manual
            )
            
        if resultado["status"] == "success":
            st.success("¡Completado!")
            for clip in resultado["clips"]:
                st.write(f"**Clip:** {clip['archivo']} | **Score:** {clip['score']}")
                
                ruta_clip = os.path.join("storage", tarea_id, clip["archivo"])
                if os.path.exists(ruta_clip):
                    st.video(ruta_clip)
                    with open(ruta_clip, "rb") as f:
                        st.download_button(f"Descargar {clip['archivo']}", f, file_name=clip["archivo"])
        else:
            st.error(f"Error: {resultado['mensaje']}")
    else:
        st.warning("Introduce una URL.")
