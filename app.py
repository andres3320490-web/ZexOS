# app.py
import os
import streamlit as st
import requests
from moviepy import VideoFileClip
from supabase import create_client, Client

# 1. Configuración de pantalla
st.set_page_config(
    page_title="ZexOS AI Studio Enterprise",
    page_icon="⚡",
    layout="wide"
)

SUPABASE_URL = "https://lhnwforsissmvwujlfdr.supabase.co"
SUPABASE_KEY = "sb_publishable_9RminSlrRKt7SnRPzosDbg_oN8vrprU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Estilos Cyberpunk
st.markdown("""
    <style>
    .stApp { background-color: #0A0D14; color: #E2E8F0; }
    h1, h2, h3, .stMarkdown strong { color: #deff9a !important; }
    .stButton>button { 
        width: 100%; background-color: #deff9a !important; color: #0A0D14 !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important;
    }
    .pro-box {
        background-color: #121620; border: 2px dashed #deff9a; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

BACKEND_API_URL = "https://vzex-zexiastudio.hf.space/procesar"

st.title("🚀 ZexOS AI Studio Core")

# --- PASO 0: IDENTIFICACIÓN DE USUARIO ---
st.subheader("📥 Identificación de Usuario")
email_usuario = st.text_input("Introduce tu correo electrónico para iniciar el entorno:", placeholder="ejemplo@correo.com").strip().lower()

if not email_usuario:
    st.info("💡 Introduce tu correo electrónico arriba para desbloquear el panel de control.")
    st.stop()

# --- VERIFICACIÓN DE RANGO ---
es_premium_o_vip = False
rango_usuario = "Gratuito"

try:
    respuesta = supabase.table("usuarios_vip").select("email").eq("email", email_usuario).execute()
    if respuesta.data and len(respuesta.data) > 0:
        es_premium_o_vip = True
        rango_usuario = "VIP / Premium Ilimitado 💎"
except Exception:
    st.warning("Aviso: Nodo de base de datos en espera.")

# --- BARRA LATERAL ---
st.sidebar.markdown(f"**Usuario:** `{email_usuario}`")
st.sidebar.markdown(f"**Rango:** `{rango_usuario}`")
st.sidebar.markdown("---")

# --- PASO 3: ENLACE DE PAGO SEGURO ---
if not es_premium_o_vip:
    st.sidebar.markdown("""
    <div class="pro-box">
        <span style="font-size: 18px;">💎 <b>PLAN PRO SAAS</b></span><br>
        <span style="color: #deff9a; font-size: 22px; font-weight: bold;">$10.00 / mes</span>
    </div>
    """, unsafe_allow_html=True)
    
    # URL Base (Cámbiala por tu link de Lemon Squeezy cuando lo tengas)
    url_pago_base = "https://www.google.com" 
    url_con_checkout_seguro = f"{url_pago_base}?checkout[email]={email_usuario}"
    
    st.sidebar.link_button("⭐ PAGAR CON TARJETA (1 MES)", url_con_checkout_seguro)
    st.sidebar.markdown("---")

# --- PROCESAMIENTO MULTIMEDIA ---
st.sidebar.subheader("Engine Render Specs")
formato_seleccionado = st.sidebar.selectbox("Aspect Ratio Target", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
con_subtitulos = st.sidebar.checkbox("Inyectar Subtítulos Dinámicos", value=True)

if not es_premium_o_vip:
    st.warning("⚠️ **Capa Free Activa:** Límite estricto de **60 segundos** por video.")
else:
    st.success("⚡ **Capa PRO Desbloqueada:** Renders ilimitados activos.")

video_subido = st.file_uploader("Cargar Máster Audiovisual", type=["mp4", "mkv", "mov"])

if video_subido:
    path_temporal = "validando_duracion.mp4"
    with open(path_temporal, "wb") as f:
        f.write(video_subido.getvalue())
        
    try:
        clip_prueba = VideoFileClip(path_temporal)
        duracion_real = clip_prueba.duration
        clip_prueba.close()
        if os.path.exists(path_temporal): os.remove(path_temporal)
            
        st.write(f"⏱️ Duración detectada: `{duracion_real:.2f} segundos`")
        
        if duracion_real > 60.0 and not es_premium_o_vip:
            st.error(f"❌ Tu video dura {duracion_real:.1f}s. Has superado el límite de la cuenta gratuita.")
            st.markdown(f"💡 **SaaS Lock:** [Haz clic aquí para activar tu suscripción e introducir tu tarjeta]({url_con_checkout_seguro})")
        else:
            st.success("✅ Estructura multimedia óptima para el renderizado.")
            col_preview, col_render = st.columns([1, 1])
            with col_preview:
                st.subheader("Source Preview")
                st.video(video_subido)
            with col_render:
                st.subheader("Orquestación Cloud")
                if st.button("EJECUTAR COMPILACIÓN"):
                    with st.spinner("Procesando en la nube con IA..."):
                        try:
                            archivos_envio = {"file": (video_subido.name, video_subido.getvalue(), video_subido.type)}
                            datos_formulario = {"formato": formato_seleccionado, "con_subtitulos": str(con_subtitulos).lower()}
                            respuesta = requests.post(BACKEND_API_URL, files=archivos_envio, data=datos_formulario, timeout=600)
                            if respuesta.status_code == 200:
                                st.balloons()
                                st.subheader("Resultado Final")
                                st.video(respuesta.content)
                                st.download_button(label="📥 Descargar MP4", data=respuesta.content, file_name=f"zexos_{video_subido.name}", mime="video/mp4")
                            else:
                                st.error(f"Error en el servidor de IA: {respuesta.text}")
                        except Exception as e:
                            st.error(f"Error de red: {str(e)}")
    except Exception as e:
        st.error(f"Error analizando video: {str(e)}")                
