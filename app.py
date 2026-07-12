import subprocess
import sys
import os

# --- PARCHE DE COMPILACIÓN INTERNO PARA PILLOW ---
try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--only-binary=:all:", "pillow"])

import uuid
import streamlit as st
from streamlit_cookies_controller import CookieController

# Asegurar importación limpia del módulo local tasks.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tasks import garantizar_entorno_tarea, pipeline_procesamiento_masivo

cookie_controller = CookieController()

# --- TU DISEÑO Y ESTILO ORIGINAL ---
st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #F1F5F9; }
    h1, h2, h3, .stMarkdown strong { color: #deff9a !important; }
    .stButton>button { background: #deff9a !important; color: #05070a !important; font-weight: 800 !important; border-radius: 10px !important; border: none !important; padding: 12px !important;}
    .clip-card { background-color: #0f172a; padding: 20px; border-radius: 12px; border: 1px solid #1e293b; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ ZexOS AI Studio Premium Max v3.5")
st.subheader("El Suite Open-Source que supera a Opus Clip")

saved_email = cookie_controller.get("zexos_user_email")
email_usuario = st.text_input("Ingresar cuenta vinculada:", value=saved_email if saved_email else "").strip()

if not email_usuario:
    st.info("💡 Introduce tu dirección de acceso seguro para iniciar los clústeres de renderizado.")
    st.stop()

cookie_controller.set("zexos_user_email", email_usuario)

# Parámetros del Sidebar
st.sidebar.subheader("🛠️ Panel de Configuración Experta")
formato = st.sidebar.selectbox("Geometría del Cuadro", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
plantilla = st.sidebar.selectbox("Diseño de Rótulos", options=["hormozi", "classic_three"])
con_sub = st.sidebar.checkbox("Activar Subtitulado Inteligente", value=True)
diccionario_manual = st.sidebar.text_area("Keywords de Alta Retención Temática:", placeholder="brutal, impactante")

col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("📥 Carga de Medios Audiovisuales")
    url_remoto = st.text_input("🔗 Enlace del Video Fuente:", placeholder="YouTube, Twitch, etc.")
    video_subido = st.file_uploader("O arrastra el archivo directamente:", type=["mp4", "mkv"])
    ejecutar = st.button("🚀 PARSEAR Y GENERAR CLIPS VIRALES")

with col_der:
    st.subheader("📊 Centro de Control de Curación Coherente")
    
    if ejecutar:
        if not url_remoto.strip() and not video_subido:
            st.error("❌ Por favor, proporciona una URL de video o arrastra un archivo local.")
        else:
            tarea_id = f"suite_{uuid.uuid4().hex[:12]}"
            st.session_state.tarea_id = tarea_id
            
            temp_dir = garantizar_entorno_tarea(tarea_id)
            ruta_input = ""
            
            if video_subido:
                ruta_input = os.path.join(temp_dir, "video_subido.mp4")
                with open(ruta_input, "wb") as buffer:
                    buffer.write(video_subido.getvalue())
                    
            with st.status("🧠 Extrayendo ganchos narrativos y mapeando clips...", expanded=True) as status:
                # Ejecución directa integrada al pipeline universal
                resultado = pipeline_procesamiento_masivo(
                    tarea_id=tarea_id, 
                    ruta_video_master=ruta_input, 
                    formato=formato,
                    con_subtitulos=con_sub, 
                    color_sub_hex="#deff9a", # Match perfecto con tu branding CSS
                    estilo_subtitulos=plantilla, 
                    url_remoto=url_remoto,
                    diccionario_manual=diccionario_manual
                )
                
                if resultado.get("status") == "success":
                    status.update(label="✨ ¡Procesamiento por lotes completado con éxito!", state="complete", expanded=False)
                    st.session_state.resultado_lote = resultado
                else:
                    status.update(label="❌ Error crítico en el pipeline", state="error")
                    st.error(resultado.get("mensaje"))

    if "resultado_lote" in st.session_state and "tarea_id" in st.session_state:
        res = st.session_state.resultado_lote
        tid = st.session_state.tarea_id
        dir_tarea = os.path.join("storage", tid)
        
        st.write(f"🎉 **Hemos descubierto e indexado {len(res['clips'])} fragmentos con alta probabilidad viral:**")
        
        # Crear pestañas para cada clip generado automáticamente igual que Opus
        nombres_pestanas = [f"Clip {i+1} ({c['score']})" for i, c in enumerate(res["clips"])]
        pestanas = st.tabs(nombres_pestanas)
        
        for idx, c in enumerate(res["clips"]):
            with pestanas[idx]:
                st.markdown("<div class='clip-card'>", unsafe_allow_html=True)
                st.metric(label="Score de Virabilidad Potencial", value=c["score"])
                
                st.write("**Reporte de Indexación:**")
                for r in c["reporte"]:
                    st.write(f"- {r}")
                
                ruta_video = os.path.join(dir_tarea, c["archivo"])
                if os.path.exists(ruta_video):
                    with open(ruta_video, "rb") as vf:
                        st.video(vf.read())
                    
                    with open(ruta_video, "rb") as vf:
                        st.download_button(
                            label=f"📥 Descargar Clip {idx + 1}",
                            data=vf,
                            file_name=c["archivo"],
                            mime="video/mp4",
                            key=f"dl_{idx}"
                        )
                else:
                    st.error("No se pudo localizar el archivo físico de este fragmento.")
                st.markdown("</div>", unsafe_allow_html=True)
