import subprocess
import sys
import os

# --- PARCHE DE CONTINGENCIA ANTIBLOQUEOS ---
# Fuerza la instalación del binario precompilado de Pillow antes de arrancar todo lo demás
try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--only-binary=:all:", "pillow"])

import streamlit as st
import uuid

# Asegurar que Streamlit encuentre los módulos locales en su ruta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tasks import garantizar_entorno_tarea, pipeline_procesamiento_masivo

st.set_page_config(page_title="Clon de Opus Clip", page_icon="✂️", layout="wide")

st.title("✂️ Clon de Opus Clip - Creador de Shorts")
st.subheader("Corta tus videos largos y conviértelos en clips virales con subtítulos automáticos")

# Crear directorios base si no existen
os.makedirs("storage", exist_ok=True)

# Formulario de entrada
with st.form("formulario_opus"):
    url_video = st.text_input("🔗 URL del video (YouTube o enlace directo mp4):", placeholder="https://www.youtube.com/watch?v=...")
    
    col1, col2 = st.columns(2)
    with col1:
        formato = st.selectbox("📐 Formato del Short:", ["9:16 (Vertical para TikTok/Reels)", "1:1 (Cuadrado)"])
    with col2:
        estilo_sub = st.selectbox("🎨 Estilo de Subtítulos:", ["Hormozi (Grande y Llamativo)", "Estándar (Limpio)"])
        
    color_sub = st.color_picker("🎨 Color de palabras clave:", "#deff9a")
    diccionario_extra = st.text_input("🔑 Palabras clave adicionales (separadas por coma):", placeholder="ganancia, brutal, hack")
    
    boton_procesar = st.form_submit_button("🚀 Generar Clips Virales")

if boton_procesar:
    if not url_video.strip():
        st.error("Por favor, introduce una URL válida.")
    else:
        id_tarea = str(uuid.uuid4())[:8]
        
        with st.spinner("🔄 Procesando video, analizando rostros y generando subtítulos... (Esto puede tardar un momento)"):
            resultado = pipeline_procesamiento_masivo(
                tarea_id=id_tarea,
                ruta_video_master="",
                formato=formato,
                con_subtitulos=True,
                color_sub_hex=color_sub,
                estilo_subtitulos="hormozi" if "Hormozi" in estilo_sub else "estandar",
                url_remoto=url_video,
                diccionario_manual=diccionario_extra
            )
            
        if resultado["status"] == "success":
            st.success("✨ ¡Clips generados con éxito!")
            
            for clip in resultado["clips"]:
                ruta_descarga = os.path.join("storage", id_tarea, clip["archivo"])
                
                with st.container():
                    st.write("---")
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric(label="Viral Score", value=clip["score"])
                        st.subheader("Análisis del Clip:")
                        for r in clip["reporte"]:
                            st.write(r)
                            
                        if os.path.exists(ruta_descarga):
                            with open(ruta_descarga, "rb") as file:
                                st.download_button(
                                    label=f"📥 Descargar {clip['archivo']}",
                                    data=file,
                                    file_name=clip["archivo"],
                                    mime="video/mp4"
                                )
                    with c2:
                        if os.path.exists(ruta_descarga):
                            st.video(ruta_descarga)
                        else:
                            st.error("El archivo del clip no se pudo localizar.")
        else:
            st.error(f"Ocurrió un error en el procesamiento: {resultado['mensaje']}")
