import subprocess
import sys
import os

# --- PARCHE INTERNO CONTRA ERRORES (Invisible en la página) ---
try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--only-binary=:all:", "pillow"])

import streamlit as st
import uuid

# Asegurar rutas locales del servidor
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tasks import garantizar_entorno_tarea, pipeline_procesamiento_masivo

# --- TU CONFIGURACIÓN Y ESTILO ORIGINAL ---
st.set_page_config(page_title="Opus Clip Clone", page_icon="✂️", layout="centered")

st.title("✂️ Opus Clip Clone")
st.markdown("### Genera tus clips virales en segundos")

# Estructura e inputs tal cual los tenías
url_video = st.text_input("Introduce la URL del video largo:")
formato = st.selectbox("Formato de salida:", ["9:16", "1:1"])
con_subtitulos = st.checkbox("¿Incluir subtítulos?", value=True)
color_sub_hex = st.color_picker("Color de los subtítulos destacados:", "#deff9a")
estilo_subtitulos = st.selectbox("Estilo:", ["hormozi", "estandar"])
diccionario_manual = st.text_input("Ganchos o palabras clave adicionales (opcional):")

if st.button("Procesar Video"):
    if url_video:
        tarea_id = str(uuid.uuid4())
        
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
            st.success("¡Completado con éxito!")
            for clip in resultado["clips"]:
                st.write(f"**Clip:** {clip['archivo']} - **Score:** {clip['score']}")
                for rep in clip["reporte"]:
                    st.write(f"- {rep}")
                
                ruta_clip = os.path.join("storage", tarea_id, clip["archivo"])
                if os.path.exists(ruta_clip):
                    st.video(ruta_clip)
                    with open(ruta_clip, "rb") as f:
                        st.download_button(f"Descargar {clip['archivo']}", f, file_name=clip["archivo"])
        else:
            st.error(f"Error: {resultado['mensaje']}")
    else:
        st.warning("Por favor introduce una URL.")
