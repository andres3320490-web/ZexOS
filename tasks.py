import subprocess
import sys
import os
import threading
import time
import uuid

try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--only-binary=:all:", "pillow"])

import streamlit as st
from streamlit_cookies_controller import CookieController
from supabase import create_client, Client

# Importar funciones desde el backend real
from tasks import garantizar_entorno_tarea, pipeline_procesamiento_masivo

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuración obligatoria de Streamlit
st.set_page_config(page_title="ZexOS AI Studio", layout="wide")

# Inicializadores de control de estado asíncrono
if "procesando" not in st.session_state:
    st.session_state.procesando = False
if "tarea_completada" not in st.session_state:
    st.session_state.tarea_completada = False

cookie_controller = CookieController()

# Credenciales de base de datos distribuidas
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"] if "SUPABASE_URL" in st.secrets else "https://lhnwforsissmvwujlfdr.supabase.co"
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"] if "SUPABASE_KEY" in st.secrets else "sb_publishable_9RminSlrRKt7SnRPzosDbg_oN8vrprU"
except Exception:
    SUPABASE_URL = "https://lhnwforsissmvwujlfdr.supabase.co"
    SUPABASE_KEY = "sb_publishable_9RminSlrRKt7SnRPzosDbg_oN8vrprU"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

# Estilo visual CSS personalizado
st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #F1F5F9; }
    h1, h2, h3, .stMarkdown strong { color: #deff9a !important; }
    .stButton>button { background: #deff9a !important; color: #05070a !important; font-weight: 800 !important; border-radius: 10px !important; border: none !important; padding: 12px !important;}
    .clip-card { background-color: #0f172a; padding: 20px; border-radius: 12px; border: 1px solid #1e293b; margin-bottom: 15px; }
    .vip-badge { background-color: #deff9a; color: #05070a; padding: 4px 8px; border-radius: 5px; font-weight: bold; font-size: 12px; }
    .free-badge { background-color: #475569; color: #FFFFFF; padding: 4px 8px; border-radius: 5px; font-weight: bold; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ ZexOS AI Studio Premium Max v3.5")
st.subheader("El Suite Open-Source que supera a Opus Clip")

saved_email = cookie_controller.get("zexos_user_email")
email_usuario = st.text_input("Ingresar cuenta vinculada:", value=saved_email if saved_email else "").strip()

if not email_usuario:
    st.info("💡 Introduce tu dirección de acceso seguro para iniciar los clústeres de renderizado.")
    st.stop()

if saved_email != email_usuario:
    cookie_controller.set("zexos_user_email", email_usuario)

# Sincronización de Base de Datos tolerante a microcortes
es_vip = False
minutos_consumidos = 0

if email_usuario:
    with st.sidebar.spinner("Sincronizando con clúster Supabase..."):
        for intento in range(3):
            try:
                respuesta = supabase.table("usuarios_vip").select("email", "minutos_usados").eq("email", email_usuario).execute()
                if respuesta.data:
                    datos_user = respuesta.data[0]
                    es_vip = True 
                    minutos_consumidos = datos_user.get("minutos_usados", 0)
                break
            except Exception:
                if intento == 2:
                    st.sidebar.error("Aviso de Red: Reconectando base de datos activa...")
                time.sleep(0.5)

st.sidebar.subheader("🛠️ Panel de Configuración Experta")

if es_vip:
    st.sidebar.markdown('Tu Estado: <span class="vip-badge">👑 VIP PREMIUM</span>', unsafe_allow_html=True)
    st.sidebar.caption("⚡ Almacenamiento local: Máximo 6GB habilitado.")
    st.sidebar.caption("⏱️ Tiempo de procesamiento: Infinito.")
else:
    st.sidebar.markdown('Tu Estado: <span class="free-badge">👤 NO-VIP (FREE)</span>', unsafe_allow_html=True)
    st.sidebar.caption("⚠️ Almacenamiento local: Limitado a 2GB.")
    st.sidebar.caption(f"⏱️ Minutos Disponibles: {120 - minutos_consumidos} de 120 min.")
    
    st.sidebar.markdown("---")
    st.sidebar.write("🏆 **Mejora a VIP por solo $10/mes:**")
    url_paypal_sidebar = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=andres3320490@gmail.com&item_name=ZexOS%20AI%20Studio%20VIP&amount=10.00&currency_code=USD"
    st.sidebar.markdown(f'<a href="{url_paypal_sidebar}" target="_blank"><button style="background-color:#deff9a; color:#05070a; border:none; padding:10px; border-radius:8px; font-weight:bold; width:100%; cursor:pointer;">💳 Pagar $10 con PayPal</button></a>', unsafe_allow_html=True)
    st.sidebar.caption("Envía el comprobante para activación inmediata.")
    st.sidebar.markdown("---")

formato_seleccionado = st.sidebar.selectbox("Geometría del Cuadro", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
plantilla = st.sidebar.selectbox("Diseño de Rótulos", options=["hormozi", "classic_three"])
con_sub = st.sidebar.checkbox("Activar Subtitulado Inteligente", value=True)
diccionario_manual = st.sidebar.text_area("Keywords de Alta Retención Temática:", placeholder="brutal, impactante")

col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("📥 Carga de Medios Audiovisuales")
    url_remoto = st.text_input("🔗 Enlace del Video Fuente:", placeholder="YouTube, Twitch, etc.")
    video_subido = st.file_uploader("O arrastra el archivo directamente:", type=["mp4", "mkv"])
    ejecutar = st.button("🚀 PARSEAR Y GENERAR CLIPS VIRALES")

# Hilo secundario de ejecución asíncrona (Previene la congelación de la GUI)
def worker_procesamiento(kwargs_pipeline, email, mins_consumidos, vip_flag, admin_list):
    try:
        resultado = pipeline_procesamiento_masivo(**kwargs_pipeline)
        if resultado and resultado.get("status") == "success":
            st.session_state.resultado_lote = resultado
            st.session_state.tarea_completada = True
            
            if not vip_flag and email not in admin_list:
                nuevos_minutos = mins_consumidos + 5
                for _ in range(3):
                    try:
                        supabase.table("usuarios_vip").update({"minutos_usados": nuevos_minutos}).eq("email", email).execute()
                        break
                    except Exception:
                        time.sleep(0.5)
        else:
            st.session_state.error_tarea = resultado.get("mensaje", "Error interno desconocido en el motor.")
    except Exception as ex:
        st.session_state.error_tarea = f"Excepción crítica en segundo plano: {str(ex)}"
    finally:
        st.session_state.procesando = False

with col_der:
    st.subheader("📊 Centro de Control de Curación Coherente")
    
    if ejecutar and not st.session_state.procesando:
        if not url_remoto.strip() and not video_subido:
            st.error("❌ Por favor, proporciona una URL de video o arrastra un archivo local.")
        else:
            ADMIN_EMAILS = ["andres3320490@gmail.com"]
            limite_gb = 6 if email_usuario in ADMIN_EMAILS else (4 if es_vip else 2)
            limite_bytes = limite_gb * 1024 * 1024 * 1024
            
            if video_subido and video_subido.size > limite_bytes:
                st.error(f"❌ El archivo excede el límite permitido ({limite_gb} GB).")
            elif not es_vip and email_usuario not in ADMIN_EMAILS and minutos_consumidos >= 120:
                st.error("❌ Has agotado tus 120 minutos gratuitos.")
            else:
                tarea_id = f"suite_{uuid.uuid4().hex[:12]}"
                temp_dir = garantizar_entorno_tarea(tarea_id)
                st.session_state.tarea_id = tarea_id
                st.session_state.dir_tarea_actual = temp_dir 
                
                ruta_input = ""
                if video_subido:
                    ruta_input = os.path.join(temp_dir, "video_subido.mp4")
                    with open(ruta_input, "wb") as buffer:
                        buffer.write(video_subido.getvalue())

                # Argumentos empaquetados para el subproceso
                pipeline_args = {
                    "tarea_id": tarea_id,
                    "ruta_video_master": ruta_input,
                    "formato": formato_seleccionado,
                    "con_subtitulos": con_sub,
                    "color_sub_hex": "#deff9a",
                    "estilo_subtitulos": plantilla,
                    "url_remoto": url_remoto,
                    "diccionario_manual": diccionario_manual
                }
                
                # Configurar estados y lanzar hilo
                st.session_state.procesando = True
                st.session_state.tarea_completada = False
                if "error_tarea" in st.session_state: 
                    del st.session_state.error_tarea
                
                hilo = threading.Thread(
                    target=worker_procesamiento,
                    args=(pipeline_args, email_usuario, minutos_consumidos, es_vip, ADMIN_EMAILS)
                )
                hilo.start()

    # Monitoreo visual de la actividad asíncrona
    if st.session_state.procesando:
        st.info("🧠 Procesando video en clúster local secundario. Puedes navegar de pestaña o re-configurar parámetros libremente.")
        st.spinner("Renderizando fotogramas dinámicos...")
        time.sleep(1.5)
        st.rerun()

    if "error_tarea" in st.session_state:
        st.error(f"❌ Ocurrió un inconveniente: {st.session_state.error_tarea}")

# Renderizado estable desacoplado basado en estados persistentes
if st.session_state.tarea_completada and "resultado_lote" in st.session_state:
    st.markdown("---")
    res = st.session_state.resultado_lote
    dir_tarea = st.session_state.dir_tarea_actual
            
    if res and "clips" in res:
        st.write(f"🎉 **Hemos descubierto e indexado {len(res['clips'])} fragmentos virales:**")
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
                    # Streaming nativo directo por ruta (Ahorra el 100% de la memoria RAM del servidor)
                    st.video(ruta_video)
                    
                    with open(ruta_video, "rb") as vf:
                        st.download_button(
                            label=f"📥 Descargar Clip {idx + 1}", 
                            data=vf.read(),
                            file_name=c["archivo"], 
                            mime="video/mp4", 
                            key=f"dl_{idx}"
                        )
                else:
                    st.error("No se pudo localizar el archivo físico en el almacenamiento local.")
                st.markdown("</div>", unsafe_allow_html=True)
