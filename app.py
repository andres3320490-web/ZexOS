import os
import streamlit as st
import requests
import time
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

# =========================================================================
# 🚀 CONEXIÓN LOCAL DIRECTA ORQUESTADA POR SUPERVISOR
# =========================================================================
BACKEND_BASE_URL = "http://127.0.0.1:8000"
# =========================================================================

st.set_page_config(
    page_title="ZexOS AI Studio Enterprise",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar el controlador de cookies premium
controller = CookieController()

# Conexión Segura al clúster de Base de Datos
SUPABASE_URL = "https://lhnwforsissmvwujlfdr.supabase.co"
SUPABASE_KEY = "sb_publishable_9RminSlrRKt7SnRPzosDbg_oN8vrprU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- INYECCIÓN DE INTERFAZ HORIZONTAL PREMIUM ---
st.markdown("""
    <style>
    .stApp { background-color: #07090e; color: #E2E8F0; }
    h1, h2, h3, .stMarkdown strong { color: #deff9a !important; font-family: 'Inter', sans-serif; }
    .clip-card {
        background: #111625; border: 1px solid #1e293b; border-radius: 12px;
        padding: 16px; margin-bottom: 12px; display: flex;
        justify-content: space-between; align-items: center; transition: all 0.3s ease;
    }
    .clip-card.locked { border-left: 4px solid #ef4444; opacity: 0.5; }
    .clip-card.processing { border-left: 4px solid #3b82f6; animation: pulseBorder 1.5s infinite; }
    .clip-card.unlocked { border-left: 4px solid #deff9a; background: #16222f; }
    @keyframes pulseBorder {
        0% { border-color: #1e293b; } 50% { border-color: #3b82f6; } 100% { border-color: #1e293b; }
    }
    .skeleton-loader {
        width: 100%; height: 10px;
        background: linear-gradient(90deg, #111625 25%, #222d44 50%, #111625 75%);
        background-size: 200% 100%; animation: loadingSkeleton 1.5s infinite;
        border-radius: 6px; margin-top: 6px; margin-bottom: 15px;
    }
    @keyframes loadingSkeleton { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
    .stButton>button { 
        width: 100%; background: #deff9a !important; color: #07090e !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important;
    }
    .pro-box { background-color: #121620; border: 2px dashed #deff9a; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ ZexOS AI Studio Enterprise")

try:
    user_ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
except Exception:
    user_ip = "127.0.0.1"  

st.subheader("📥 Identificación de Entorno")
email_usuario = st.text_input("Correo electrónico corporativo:", placeholder="ejemplo@correo.com").strip()

if not email_usuario:
    st.info("💡 Introduce tus credenciales en la caja superior para desplegar tu espacio de trabajo.")
    st.stop()

correo_ingresado_limpio = email_usuario.strip().lower()
cuenta_vinculada_en_dispositivo = controller.get("zexos_device_owner")

if correo_ingresado_limpio != "zexosadmin":
    if cuenta_vinculada_en_dispositivo and cuenta_vinculada_en_dispositivo != correo_ingresado_limpio:
        st.error(f"⛔ **POLÍTICA ANTI-FRAUDE:** Este dispositivo ya pertenece a `{cuenta_vinculada_en_dispositivo}`.")
        st.stop()
        
    try:
        res_ip = supabase.table("registro_ips").select("*").eq("ip_address", user_ip).execute()
        cuentas_asociadas = [fila["email"] for fila in res_ip.data] if res_ip.data else []
        
        if correo_ingresado_limpio not in cuentas_asociadas:
            if len(cuentas_asociadas) >= 3:
                st.error(f"⛔ **LÍMITE EXCEDIDO:** La IP `{user_ip}` ya tiene el máximo de 3 cuentas gratuitas.")
                st.stop()
            else:
                supabase.table("registro_ips").insert({"ip_address": user_ip, "email": correo_ingresado_limpio}).execute()
    except Exception as e:
        st.warning(f"⚠️ Contingencia de base de datos activa: {str(e)}")

    if not cuenta_vinculada_en_dispositivo:
        controller.set("zexos_device_owner", correo_ingresado_limpio)
        st.rerun()

es_premium_o_vip = False
es_admin = False
rango_usuario = "Gratuito"

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
    st.warning(f"Bypass de verificación premium activo: {str(e)}")

st.sidebar.markdown(f"### 👤 Perfil: `{email_usuario}`")
st.sidebar.markdown(f"**IP:** `{user_ip}`")
st.sidebar.markdown(f"**Rango:** {rango_usuario}")
st.sidebar.markdown("---")

if not es_premium_o_vip:
    st.sidebar.markdown('<div class="pro-box"><span>💎 <b>UPGRADE A VIP RENDER</b></span><br><span style="color: #deff9a; font-size: 20px; font-weight: bold;">$10.00 / mes</span></div>', unsafe_allow_html=True)
    paypal_html_btn = f"""
    <div style="display: flex; justify-content: center;">
        <form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_blank">
            <input type="hidden" name="cmd" value="_xclick">
            <input type="hidden" name="business" value="andres3320490@gmail.com">
            <input type="hidden" name="item_name" value="ZexOS AI Studio Pro - {email_usuario}">
            <input type="hidden" name="amount" value="10.00">
            <input type="hidden" name="currency_code" value="USD">
            <input type="image" src="https://www.paypalobjects.com/webstatic/en_US/i/buttons/checkout-logo-medium.png" border="0" name="submit">
        </form>
    </div>
    """
    st.sidebar.html(paypal_html_btn)
    st.sidebar.markdown("---")

formato_seleccionado = st.sidebar.selectbox("Relación de Aspecto Target", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
con_subtitulos = st.sidebar.checkbox("Subtítulos Dinámicos Inteligentes", value=True)
estilo_elegido = st.sidebar.selectbox("Plantilla Tipográfica", options=["hormozi", "classic_three", "minimal"]) if con_subtitulos else "hormozi"
diccionario_manual = st.sidebar.text_area("Ganchos prioritarios:", placeholder="VTuber, épico, brutal", height=80)

col_izquierda, col_derecha = st.columns([1, 1], gap="large")

with col_izquierda:
    st.subheader("📥 Carga de Material Audiovisual")
    url_remoto = st.text_input("🔗 Enlace Directo (YouTube, TikTok, Twitch):", placeholder="https://...").strip()
    limite_texto = "Máximo 4GB 💎" if es_premium_o_vip else "Máximo 2GB ⚡"
    st.markdown(f"<small style='color:#94a3b8;'>Soporte: {limite_texto}</small>", unsafe_allow_html=True)
    video_subido = st.file_uploader("O sube tu archivo local aquí:", type=["mp4", "mkv", "mov"])
    
    bloquear_envio = False
    if video_subido is not None:
        tamanio_gb = video_subido.size / (1024 * 1024 * 1024)
        if not es_premium_o_vip and tamanio_gb > 2.0:
            st.error("⛔ Archivo demasiado grande. El plan gratuito limita a 2 GB.")
            bloquear_envio = True
        elif es_premium_o_vip and tamanio_gb > 4.0:
            st.error("⛔ Archivo excede el límite VIP de 4 GB.")
            bloquear_envio = True

    boton_procesar = st.button("🚀 INICIAR PROCESAMIENTO HÍBRIDO", disabled=bloquear_envio)

with col_derecha:
    st.subheader("📊 Monitorización de Clips y Descarga")
    
    if not boton_procesar and "tarea_id" not in st.session_state:
        st.info("⌛ Configura tu material en la sección izquierda para inicializar.")
    
    if boton_procesar and not bloquear_envio:
        st.session_state.procesando = True
        with st.spinner("Conectando con el clúster..."):
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
                    r = requests.post(f"{BACKEND_BASE_URL}/procesar/", files=archivos, data=datos_formulario, timeout=(10, 600))
                else:
                    r = requests.post(f"{BACKEND_BASE_URL}/procesar/", data=datos_formulario, timeout=(10, 600))
                    
                if r.status_code == 200:
                    st.session_state.tarea_id = r.json().get("tarea_id")
                else:
                    st.error(f"❌ Error en la comunicación ({r.status_code}): {r.text}")
            except Exception as e:
                st.error(f"Error crítico de red: {str(e)}")

    if "tarea_id" in st.session_state:
        tarea_id = st.session_state.tarea_id
        placeholder_monitor = st.empty()
        fases_ia = [
            "Aislamiento de silencios y frecuencias de voz con Whisper",
            "Análisis adaptativo VTuber / Tracker facial OpenCV predictivo",
            "Generación e inyección tipográfica animada Pop-In",
            "Exportación y empaquetado de Shorts independientes"
        ]
        
        while True:
            try:
                check_r = requests.get(f"{BACKEND_BASE_URL}/estado/{tarea_id}/", timeout=5)
                if check_r.status_code == 200:
                    info_tarea = check_r.json()
                    estado = info_tarea.get("status")
                    
                    if estado in ["processing", "pending", "queued"]:
                        with placeholder_monitor.container():
                            st.markdown("#### ⚙️ Pipeline de Ejecución de IA:")
                            for i, fase in enumerate(fases_ia):
                                if i == 0 and estado == "processing":
                                    st.markdown(f'<div class="clip-card processing"><span>🔄 <b>Fase 1:</b> {fase}</span><span style="color:#3b82f6; font-weight:bold;">Procesando...</span></div><div class="skeleton-loader"></div>', unsafe_allow_html=True)
                                elif i == 0:
                                    st.markdown(f'<div class="clip-card processing"><span>⏳ <b>En cola:</b> {fase}</span></div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="clip-card locked"><span>🔒 <b>Fase {i+1}:</b> {fase}</span></div>', unsafe_allow_html=True)
                                    
                    elif estado == "completed":
                        placeholder_monitor.empty()
                        st.balloons()
                        st.markdown('<div class="clip-card unlocked"><span>✅ <b>¡Clips listos en la nube!</b></span></div>', unsafe_allow_html=True)
                        
                        total_clips = info_tarea.get("total_clips", 1)
                        opciones_clips = [f"🔥 Short # {i+1}" for i in range(total_clips)]
                        clip_elegido = st.selectbox("Selecciona fragmento:", options=opciones_clips)
                        indice_clip = opciones_clips.index(clip_elegido) + 1
                        
                        if st.button(f"🔍 Verificar {clip_elegido}"):
                            with st.spinner("Cargando clip..."):
                                res_download = requests.get(f"{BACKEND_BASE_URL}/descargar/{tarea_id}/?clip_num={indice_clip}")
                                if res_download.status_code == 200:
                                    st.video(res_download.content)
                                    st.download_button(label=f"📥 Descargar {clip_elegido}", data=res_download.content, file_name=f"clip_{indice_clip}.mp4", mime="video/mp4")
                        break
                        
                    elif estado == "failed":
                        st.error(f"❌ Error en procesamiento: {info_tarea.get('error')}")
                        break
            except Exception as e:
                st.caption(f"Estabilizando conexión con el clúster...: {str(e)}")
            
            time.sleep(4)
