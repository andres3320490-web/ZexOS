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

# Estilos Cyberpunk y truco CSS para ocultar el límite por defecto de 200MB de Streamlit
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
    .admin-box {
        background-color: #1a1018; border: 1px solid #ff007f; padding: 10px; border-radius: 8px; margin-bottom: 15px;
    }
    /* Oculta la etiqueta por defecto de límite de tamaño (200MB per file) para evitar confusiones */
    [data-testid="stFileUploaderDropzone"] small {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

BACKEND_API_URL = "https://vzex-zexiastudio.hf.space/procesar"

st.title("🚀 ZexOS AI Studio Core")

# --- PASO 0: IDENTIFICACIÓN DE USUARIO ---
st.subheader("📥 Identificación de Usuario")
email_usuario = st.text_input("Introduce tu correo electrónico para iniciar el entorno:", placeholder="ejemplo@correo.com o Clave Admin").strip()

if not email_usuario:
    st.info("💡 Introduce tu correo electrónico arriba para desbloquear el panel de control.")
    st.stop()

# --- VERIFICACIÓN DE RANGO / ADMIN (SISTEMA DE COINCIDENCIA ABSOLUTA) ---
es_premium_o_vip = False
es_admin = False
rango_usuario = "Gratuito"
lista_usuarios_cruda = []

# Limpiamos la entrada de la interfaz
correo_ingresado_limpio = email_usuario.strip().lower()

if correo_ingresado_limpio == "zexosadmin":
    es_admin = True
    es_premium_o_vip = True
    rango_usuario = "Administrador Principal 🛠️"
    email_usuario = "admin@zexos.com"

try:
    # Traemos todos los registros de la tabla
    respuesta = supabase.table("usuarios_vip").select("*").execute()
    
    if respuesta.data:
        lista_usuarios_cruda = respuesta.data
        
        # Si no es la clave maestra admin, escaneamos celda por celda
        if not es_admin:
            for fila in respuesta.data:
                for clave, valor in fila.items():
                    if valor is None:
                        continue
                    
                    texto_columna = str(valor).strip().lower()
                    
                    # Comparamos si coincide exactamente o si el valor ingresado está contenido dentro del campo
                    if correo_ingresado_limpio == texto_columna or (len(correo_ingresado_limpio) > 3 and correo_ingresado_limpio in texto_columna):
                        es_premium_o_vip = True
                        rango_usuario = "VIP 💎"  # Modificado a petición para mostrar solo VIP
                        break
                if es_premium_o_vip:
                    break
except Exception as e:
    st.warning(f"Aviso de Red: {str(e)}")

# --- BARRA LATERAL ---
st.sidebar.markdown(f"**Usuario:** `{email_usuario}`")
st.sidebar.markdown(f"**Rango:** `{rango_usuario}`")
st.sidebar.markdown("---")

# --- PANEL EXCLUSIVO DE ADMINISTRADOR ---
if es_admin:
    st.sidebar.markdown("""
    <div class="admin-box">
        <span style="color: #ff007f; font-weight: bold;">⚡ CONSOLA DE ADMINISTRACIÓN</span>
    </div>
    """, unsafe_allow_html=True)
    
    total_vip = len(lista_usuarios_cruda)
    st.sidebar.metric(label="👥 Total Clientes VIP Activos", value=total_vip)
    
    st.sidebar.markdown("**📍 1. Monitor de Usuarios VIP:**")
    for idx, fila in enumerate(lista_usuarios_cruda):
        valores = [str(v) for v in fila.values() if v is not None and str(v).lower() != 'id']
        correo_mostrar = valores[0] if valores else f"ID {idx+1}"
        st.sidebar.text(f"• {correo_mostrar}")
        
    st.sidebar.markdown("**📍 2. Sistema de Control:**")
    st.sidebar.caption("Para dar de alta nuevos clientes que paguen por PayPal, ingresa directamente a tu dashboard web de Supabase.")
    
    st.sidebar.markdown("**📍 3. Estado de la Red:**")
    st.sidebar.success("Conexión con Supabase: ONLINE")
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
    
    st.sidebar.info("⏳ **Activación del servicio:** Tras completar tu pago en PayPal, el estado Pro se validará y activará en tu cuenta en un lapso máximo de **24 horas**.")
    st.sidebar.markdown("---")

# --- PROCESAMIENTO MULTIMEDIA & PERSONALIZACIÓN ESTÉTICA ---
st.sidebar.subheader("Engine Render Specs")
formato_seleccionado = st.sidebar.selectbox("Aspect Ratio Target", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
con_subtitulos = st.sidebar.checkbox("Inyectar Subtítulos Dinámicos", value=True)

fuente_seleccionada = "Impact"
color_seleccionado = "#FFFFFF"

if con_subtitulos:
    st.sidebar.markdown("**🎨 Estilo de Subtítulos**")
    fuente_seleccionada = st.sidebar.selectbox(
        "Tipografía", 
        options=["Impact", "Arial Black", "Montserrat-Bold", "Bangers", "TheBoldFont"]
    )
    color_seleccionado = st.sidebar.color_picker("Color del Texto Principal", "#deff9a")

if not es_premium_o_vip:
    st.warning("⚠️ **Capa Free Activa:** Límite de **120 minutos** por video. Peso máx: **2 GB**.")
else:
    if es_admin:
        st.success("⚡ **Modo Root Activo:** Subidas Premium Desbloqueadas (**Hasta 4 GB**).")
    else:
        st.success("⚡ **Capa VIP Desbloqueada:** Subidas Premium Desbloqueadas (**Hasta 4 GB**).")

# Subidor de archivos
video_subido = st.file_uploader("Cargar Máster Audiovisual", type=["mp4", "mkv", "mov"])

if video_subido:
    peso_archivo_bytes = video_subido.size
    peso_max_free = 2048 * 1024 * 1024     
    peso_max_premium = 4096 * 1024 * 1024  
    
    if not es_premium_o_vip and peso_archivo_bytes > peso_max_free:
        st.error(f"❌ El archivo pesa {(peso_archivo_bytes / (1024*1024)):.1f} MB. Has superado el límite de 2 GB de la cuenta gratuita.")
        st.stop()
    elif es_premium_o_vip and peso_archivo_bytes > peso_max_premium:
        st.error(f"❌ El archivo supera los 4 GB permitidos ({ (peso_archivo_bytes / (1024*1024*1024)):.2f} GB detectados).")
        st.stop()
        
    path_temporal = "validando_duracion.mp4"
    with open(path_temporal, "wb") as f:
        f.write(video_subido.getvalue())
        
    try:
        clip_prueba = VideoFileClip(path_temporal)
        duracion_real = clip_prueba.duration
        clip_prueba.close()
        if os.path.exists(path_temporal): os.remove(path_temporal)
            
        st.write(f"⏱️ Duración detectada: `{duracion_real:.2f} segundos` | Peso: `{ (peso_archivo_bytes / (1024*1024)):.1f} MB`")
        
        if duracion_real > 7200.0 and not es_premium_o_vip:
            st.error(f"❌ Tu video dura {duracion_real:.1f}s. Has superado el límite de 120 minutos de la cuenta gratuita.")
        else:
            st.success("✅ Estructura multimedia óptima para el renderizado.")
            col_preview, col_render = st.columns([1, 1])
            with col_preview:
                st.subheader("Source Preview")
                st.video(video_subido)
            with col_render:
                st.subheader("Orquestación Cloud")
                if st.button("EJECUTAR COMPILACIÓN"):
                    with st.spinner("Procesando en la nube con IA... (Archivos grandes pueden demorar varios minutos)"):
                        try:
                            archivos_envio = {"file": (video_subido.name, video_subido.getvalue(), video_subido.type)}
                            
                            datos_formulario = {
                                "formato": formato_seleccionado, 
                                "con_subtitulos": str(con_subtitulos).lower(),
                                "fuente": fuente_seleccionada,
                                "color": color_seleccionado
                            }
                            
                            respuesta = requests.post(BACKEND_API_URL, files=archivos_envio, data=datos_formulario, timeout=1200) 
                            if respuesta.status_code == 200:
                                st.balloons()
                                st.subheader("Resultado Final")
                                st.video(respuesta.content)
                                st.download_button(label="📥 Descargar MP4", data=respuesta.content, file_name=f"zexos_{video_subido.name}", mime="video/mp4")
                            else:
                                st.error(f"Error en el servidor de IA: {respuesta.text}")
                        except Exception as e:
                            st.error(f"Error de red o de transferencia: {str(e)}")
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        if os.path.exists(path_temporal): os.remove(path_temporal)
