# app.py
import os
import streamlit as st
import requests
from moviepy import VideoFileClip
from supabase import create_client, Client

# 1. Configuración de pantalla con estética SaaS Premium
st.set_page_config(
    page_title="ZexOS AI Studio Enterprise",
    page_icon="⚡",
    layout="wide"
)

# Conexión Segura con tu Base de Datos Supabase
# ⚠️ ADVERTENCIA: Reemplaza "TU_PROJECT_URL_AQUÍ" con tu enlace de Supabase (ej: https://xxxx.supabase.co)
SUPABASE_URL = "https://lhnwforsissmvwujlfdr.supabase.co"
SUPABASE_KEY = "sb_publishable_9RminSlrRKt7SnRPzosDbg_oN8vrprU"

# Inicializamos el cliente de la base de datos de manera segura
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Estilo Cyberpunk Flúor
st.markdown("""
    <style>
    .stApp { background-color: #0A0D14; color: #E2E8F0; }
    h1, h2, h3, .stMarkdown strong { color: #deff9a !important; }
    .stButton>button { 
        width: 100%; background-color: #deff9a !important; color: #0A0D14 !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important;
        box-shadow: 0px 4px 15px rgba(222, 255, 154, 0.3);
    }
    .ad-card {
        background-color: #121620; border: 1px solid #deff9a; padding: 15px; border-radius: 8px; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# URL de tu motor de IA en Hugging Face
BACKEND_API_URL = "https://vzex-zexiastudio.hf.space/procesar"

st.title("🚀 ZexOS AI Studio Core — Cloud SaaS Engine")

# --- PASO 0: IDENTIFICACIÓN DIRECTA SIN CONTRASEÑA ---
st.subheader("📥 Identificación de Usuario")
email_usuario = st.text_input("Introduce tu correo electrónico para iniciar el entorno:", placeholder="ejemplo@correo.com").strip().lower()

if not email_usuario:
    st.info("💡 Introduce tu correo electrónico arriba para desbloquear el panel de control.")
    st.stop()

# --- VERIFICACIÓN AUTOMÁTICA DE RANGO (VIP / PREMIUM / GRATIS) ---
es_premium_o_vip = False
rango_usuario = "Gratuito"

try:
    # Consultamos a Supabase si este correo existe en la lista de compradores o VIPs
    respuesta = supabase.table("usuarios_vip").select("email").eq("email", email_usuario).execute()
    if len(respuesta.data) > 0:
        es_premium_o_vip = True
        rango_usuario = "VIP / Premium Ilimitado 💎"
except Exception:
    st.error("Error temporal de conexión con el nodo de base de datos. Verifica que tu SUPABASE_URL sea correcta.")

st.sidebar.markdown(f"**Usuario Activo:** `{email_usuario}`")
st.sidebar.markdown(f"**Rango de Cuenta:** `{rango_usuario}`")

# --- ANUNCIOS Y CONFIGURACIÓN ---
st.sidebar.markdown("---")
st.sidebar.subheader("Engine Render Specs")
formato_seleccionado = st.sidebar.selectbox("Aspect Ratio Target", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
con_subtitulos = st.sidebar.checkbox("Inyectar Subtítulos Dinámicos", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("📢 Patrocinadores")
html_anuncio = """
<div class="ad-card">
    <a href="https://tu-tienda.lemonsqueezy.com" target="_blank" style="text-decoration: none; color: #E2E8F0;">
        <p style="margin: 0; font-size: 14px; font-weight: bold; color: #deff9a;">⭐ ¡Pásate a PRO!</p>
        <p style="margin: 6px 0 0 0; font-size: 11px; color: #A0AEC0;">Elimina el límite de 60 segundos y procesa videos de hasta 2 horas haciendo clic aquí.</p>
    </a>
</div>
"""
st.sidebar.html(html_anuncio)

# --- PANEL DE SUBIDA ---
st.markdown("---")
if not es_premium_o_vip:
    st.warning("⚠️ **Capa Free Activa:** Límite estricto de **60 segundos** por video.")
else:
    st.success("⚡ **Capa PRO Desbloqueada:** Tienes acceso ilimitado sin restricciones de tiempo.")

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
        
        # APLICAR FILTRO DE TIEMPO SOLO A LOS QUE NO SON VIP/PREMIUM
        if duracion_real > 60.0 and not es_premium_o_vip:
            st.error(f"❌ Tu video dura {duracion_real:.1f}s. Has superado el límite de la cuenta gratuita.")
            st.markdown(f"💡 **¿Quieres renderizar este video?** [Haz clic aquí para comprar el Plan Pro](https://tu-tienda.lemonsqueezy.com) y activa tu correo al instante.")
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
