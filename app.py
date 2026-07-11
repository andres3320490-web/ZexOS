import os
import shutil
import uuid
import time
import requests
import numpy as np
import cv2
import torch
import yt_dlp
import urllib.request
import streamlit as st
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

# Importamos directamente la función sin APIs ni puertos intermedios
try:
    from tasks import async_render_worker, garantizar_entorno_tarea
except ImportError:
    st.error("❌ No se encontró el archivo 'tasks.py' en el repositorio.")
    st.stop()

# =========================================================================
# 🎨 FRONTEND DE STREAMLIT
# =========================================================================
st.markdown("""
    <style>
    .stApp { background-color: #07090e; color: #E2E8F0; }
    h1, h2, h3, .stMarkdown strong { color: #deff9a !important; font-family: 'Inter', sans-serif; }
    .clip-card { background: #111625; border: 1px solid #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
    .stButton>button { width: 100%; background: #deff9a !important; color: #07090e !important; font-weight: bold !important; border-radius: 8px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ ZexOS AI Studio Enterprise")
email_usuario = st.text_input("Correo electrónico corporativo:", placeholder="ejemplo@correo.com").strip()

if not email_usuario:
    st.info("💡 Introduce tu correo para desplegar tu espacio de trabajo.")
    st.stop()

formato_seleccionado = st.sidebar.selectbox("Relación de Aspecto Target", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
con_subtitulos = st.sidebar.checkbox("Subtítulos Dinámicos Inteligentes", value=True)
estilo_elegido = st.sidebar.selectbox("Plantilla Tipográfica", options=["hormozi", "classic_three", "minimal"]) if con_subtitulos else "hormozi"
diccionario_manual = st.sidebar.text_area("Ganchos prioritarios:", placeholder="VTuber, épico", height=80)

col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("📥 Carga de Material Audiovisual")
    url_remoto = st.text_input("🔗 Enlace Directo:", placeholder="https://...").strip()
    video_subido = st.file_uploader("O sube tu archivo local aquí:", type=["mp4", "mkv"])
    boton_procesar = st.button("🚀 INICIAR PROCESAMIENTO HÍBRIDO")

with col_der:
    st.subheader("📊 Monitorización de Clips y Descarga")
    
    if boton_procesar:
        tarea_id = f"job_{uuid.uuid4().hex[:10]}"
        st.session_state.tarea_id = tarea_id
        
        # Crear entorno local de almacenamiento seguro
        temp_dir = garantizar_entorno_tarea(tarea_id)
        ruta_input = ""
        
        if video_subido:
            ruta_input = os.path.join(temp_dir, video_subido.name)
            with open(ruta_input, "wb") as buffer:
                buffer.write(video_subido.getvalue())
        
        # Renderizado síncrono controlado visualmente por st.status
        with st.status("Procesando video con Inteligencia Artificial...", expanded=True) as status:
            st.write("⏳ Analizando rostros y aplicando tracking facial adaptativo...")
            
            # Ejecución directa del pipeline sin pasar por hilos de red bloqueados
            resultado = async_render_worker(
                tarea_id=tarea_id, 
                ruta_video_master=ruta_input, 
                formato=formato_seleccionado, 
                con_subtitulos=con_subtitulos, 
                color_sub_hex="#deff9a", 
                estilo_subtitulos=estilo_elegido, 
                url_remoto=url_remoto, 
                diccionario_manual=diccionario_manual
            )
            
            if resultado.get("status") == "success":
                status.update(label="⚡ ¡Procesamiento Completado con Éxito!", state="complete", expanded=False)
                st.session_state.resultado_tarea = resultado
            else:
                status.update(label="❌ El proceso ha fallado", state="error")
                st.error(f"Detalle: {resultado.get('mensaje')}")

    # Despliegue de resultados estables en sesión
    if "resultado_tarea" in st.session_state and "tarea_id" in st.session_state:
        res = st.session_state.resultado_tarea
        tid = st.session_state.tarea_id
        
        st.success("¡Tus clips ya están listos!")
        total_clips = res.get("total_clips", 1)
        opciones_clips = [f"🔥 Short # {i+1}" for i in range(total_clips)]
        clip_elegido = st.selectbox("Selecciona fragmento:", options=opciones_clips)
        indice_clip = opciones_clips.index(clip_elegido) + 1
        
        dir_tarea = os.path.join("storage", tid)
        if os.path.exists(dir_tarea):
            archivos = [f for f in os.listdir(dir_tarea) if f.startswith(f"clip_{indice_clip}_")]
            if archivos:
                ruta_clip_final = os.path.join(dir_tarea, archivos[0])
                with open(ruta_clip_final, "rb") as video_file:
                    st.video(video_file.read())
                    
                # Botón nativo de descarga
                with open(ruta_clip_final, "rb") as vf:
                    st.download_button(
                        label="📥 Descargar Clip en Alta Definición",
                        data=vf,
                        file_name=archivos[0],
                        mime="video/mp4"
                    )
