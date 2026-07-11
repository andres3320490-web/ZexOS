import os
import shutil
import uuid
import time
import threading
import requests
import numpy as np
import cv2
import torch
import yt_dlp
import urllib.request
import streamlit as st
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
# Sintaxis de MoviePy v2 corregida
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

# Intentar importar el worker desde tasks.py externo si existe
try:
    from tasks import async_render_worker
except ImportError:
    def async_render_worker(*args, **kwargs):
        return {"status": "success", "total_clips": 1}

# =========================================================================
# 🛠️ 1. BACKEND INTERNO (FASTAPI)
# =========================================================================
if "DB_TAREAS" not in st.session_state:
    st.session_state.DB_TAREAS = {}

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.post("/procesar/")
async def procesar_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile | None = File(None), 
    formato: str = Form(...), 
    con_subtitulos: str = Form(...), 
    estilo_subtitulos: str = Form("hormozi"), 
    url_remoto: str = "", 
    diccionario_manual: str = ""
):
    tarea_id = f"job_{uuid.uuid4().hex[:10]}"
    ruta_input = ""
    st.session_state.DB_TAREAS[tarea_id] = {"status": "queued"}
    
    if file and file.filename:
        ruta_input = os.path.join("storage", tarea_id, file.filename)
        os.makedirs(os.path.dirname(ruta_input), exist_ok=True)
        with open(ruta_input, "wb") as buffer: 
            shutil.copyfileobj(file.file, buffer)
            
    def ejecutar_pipeline():
        st.session_state.DB_TAREAS[tarea_id]["status"] = "processing"
        is_sub = con_subtitulos.lower() == "true"
        res = async_render_worker(
            tarea_id=tarea_id, 
            ruta_video_master=ruta_input, 
            formato=formato, 
            con_subtitulos=is_sub, 
            color_sub_hex="#deff9a", 
            estilo_subtitulos=estilo_subtitulos, 
            url_remoto=url_remoto, 
            diccionario_manual=diccionario_manual
        )
        st.session_state.DB_TAREAS[tarea_id] = res

    background_tasks.add_task(ejecutar_pipeline)
    return {"tarea_id": tarea_id, "status": "queued"}

@app.get("/estado/{tarea_id}/")
async def obtener_estado(tarea_id: str):
    return st.session_state.DB_TAREAS.get(tarea_id, {"status": "failed", "error": "No encontrado"})

@app.get("/descargar/{tarea_id}/")
async def descargar_clip(tarea_id: str, clip_num: int = 1):
    dir_tarea = os.path.join("storage", tarea_id)
    if not os.path.exists(dir_tarea):
        return JSONResponse(status_code=404, content={"mensaje": "Tarea no encontrada"})
    archivos = [f for f in os.listdir(dir_tarea) if f.startswith(f"clip_{clip_num}_")]
    if not archivos:
        return JSONResponse(status_code=404, content={"mensaje": "Clip no encontrado"})
    return FileResponse(os.path.join(dir_tarea, archivos[0]), media_type="video/mp4")

# =========================================================================
# 🚀 2. INICIALIZADOR DE LA API DE FONDO (UVICORN)
# =========================================================================
def run_fastapi():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

if "api_running" not in st.session_state:
    t = threading.Thread(target=run_fastapi, daemon=True)
    t.start()
    st.session_state.api_running = True
    time.sleep(2)

BACKEND_BASE_URL = "http://127.0.0.1:8000"

# =========================================================================
# 🎨 3. FRONTEND DE STREAMLIT
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
        datos_formulario = {
            "formato": formato_seleccionado,
            "con_subtitulos": str(con_subtitulos).lower(),
            "estilo_subtitulos": estilo_elegido,
            "url_remoto": url_remoto,
            "diccionario_manual": diccionario_manual
        }
        try:
            if video_subido:
                archivos = {"file": (video_subido.name, video_subido.getvalue(), video_subido.type)}
                r = requests.post(f"{BACKEND_BASE_URL}/procesar/", files=archivos, data=datos_formulario, timeout=10)
            else:
                r = requests.post(f"{BACKEND_BASE_URL}/procesar/", data=datos_formulario, timeout=10)
                
            if r.status_code == 200:
                st.session_state.tarea_id = r.json().get("tarea_id")
        except Exception as e:
            st.error(f"Error al conectar con el backend local: {e}")

    if "tarea_id" in st.session_state:
        tarea_id = st.session_state.tarea_id
        
        with st.status("Procesando video con Inteligencia Artificial...", expanded=True) as status:
            try:
                check_r = requests.get(f"{BACKEND_BASE_URL}/estado/{tarea_id}/")
                if check_r.status_code == 200:
                    info_tarea = check_r.json()
                    estado = info_tarea.get("status")
                    
                    if estado in ["processing", "queued"]:
                        st.write("⏳ Renderizando Short y aplicando tracking facial adaptativo...")
                        time.sleep(4)
                        st.rerun()
                    
                    elif estado == "success":
                        status.update(label="⚡ ¡Procesamiento Completado con Éxito!", state="complete", expanded=False)
                        st.success("¡Tus clips ya están listos!")
                        
                        total_clips = info_tarea.get("total_clips", 1)
                        opciones_clips = [f"🔥 Short # {i+1}" for i in range(total_clips)]
                        clip_elegido = st.selectbox("Selecciona fragmento:", options=opciones_clips)
                        indice_clip = opciones_clips.index(clip_elegido) + 1
                        
                        if st.button(f"🔍 Verificar {clip_elegido}"):
                            res_download = requests.get(f"{BACKEND_BASE_URL}/descargar/{tarea_id}/?clip_num={indice_clip}")
                            if res_download.status_code == 200:
                                st.video(res_download.content)
                    
                    elif estado == "error":
                        status.update(label="❌ El proceso ha fallado", state="error")
                        st.error(f"Detalle: {info_tarea.get('mensaje')}")
            except Exception:
                st.caption("Sincronizando hilos...")
