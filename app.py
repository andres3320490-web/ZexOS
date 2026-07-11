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
    .paypal-container {
        display: flex;
        justify-content: center;
        margin-top: 10px;
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


# =========================================================================
# ✅ CORREO CONFIGURADO PARA RECIBIR TUS PAGOS DIRECTOS
# =========================================================================
CORREO_PAYPAL = "andres3320490@gmail.com"
# =========================================================================


# --- PASO 3: ENLACE DE PAGO DIRECTO A PAYPAL ---
if not es_premium_o_vip:
    st.sidebar.markdown("""
    <div class="pro-box">
        <span style="font-size: 18px;">💎 <b>PLAN PRO SAAS</b></span><br>
        <span style="color: #deff9a; font-size: 22px; font-weight: bold;">$10.00 / mes</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulario HTML estándar de PayPal para pagos rápidos
    paypal_html_btn = f"""
    <div class="paypal-container">
        <form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_blank">
            <input type="hidden" name="cmd" value="_xclick">
            <input type="hidden" name="business" value="{CORREO_PAYPAL}">
            <input type="hidden" name="item_name" value="ZexOS AI Studio - Plan Pro (Usuario: {email_usuario})">
            <input type="hidden" name="amount" value="10.00">
            <input type="hidden" name="currency_code" value="USD">
            <input type="hidden" name="no_shipping" value="1">
            <input type="image" src="https://www.paypalobjects.com/webstatic/en_US/i/buttons/checkout-logo-medium.png" border="0" name="submit" alt="PayPal - The safer, easier way to pay online!">
        </form>
    </div>
    """
    st.sidebar.html(paypal_html_btn)
    
    # Mensaje de aclaración sobre el tiempo de activación manual
    st.sidebar.info("⏳ **Activación del servicio:** Tras completar tu pago en PayPal, el estado Pro se validará y activará en tu cuenta en un lapso máximo de **24 horas**.")
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
            st.info("💡 **SaaS Lock:** Utiliza el botón de PayPal en la barra lateral para adquirir tu suscripción.")
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
        st.error(f"Error al procesar el archivo: {str(e)}")
        if os.path.exists(path_temporal): os.remove(path_temporal)
