import os
import uuid
import streamlit as st
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

# Importación del backend modularizado
from tasks import garantizar_entorno_tarea, async_render_worker

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.sidebar.error(f"Error Supabase: {e}")

cookie_controller = CookieController()

st.markdown("""
    <style>
    .stApp { background-color: #07090e; color: #E2E8F0; }
    h1, h2, h3, .stMarkdown strong { color: #deff9a !important; font-family: 'Inter', sans-serif; }
    .stButton>button { width: 100%; background: #deff9a !important; color: #07090e !important; font-weight: bold !important; border-radius: 8px !important; }
    .report-box { background-color: #111827; padding: 15px; border-radius: 8px; border-left: 4px solid #deff9a; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ ZexOS AI Studio Pro (Clon 110% Opus)")

saved_email = cookie_controller.get("zexos_user_email")
email_usuario = st.text_input("Correo electrónico corporativo:", value=saved_email if saved_email else "", placeholder="ejemplo@correo.com").strip()

if not email_usuario:
    st.info("💡 Introduce tu correo para desplegar tu espacio de trabajo corporativo.")
    st.stop()

cookie_controller.set("zexos_user_email", email_usuario)

# Parámetros avanzados del Sidebar
st.sidebar.subheader("🔒 Configuración del Short")
formato_seleccionado = st.sidebar.selectbox("Relación de Aspecto Target", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
con_subtitulos = st.sidebar.checkbox("Subtítulos Dinámicos Inteligentes", value=True)
stilo_elegido = st.sidebar.selectbox("Plantilla Tipográfica", options=["hormozi", "classic_three"])
diccionario_manual = st.sidebar.text_area("Palabras clave extra:", placeholder="brutal, éxito", height=80)

col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("📥 Material Audiovisual")
    url_remoto = st.text_input("🔗 Enlace del Video (YouTube / Redes):", placeholder="https://...").strip()
    video_subido = st.file_uploader("O sube un archivo local:", type=["mp4", "mkv"])
    boton_procesar = st.button("🚀 GENERAR SHORT ULTRA-VIRAL")

with col_der:
    st.subheader("📊 Consola de Resultados Inteligente")
    
    if boton_procesar:
        tarea_id = f"job_{uuid.uuid4().hex[:10]}"
        st.session_state.tarea_id = tarea_id
        
        temp_dir = garantizar_entorno_tarea(tarea_id)
        ruta_input = ""
        
        if video_subido:
            ruta_input = os.path.join(temp_dir, video_subido.name)
            with open(ruta_input, "wb") as buffer:
                buffer.write(video_subido.getvalue())
        
        with st.status("Ejecutando análisis semántico y tracking cinemático...", expanded=True) as status:
            resultado = async_render_worker(
                tarea_id=tarea_id, 
                ruta_video_master=ruta_input, 
                formato=formato_seleccionado, 
                con_subtitulos=con_subtitulos, 
                color_sub_hex="#deff9a", 
                estilo_subtitulos=stilo_elegido, 
                url_remoto=url_remoto, 
                diccionario_manual=diccionario_manual
            )
            
            if resultado.get("status") == "success":
                status.update(label="⚡ ¡Corto Optimizado y Evaluado con Éxito!", state="complete", expanded=False)
                st.session_state.resultado_tarea = resultado
            else:
                status.update(label="❌ Fallo en procesamiento", state="error")
                st.error(f"Detalle: {resultado.get('mensaje')}")

    if "resultado_tarea" in st.session_state and "tarea_id" in st.session_state:
        res = st.session_state.resultado_tarea
        tid = st.session_state.tarea_id
        
        # 🧠 EXCLUSIVO 110%: Despliegue de métricas reales calculadas por el backend matemático
        st.metric(label="Score de Virabilidad Basado en NLP", value=res.get("viral_score"))
        
        st.markdown("<div class='report-box'><strong>📋 Reporte de Retención de Audiencia:</strong>", unsafe_allow_html=True)
        for frase in res.get("analisis_popularidad", []):
            st.markdown(f"- {frase}")
        st.markdown("</div>", unsafe_allow_html=True)
        st.write("")
        
        dir_tarea = os.path.join("storage", tid)
        if os.path.exists(dir_tarea):
            archivos = [f for f in os.listdir(dir_tarea) if f.startswith("clip_1_viral_")]
            if archivos:
                ruta_clip_final = os.path.join(dir_tarea, archivos[0])
                with open(ruta_clip_final, "rb") as video_file:
                    st.video(video_file.read())
                    
                with open(ruta_clip_final, "rb") as vf:
                    st.download_button(
                        label="📥 Descargar Short en Alta Definición",
                        data=vf,
                        file_name=archivos[0],
                        mime="video/mp4"
                    )
