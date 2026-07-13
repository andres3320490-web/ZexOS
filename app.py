import subprocess
import sys
import os

try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--only-binary=:all:", "pillow"])

import uuid
import streamlit as st
from streamlit_cookies_controller import CookieController
from supabase import create_client, Client

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from tasks import garantizar_entorno_tarea, pipeline_procesamiento_masivo
except ImportError as e:
    st.error(f"❌ Error crítico de importación en tasks.py: {e}")
    st.stop()

cookie_controller = CookieController()

SUPABASE_URL = "https://lhnwforsissmvwujlfdr.supabase.co"
SUPABASE_KEY = "sb_publishable_9RminSlrRKt7SnRPzosDbg_oN8vrprU"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

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

cookie_controller.set("zexos_user_email", email_usuario)

try:
    respuesta = supabase.table("usuarios_vip").select("email").eq("email", email_usuario).execute()
    es_vip = len(respuesta.data) > 0
except Exception:
    es_vip = False

if "minutos_usados" not in st.session_state:
    st.session_state.minutos_usados = 0
minutos_consumidos = st.session_state.minutos_usados

st.sidebar.subheader("🛠️ Panel de Configuración Experta")

if es_vip:
    st.sidebar.markdown('Tu Estado: <span class="vip-badge">👑 VIP PREMIUM</span>', unsafe_allow_html=True)
    st.sidebar.caption("⚡ Almacenamiento en Servidor Local: Máximo 6GB habilitado.")
    st.sidebar.caption("⏱️ Tiempo de procesamiento: Infinito.")
else:
    st.sidebar.markdown('Tu Estado: <span class="free-badge">👤 NO-VIP (FREE)</span>', unsafe_allow_html=True)
    st.sidebar.caption("⚠️ Almacenamiento en Servidor Local: Limitado a 2GB (4GB VIP).")
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

with col_der:
    st.subheader("📊 Centro de Control de Curación Coherente")
    
    if ejecutar:
        if not url_remoto.strip() and not video_subido:
            st.error("❌ Por favor, proporciona una URL de video o arrastra un archivo local.")
        else:
            ADMIN_EMAILS = ["andres3320490@gmail.com"]
            
            if email_usuario in ADMIN_EMAILS:
                limite_gb = 6
            elif es_vip:
                limite_gb = 4
            else:
                limite_gb = 2
                
            limite_bytes = limite_gb * 1024 * 1024 * 1024
            
            if video_subido and video_subido.size > limite_bytes:
                st.error(f"❌ El archivo excede el límite permitido ({limite_gb} GB).")
                st.stop()
                
            if not es_vip and email_usuario not in ADMIN_EMAILS and minutos_consumidos >= 120:
                st.error("❌ Has agotado tus 120 minutos gratuitos.")
                st.stop()

            tarea_id = f"suite_{uuid.uuid4().hex[:12]}"
            st.session_state.tarea_id = tarea_id
            temp_dir = garantizar_entorno_tarea(tarea_id)
            ruta_input = ""
                                
            if video_subido:
                ruta_input = os.path.join(temp_dir, "video_subido.mp4")
                with open(ruta_input, "wb") as buffer:
                    buffer.write(video_subido.getvalue())
                                        
            with st.status("🧠 Extrayendo ganchos narrativos y mapeando clips en servidor local...", expanded=True) as status:
                try:
                    # Adaptación exacta al backend optimizado de tasks.py
                    resultado = pipeline_procesamiento_masivo(
                        tarea_id=tarea_id, 
                        ruta_video_master=ruta_input, 
                        formato=formato_seleccionado, # Envía el string seleccionado directamente
                        con_subtitulos=con_sub, 
                        color_sub_hex="#deff9a", 
                        estilo_subtitulos=plantilla, 
                        url_remoto=url_remoto, 
                        diccionario_manual=diccionario_manual
                    )
                except Exception as ex:
                    resultado = {"status": "error", "mensaje": f"Excepción crítica controlada: {str(ex)}"}
                                        
                if resultado and resultado.get("status") == "success":
                    status.update(label="✨ ¡Procesamiento por lotes completado con éxito!", state="complete", expanded=False)
                    st.session_state.resultado_lote = resultado
                    if not es_vip and email_usuario not in ADMIN_EMAILS:
                        st.session_state.minutos_usados += 5
                else:
                    status.update(label="❌ Error crítico en el pipeline", state="error")
                    mensaje_err = resultado.get("mensaje") if resultado else "Error desconocido (La respuesta retornó vacía)."
                    st.error(mensaje_err)

    if "resultado_lote" in st.session_state and "tarea_id" in st.session_state:
        res = st.session_state.resultado_lote
        tid = st.session_state.tarea_id
        dir_tarea = os.path.join("storage", tid)
                
        if res and "clips" in res:
            st.write(f"🎉 **Hemos descubierto e indexado {len(res['clips'])} fragmentos con alta probabilidad viral:**")
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
                                label=f"📥 Descargar Clip {idx + 1}", data=vf,
                                file_name=c["archivo"], mime="video/mp4", key=f"dl_{idx}"
                            )
                    else:
                        st.error("No se pudo localizar el archivo físico en el almacenamiento local.")
                    st.markdown("</div>", unsafe_allow_html=True)
