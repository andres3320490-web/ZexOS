# app.py
import os
import streamlit as st
import requests
from moviepy import VideoFileClip

# 1. Configuración de pantalla con estética SaaS Premium
st.set_page_config(
    page_title="ZexOS AI Studio Enterprise",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inyección de CSS Limpio con tu paleta Flúor (#deff9a)
st.markdown("""
    <style>
    .stApp { background-color: #0A0D14; color: #E2E8F0; }
    
    /* Títulos y textos destacados en flúor */
    h1, h2, h3, .stMarkdown strong { color: #deff9a !important; }
    
    /* Botón principal flúor estilo Cyberpunk */
    .stButton>button { 
        width: 100%; 
        background-color: #deff9a !important; 
        color: #0A0D14 !important; 
        font-weight: bold !important;
        border-radius: 8px !important; 
        border: none !important;
        box-shadow: 0px 4px 15px rgba(222, 255, 154, 0.3);
        transition: transform 0.2s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    
    /* Tarjeta lateral de anuncios */
    .ad-card {
        background-color: #121620;
        border: 1px solid #deff9a;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0px 4px 10px rgba(222, 255, 154, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# 3. Dirección de tu Servidor de IA en Hugging Face
# Asegúrate de que entre las comillas esté TU enlace directo terminando en /procesar
BACKEND_API_URL = "https://vzex-zexiastudio.hf.space/procesar"

# --- LOGIN SIMULADO PARA SEPARAR SESIONES ---
if "user_logged" not in st.session_state:
    st.session_state.user_logged = None

if not st.session_state.user_logged:
    st.title("⚡ ZexOS AI Studio Core")
    st.subheader("🔑 Acceso al Panel SaaS")
    email = st.text_input("Correo electrónico del suscriptor")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Inicializar Nodo Cloud"):
        if email and len(password) >= 6:
            st.session_state.user_logged = email
            st.rerun()
        else:
            st.error("Por favor, introduce credenciales válidas (mínimo 6 caracteres).")
    st.stop()

# --- INSTANCIA ACTIVA: INTERFAZ PRINCIPAL ---
st.title("🚀 ZexOS AI Studio Core — Cloud SaaS Engine")
st.caption("Cargue bruto audiovisual. El sistema ejecutará el tracking predictivo, elipsis de silencios y normalización en servidores remotos.")

# --- BARRA LATERAL (Sidebar) + CONFIGURACIÓN + ANUNCIOS ---
st.sidebar.markdown(f"**Usuario:** `{st.session_state.user_logged}`")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.user_logged = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Engine Render Specs")

formato_seleccionado = st.sidebar.selectbox(
    "Aspect Ratio Target",
    options=["Short Vertical (9:16) - Opus Optimized", "Cinema Traditional (16:9)"],
    index=0
)

con_subtitulos = st.sidebar.checkbox("Inyectar Subtítulos Dinámicos (Word-Level)", value=True)

# 📢 SECCIÓN DE ANUNCIOS MONETIZABLE (HTML NATIVO)
st.sidebar.markdown("---")
st.sidebar.subheader("📢 Patrocinadores")

html_anuncio = """
<div class="ad-card">
    <a href="https://tu-enlace-de-afiliado.com" target="_blank" style="text-decoration: none; color: #E2E8F0;">
        <p style="margin: 0; font-size: 14px; font-weight: bold; color: #deff9a;">🎬 ¿Música sin Copyright?</p>
        <p style="margin: 6px 0 0 0; font-size: 11px; color: #A0AEC0;">Consigue 30 días GRATIS en la mejor librería para creadores haciendo clic aquí.</p>
    </a>
</div>
"""
st.sidebar.html(html_anuncio)

# --- CUERPO PRINCIPAL: SUBIDA Y CONTROL DE SEGURIDAD ---
st.markdown("---")
st.warning("⚠️ **Restricción de la capa Free:** Máximo **60 segundos** por video para evitar saturación o cortes por tiempo de espera (Timeout) en la nube.")

video_subido = st.file_uploader("Cargar Máster Audiovisual", type=["mp4", "mkv", "mov"])

if video_subido:
    # Generamos un archivo temporal rápido para validar la duración sin colapsar tu memoria RAM
    path_temporal = "validando_duracion.mp4"
    with open(path_temporal, "wb") as f:
        f.write(video_subido.getvalue())
        
    try:
        # Abrimos el video con MoviePy para leer la duración real
        clip_prueba = VideoFileClip(path_temporal)
        duracion_real = clip_prueba.duration
        clip_prueba.close()
        
        # Eliminamos el temporal inmediatamente del disco duro
        if os.path.exists(path_temporal):
            os.remove(path_temporal)
            
        st.write(f"⏱️ Duración del archivo cargado: `{duracion_real:.2f} segundos`")
        
        # 🛡️ FILTRO ESTRICTO ANTICRISIS DE SERVIDOR
        if duracion_real > 60.0:
            st.error(f"❌ Tu video dura {duracion_real:.1f}s. Has superado el límite de 60 segundos de la cuenta gratuita.")
            st.info("💡 **¿Necesitas procesar videos de hasta 2 horas?** Actualiza tu suscripción al Plan Pro ilimitado mediante Lemon Squeezy.")
        else:
            st.success("✅ Metraje verificado con éxito. El tamaño se encuentra dentro del rango óptimo para los servidores de IA.")
            
            # Columnas para organizar el espacio visual
            col_preview, col_render = st.columns([1, 1])
            
            with col_preview:
                st.subheader("Source Input Preview")
                st.video(video_subido)
                
            with col_render:
                st.subheader("Orquestación del Render Cloud")
                
                if st.button("EJECUTAR COMPILACIÓN MULTIMODAL AUTOMÁTICA"):
                    with st.spinner("Inicializando Workers de GPU remotos y procesando timestamps con Whisper..."):
                        try:
                            # Preparamos el paquete de datos binarios para enviar por red
                            archivos_envio = {
                                "file": (video_subido.name, video_subido.getvalue(), video_subido.type)
                            }
                            datos_formulario = {
                                "formato": formato_seleccionado,
                                "con_subtitulos": str(con_subtitulos).lower()
                            }
                            
                            # Hacemos la llamada HTTP POST hacia Hugging Face
                            respuesta = requests.post(
                                BACKEND_API_URL, 
                                files=archivos_envio, 
                                data=datos_formulario, 
                                timeout=600  # 10 minutos máximos de espera en red
                            )
                            
                            if respuesta.status_code == 200:
                                st.balloons()
                                st.success("¡Pipeline ejecutado correctamente por la infraestructura de IA!")
                                
                                # Mostramos el video procesado devuelto por la API
                                st.subheader("Resultado Final Distribuible")
                                st.video(respuesta.content)
                                
                                st.download_button(
                                    label="📥 Descargar Máster MP4",
                                    data=respuesta.content,
                                    file_name=f"zexos_editado_{video_subido.name}",
                                    mime="video/mp4"
                                )
                            else:
                                st.error(f"Fallo crítico en el clúster de renderizado: {respuesta.text}")
                                
                        except Exception as error_red:
                            st.error(f"Error de enlace de red con los servidores de Hugging Face: {str(error_red)}")
                            st.info("Asegúrate de que tu espacio en Hugging Face haya terminado de compilar y esté en estado 'Running'.")
                            
    except Exception as e:
        st.error(f"Error al analizar la estructura multimedia del archivo: {str(e)}")
        if os.path.exists(path_temporal):
            os.remove(path_temporal)
