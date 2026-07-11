# app.py
import os
import streamlit as st
import requests
import time
from supabase import create_client, Client

st.set_page_config(
    page_title="ZexOS AI Studio Enterprise",
    page_icon="⚡",
    layout="wide"
)

# Configuración de base de datos segura integrada
SUPABASE_URL = "https://lhnwforsissmvwujlfdr.supabase.co"
SUPABASE_KEY = "sb_publishable_9RminSlrRKt7SnRPzosDbg_oN8vrprU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

BACKEND_BASE_URL = "https://vzex-zexiastudio.hf.space"

st.title("🚀 ZexOS AI Studio Core (v110% Pro)")

# --- ACCESO DE USUARIO ---
st.subheader("📥 Identificación de Usuario")
email_usuario = st.text_input("Introduce tu correo electrónico para iniciar el entorno:", placeholder="ejemplo@correo.com o Clave Admin").strip()

if not email_usuario:
    st.info("💡 Introduce tu correo electrónico arriba para desbloquear el panel de control.")
    st.stop()

es_premium_o_vip = False
es_admin = False
rango_usuario = "Gratuito"
correo_ingresado_limpio = email_usuario.strip().lower()

if correo_ingresado_limpio == "zexosadmin":
    es_admin = True
    es_premium_o_vip = True
    rango_usuario = "Administrador Principal 🛠️"
    email_usuario = "admin@zexos.com"

try:
    respuesta = supabase.table("usuarios_vip").select("*").execute()
    if respuesta.data and not es_admin:
        for fila in respuesta.data:
            for clave, valor in fila.items():
                if valor is not None and correo_ingresado_limpio == str(valor).strip().lower():
                    es_premium_o_vip = True
                    rango_usuario = "VIP 💎"
                    break
except Exception as e:
    st.warning(f"Aviso de Red Supabase: {str(e)}")

# --- SIDEBAR MONETIZACIÓN & PARÁMETROS ---
st.sidebar.markdown(f"**Usuario:** `{email_usuario}`")
st.sidebar.markdown(f"**Rango:** `{rango_usuario}`")
st.sidebar.markdown("---")

if not es_premium_o_vip:
    st.sidebar.markdown('<div class="pro-box"><span style="font-size: 18px;">💎 <b>PLAN PRO SAAS</b></span><br><span style="color: #deff9a; font-size: 22px; font-weight: bold;">$10.00 / mes</span></div>', unsafe_allow_html=True)
    paypal_html_btn = f"""
    <div style="display: flex; justify-content: center; margin-top: 10px;">
        <form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_blank">
            <input type="hidden" name="cmd" value="_xclick">
            <input type="hidden" name="business" value="andres3320490@gmail.com">
            <input type="hidden" name="item_name" value="ZexOS AI Studio - Plan Pro (Usuario: {email_usuario})">
            <input type="hidden" name="amount" value="10.00">
            <input type="hidden" name="currency_code" value="USD">
            <input type="image" src="https://www.paypalobjects.com/webstatic/en_US/i/buttons/checkout-logo-medium.png" border="0" name="submit">
        </form>
    </div>
    """
    st.sidebar.html(paypal_html_btn)
    st.sidebar.markdown("---")

st.sidebar.subheader("Engine Render Specs")
formato_seleccionado = st.sidebar.selectbox("Aspect Ratio Target", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
con_subtitulos = st.sidebar.checkbox("Inyectar Subtítulos Dinámicos", value=True)
estilo_elegido = st.sidebar.selectbox("Estilo de Subtítulos", options=["hormozi", "classic_three", "minimal"]) if con_subtitulos else "hormozi"

# --- CORE CARGA Y PREVISUALIZACIÓN ---
st.subheader("🎬 Carga de Material Audiovisual")
url_remoto = st.text_input("🔗 Pegar Enlace directo (YouTube, Twitch VOD, Shorts o Reels):", placeholder="https://www.youtube.com/watch?v=...").strip()
video_subido = st.file_uploader("📥 O arrastra un archivo local si lo prefieres:", type=["mp4", "mkv", "mov"])

if video_subido or url_remoto:
    st.success("🎥 Origen multimedia detectado correctamente.")
    col_prev, col_editor = st.columns([1, 1])
    
    with col_prev:
        st.subheader("📺 Previsualización del Vídeo")
        if video_subido:
            st.video(video_subido)
        elif url_remoto:
            st.video(url_remoto)
            
    with col_editor:
        st.subheader("✍️ Editor de Transcripción Manual (Guía de Modulación)")
        st.caption("Escribe palabras clave particulares de tu canal (ej: nombre de VTuber, expresiones, jergas) separadas por comas para forzar el diccionario y pintarlas de color de impacto.")
        diccionario_manual = st.text_area("Ganchos / Correcciones prioritarias:", placeholder="ejemplo: VTuber, ZexOS, clips, épico, brutal", height=100)
        
        if st.button("🚀 INICIAR COMPILACIÓN EN SEGUNDO PLANO"):
            with st.spinner("Enviando orden de renderizado asíncrono..."):
                try:
                    datos_formulario = {
                        "formato": formato_seleccionado,
                        "con_subtitulos": str(con_subtitulos).lower(),
                        "estilo_subtitulos": estilo_elegido,
                        "url_remoto": url_remoto,
                        "diccionario_manual": diccionario_manual
                    }
                    
                    if video_subido:
                        archivos = {"file": (video_subido.name, video_subido.getvalue(), video_subido.type)}
                        r = requests.post(f"{BACKEND_BASE_URL}/procesar", files=archivos, data=datos_formulario)
                    else:
                        r = requests.post(f"{BACKEND_BASE_URL}/procesar", data=datos_formulario)
                        
                    if r.status_code == 200:
                        tarea_id = r.json().get("tarea_id")
                        status_placeholder = st.empty()
                        bar_progreso = st.progress(0)
                        
                        # --- LOOP ANTI-TIMEOUT POLLING ENGINE ---
                        while True:
                            check_r = requests.get(f"{BACKEND_BASE_URL}/estado/{tarea_id}")
                            if check_r.status_code == 200:
                                info_tarea = check_r.json()
                                estado = info_tarea.get("status")
                                
                                if estado == "processing":
                                    status_placeholder.markdown("⏳ **La IA está aislando silencios, procesando avatares mediante filtro híbrido y animando subtítulos...**")
                                    bar_progreso.progress(45)
                                elif estado == "completed":
                                    status_placeholder.empty()
                                    bar_progreso.progress(100)
                                    st.balloons()
                                    
                                    st.subheader("🔥 ¡Tus Clips Listos para Redes!")
                                    st.metric(label="📊 Curation Viral Score", value=info_tarea.get("viral_score", "94%"))
                                    
                                    res_download = requests.get(f"{BACKEND_BASE_URL}/descargar/{tarea_id}")
                                    if res_download.status_code == 200:
                                        st.video(res_download.content)
                                        st.download_button("📥 Descargar Primer Clip de la Parrilla", data=res_download.content, file_name=f"zexos_short_{tarea_id[:5]}.mp4", mime="video/mp4")
                                    break
                                elif estado == "failed":
                                    st.error(f"❌ Falló el procesamiento del motor: {info_tarea.get('error')}")
                                    break
                            else:
                                st.error("❌ Conexión interrumpida.")
                                break
                            time.sleep(5)
                except Exception as e:
                    st.error(f"Error en llamada de red: {str(e)}")
