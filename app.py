import os
import streamlit as st
import requests
import time
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

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

# --- INYECCIÓN DE INTERFAZ HORIZONTAL PREMIUM (CSS GRID / FLEXBOX) ---
st.markdown("""
    <style>
    .stApp { background-color: #07090e; color: #E2E8F0; }
    h1, h2, h3, .stMarkdown strong { color: #deff9a !important; font-family: 'Inter', sans-serif; }
    
    /* Contenedor de Tarjetas de Progreso de la IA */
    .clip-card {
        background: #111625;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
    }
    .clip-card.locked {
        border-left: 4px solid #ef4444;
        opacity: 0.5;
    }
    .clip-card.processing {
        border-left: 4px solid #3b82f6;
        animation: pulseBorder 1.5s infinite;
    }
    .clip-card.unlocked {
        border-left: 4px solid #deff9a;
        background: #16222f;
    }
    
    /* Animación del Skeleton Loader Comercial */
    @keyframes pulseBorder {
        0% { border-color: #1e293b; }
        50% { border-color: #3b82f6; }
        100% { border-color: #1e293b; }
    }
    .skeleton-loader {
        width: 100%;
        height: 10px;
        background: linear-gradient(90deg, #111625 25%, #222d44 50%, #111625 75%);
        background-size: 200% 100%;
        animation: loadingSkeleton 1.5s infinite;
        border-radius: 6px;
        margin-top: 6px;
        margin-bottom: 15px;
    }
    @keyframes loadingSkeleton {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Botones de Acción Estilo Neon SaaS */
    .stButton>button { 
        width: 100%; background: #deff9a !important; color: #07090e !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important;
        box-shadow: 0 4px 14px rgba(222, 255, 154, 0.15);
    }
    .pro-box {
        background-color: #121620; border: 2px dashed #deff9a; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# URL CORREGIDA: Apunta a la Direct API dinámica sin el subdominio '.static'
BACKEND_BASE_URL = "https://vzex-zexiastudio.hf.space"

st.title("⚡ ZexOS AI Studio Enterprise")

# --- OBTENCIÓN DE IP PÚBLICA EN TORNO NUBE ---
try:
    user_ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
except Exception:
    user_ip = "127.0.0.1"  

# --- CONTROL DE ACCESO E IDENTIFICACIÓN ---
st.subheader("📥 Identificación de Entorno")
email_usuario = st.text_input("Correo electrónico corporativo / Clave Acceso:", placeholder="ejemplo@correo.com").strip()

if not email_usuario:
    st.info("💡 Introduce tus credenciales en la caja superior para desplegar tu espacio de trabajo horizontal.")
    st.stop()

correo_ingresado_limpio = email_usuario.strip().lower()

# =========================================================================
# 🔒 MITIGACIÓN EFECTIVA: CONTROL DE COOKIES CON CONTROLADOR EXTERNO
# =========================================================================
cuenta_vinculada_en_dispositivo = controller.get("zexos_device_owner")

if correo_ingresado_limpio != "zexosadmin":
    
    # 1. Validación cruzada por Cookies del Dispositivo
    if cuenta_vinculada_en_dispositivo and cuenta_vinculada_en_dispositivo != correo_ingresado_limpio:
        st.error(f"⛔ **POLÍTICA ANTI-FRAUDE:** Este dispositivo ya está vinculado a la cuenta `{cuenta_vinculada_en_dispositivo}`.")
        st.stop()
        
    # 2. Validación de Límites por IP vía Supabase (MODIFICADO A 3 CUENTAS MÁXIMO)
    try:
        res_ip = supabase.table("registro_ips").select("*").eq("ip_address", user_ip).execute()
        cuentas_asociadas = [fila["email"] for fila in res_ip.data] if res_ip.data else []
        
        if correo_ingresado_limpio not in cuentas_asociadas:
            if len(cuentas_asociadas) >= 3:
                st.error(f"⛔ **LÍMITE DE IP EXCEDIDO:** Esta dirección IP (`{user_ip}`) ya ha alcanzado el máximo de 3 cuentas permitidas para el plan gratuito.")
                st.stop()
            else:
                supabase.table("registro_ips").insert({"ip_address": user_ip, "email": correo_ingresado_limpio}).execute()
    except Exception as e:
        st.warning(f"⚠️ Validación de IP en modo contingencia (Bypass temporal): {str(e)}")

    # Guardar en cookies usando el controlador si el dispositivo estaba limpio
    if not cuenta_vinculada_en_dispositivo:
        controller.set("zexos_device_owner", correo_ingresado_limpio)
        st.rerun()

# --- LÓGICA DINÁMICA DE PERMISOS ---
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
    st.warning(f"Conexión Supabase Bypass (Offline Mode): {str(e)}")

# --- CONFIGURACIÓN EN BARRA LATERAL (SIDEBAR DASHBOARD STYLE) ---
st.sidebar.markdown(f"### 👤 Perfil: `{email_usuario}`")
st.sidebar.markdown(f"**IP Rastreada:** `{user_ip}`")
st.sidebar.markdown(f"**Rango Actual:** {rango_usuario}")
st.sidebar.markdown("---")

if not es_premium_o_vip:
    st.sidebar.markdown('<div class="pro-box"><span style="font-size: 14px;">💎 <b>UPGRADE A VIP RENDER</b></span><br><span style="color: #deff9a; font-size: 20px; font-weight: bold;">$10.00 / mes</span></div>', unsafe_allow_html=True)
    paypal_html_btn = f"""
    <div style="display: flex; justify-content: center; margin-top: 5px;">
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

st.sidebar.subheader("🎛️ Configuración de Renderizado")
formato_seleccionado = st.sidebar.selectbox("Relación de Aspecto Target", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
con_subtitulos = st.sidebar.checkbox("Subtítulos Dinámicos Inteligentes", value=True)
estilo_elegido = st.sidebar.selectbox("Plantilla Tipográfica", options=["hormozi", "classic_three", "minimal"]) if con_subtitulos else "hormozi"

st.sidebar.markdown("---")
st.sidebar.subheader("✍️ Filtros de Transcripción Manual")
diccionario_manual = st.sidebar.text_area("Ganchos prioritarios (separados por comas):", placeholder="VTuber, épico, brutal, reaccion", height=80)

# --- ARQUITECTURA DE TRABAJO HORIZONTAL (DASHBOARD) ---
col_izquierda, col_derecha = st.columns([1, 1], gap="large")

with col_izquierda:
    st.subheader("📥 Carga de Material Audiovisual")
    url_remoto = st.text_input("🔗 Enlace Directo (YouTube, Twitch VOD, Reels, TikTok):", placeholder="https://www.youtube.com/watch?v=...").strip()
    
    if es_premium_o_vip:
        limite_texto = "Soporte de Carga VIP: Máximo 4GB por archivo (Límite Ampliado) 💎"
    else:
        limite_texto = "Soporte de Carga Regular: Máximo 2GB por archivo (Obtén Plan VIP para habilitar 4GB) ⚡"
        
    st.markdown(f"<small style='color:#94a3b8;'>{limite_texto}</small>", unsafe_allow_html=True)
    video_subido = st.file_uploader(
        "O arrastra tu archivo multimedia local aquí:", 
        type=["mp4", "mkv", "mov"],
        help=f"La tasa de transferencia acepta hasta {limite_texto}."
    )
    
    # --- VALIDACIÓN DEL TAMAÑO ---
    bloquear_envio = False
    if video_subido is not None:
        tamanio_gb = video_subido.size / (1024 * 1024 * 1024)
        if not es_premium_o_vip and tamanio_gb > 2.0:
            st.error(f"⛔ ¡Acceso Denegado! Tu archivo pesa {tamanio_gb:.2f} GB. El plan gratuito solo permite hasta 2 GB.")
            bloquear_envio = True
        elif es_premium_o_vip and tamanio_gb > 4.0:
            st.error(f"⛔ ¡Límite Excedido! Las cuentas VIP tienen un tope máximo de 4 GB. Tu archivo pesa {tamanio_gb:.2f} GB.")
            bloquear_envio = True

    boton_procesar = st.button("🚀 INICIAR PROCESAMIENTO HÍBRIDO", disabled=bloquear_envio)

with col_derecha:
    st.subheader("📊 Monitorización de Clips y Descarga")
    
    if not boton_procesar and "tarea_id" not in st.session_state:
        st.info("⌛ Configura tu material en la sección izquierda y presiona el botón para inicializar la Grid de descargas.")
    
    if boton_procesar and not bloquear_envio:
        st.session_state.procesando = True
        with st.spinner("Conectando con el clúster de procesamiento asíncrono..."):
            try:
                datos_formulario = {
                    "formato": formato_seleccionado,
                    "con_subtitulos": str(con_subtitulos).lower(),
                    "estilo_subtitulos": estilo_elegido,
                    "url_remoto": url_remoto,
                    "diccionario_manual": diccionario_manual
                }
                
                timeout_config = (10, 600)

                # CORREGIDO: Las rutas ahora terminan en '/' para cumplir con los proxies de Hugging Face
                if video_subido:
                    archivos = {"file": (video_subido.name, video_subido.getvalue(), video_subido.type)}
                    r = requests.post(f"{BACKEND_BASE_URL}/procesar/", files=archivos, data=datos_formulario, timeout=timeout_config)
                else:
                    r = requests.post(f"{BACKEND_BASE_URL}/procesar/", data=datos_formulario, timeout=timeout_config)
                    
                if r.status_code == 200:
                    st.session_state.tarea_id = r.json().get("tarea_id")
                else:
                    st.error(f"❌ El backend rechazó la petición (Código {r.status_code}). Detalle: {r.text}")
            except requests.exceptions.Timeout:
                st.error("⏳ La subida del video tardó demasiado tiempo y el clúster interrumpió la conexión.")
            except Exception as e:
                st.error(f"Error crítico de red: {str(e)}")

    # --- POLLING LOOP SEGURO CON SKELETON LOADERS ---
    if "tarea_id" in st.session_state:
        tarea_id = st.session_state.tarea_id
        placeholder_monitor = st.empty()
        fases_ia = [
            "Aislamiento de silencios y frecuencias de voz con Whisper",
            "Análisis adaptativo VTuber / Tracker facial OpenCV predictivo",
            "Generación e inyección tipográfica animada Pop-In",
            "Exportación y empaquetado de Shorts independientes en disco"
        ]
        
        while True:
            try:
                # CORREGIDO: Inclusión del slash final reglamentario para el endpoint de estado
                check_r = requests.get(f"{BACKEND_BASE_URL}/estado/{tarea_id}/", timeout=5)
                if check_r.status_code == 200:
                    info_tarea = check_r.json()
                    estado = info_tarea.get("status")
                    
                    if estado in ["processing", "pending", "queued"]:
                        with placeholder_monitor.container():
                            st.markdown("#### ⚙️ Pipeline de Ejecución de Inteligencia Artificial:")
                            for i, fase in enumerate(fases_ia):
                                if i == 0:
                                    st.markdown(f'<div class="clip-card processing"><span>🔄 <b>Fase 1:</b> {fase}</span><span style="color:#3b82f6; font-weight:bold;">Procesando...</span></div><div class="skeleton-loader"></div>', unsafe_allow_html=True)
                                elif i == 1:
                                    st.markdown(f'<div class="clip-card locked"><span>🔒 <b>Fase 2:</b> {fase}</span><span style="color:#ef4444;">Esperando fase previa</span></div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="clip-card locked"><span>🔒 <b>Fase {i+1}:</b> {fase}</span></div>', unsafe_allow_html=True)
                                    
                    elif estado == "completed":
                        placeholder_monitor.empty()
                        st.balloons()
                        st.markdown('<div class="clip-card unlocked"><span>✅ <b>¡Parrilla Multi-Clip Compilada con Éxito!</b></span></div>', unsafe_allow_html=True)
                        
                        total_clips = info_tarea.get("total_clips", 1)
                        opciones_clips = [f"🔥 Short # {i+1}" for i in range(total_clips)]
                        clip_elegido = st.selectbox("Selecciona qué fragmento deseas procesar:", options=opciones_clips)
                        indice_clip = opciones_clips.index(clip_elegido) + 1
                        
                        if st.button(f"🔍 Cargar y Verificar {clip_elegido}"):
                            with st.spinner("Cargando archivo..."):
                                # CORREGIDO: Endpoint estructurado con barra al final antes de los parámetros
                                res_download = requests.get(f"{BACKEND_BASE_URL}/descargar/{tarea_id}/?clip_num={indice_clip}")
                                if res_download.status_code == 200:
                                    st.video(res_download.content)
                                    st.download_button(label=f"📥 Descargar {clip_elegido}", data=res_download.content, file_name=f"clip_{indice_clip}.mp4", mime="video/mp4")
                        break
                    elif estado == "failed":
                        st.error(f"❌ Error en clúster: {info_tarea.get('error')}")
                        break
            except Exception as e:
                st.caption(f"Conectando con el clúster... (Reintentando): {str(e)}")
            
            time.sleep(4)
