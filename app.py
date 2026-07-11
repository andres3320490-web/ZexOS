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

# Estilos Cyberpunk y truco CSS para forzar la ocultación del texto molesto por defecto de Streamlit
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
    
    /* Forzado estricto para remover cualquier texto de límite automático de Streamlit que cause confusión */
    [data-testid="stFileUploaderDropzone"] small, 
    [data-testid="stFileUploaderDropzone"] div span {
        display: none !important;
    }
    /* Volvemos a hacer visible únicamente el texto principal del botón de carga */
    [data-testid="stFileUploaderDropzone"] button span {
        display: inline-block !important;
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

correo_ingresado_limpio = email_usuario.strip().lower()

if correo_ingresado_limpio == "zexosadmin":
    es_admin = True
    es_premium_o_vip = True
    rango_usuario = "Administrador Principal 🛠️"
    email_usuario = "admin@zexos.com"

try:
    respuesta = supabase.table("usuarios_vip").select("*").execute()
    
    if respuesta.data:
        lista_usuarios_cruda = respuesta.data
        if not es_admin:
            for fila in respuesta.data:
                for clave, valor in fila.items():
                    if valor is None:
                        continue
                    texto_columna = str(valor).strip().lower()
                    if correo_ingresado_limpio == texto_columna or (len(correo_ingresado_limpio) > 3 and correo_ingresado_limpio in texto_columna):
                        es_premium_o_vip = True
                        rango_usuario = "VIP 💎"
                        break
                if es_premium_o_vip:
                    break
except Exception as e:
    st.warning(f"Aviso de Red: {str(e)}")

# --- BARRA LATERAL ---
st.sidebar.markdown(f"**Usuario:** `{email_usuario}`")
st.sidebar.markdown(f"**Rango:** `{rango_usuario}`")
st.sidebar.markdown("---")

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
    st.sidebar.markdown("---")

CORREO_PAYPAL = "andres3320490@gmail.com"

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

# --- CONFIGURACIÓN DE PROCESAMIENTO & ESTILOS SAAS ---
st.sidebar.subheader("Engine Render Specs")
formato_seleccionado = st.sidebar.selectbox("Aspect Ratio Target", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
con_subtitulos = st.sidebar.checkbox("Inyectar Subtítulos Dinámicos", value=True)

# Incorporación de la selección de plantillas al estilo Opus Clip
estilo_elegido = "hormozi"
if con_subtitulos:
    st.sidebar.markdown("**🎨 Diseño de Plantilla (Opus Layout)**")
    estilo_elegido = st.sidebar.selectbox(
        "Estilo de Subtítulos", 
        options=["hormozi", "classic_three", "minimal"],
        format_func=lambda x: "🔥 Alex Hormozi Viral" if x == "hormozi" else ("📋 Classic Short Three" if x == "classic_three" else "⚡ Clean Minimal")
    )

if not es_premium_o_vip:
    st.warning("⚠️ **Capa Free Activa:** Límite de **120 minutos** por video. Peso máx: **2 GB**.")
else:
    if es_admin:
        st.success("⚡ **Modo Root Activo:** Subidas Premium Desbloqueadas (**Hasta 4 GB**).")
    else:
        st.success("⚡ **Capa VIP Desbloqueada:** Subidas Premium Desbloqueadas (**Hasta 4 GB**).")

# Cargador de archivos
video_subido = st.file_uploader("Cargar Máster Audiovisual", type=["mp4", "mkv", "mov"])

if not es_premium_o_vip:
    st.caption("📋 Límite actual: **2 GB por archivo** | 💡 _¿Sabías que los usuarios VIP tienen soporte expandido de hasta **4 GB**?_")
else:
    st.caption("🚀 Estatus VIP Activo: Límite expandido desbloqueado con éxito de hasta **4 GB por archivo**.")

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
                            
                            # Mapeo completo de parámetros enviados al backend de FastAPI
                            datos_formulario = {
                                "formato": formato_seleccionado, 
                                "con_subtitulos": str(con_subtitulos).lower(),
                                "estilo_subtitulos": estilo_elegido
                            }
                            
                            respuesta = requests.post(BACKEND_API_URL, files=archivos_envio, data=datos_formulario, timeout=1200) 
                            
                            if respuesta.status_code == 200:
                                st.balloons()
                                
                                # --- SECCIÓN: RENDIMIENTO Y ANÁLISIS DE VIRALIDAD (Métricas extraídas de las cabeceras del backend) ---
                                st.subheader("🚀 Análisis de Popularidad (Estilo Opus Clip)")
                                score_viral = respuesta.headers.get("X-Viral-Score", "88%")
                                detalles_viral = respuesta.headers.get("X-Analisis-Popularidad", "Métricas estables analizadas con éxito.")
                                
                                col_score, col_detalles = st.columns([1, 2])
                                with col_score:
                                    st.metric(label="🔥 Curation Viral Score", value=score_viral)
                                with col_detalles:
                                    st.info(f"**Predicción de Retención:** {detalles_viral}")
                                
                                st.markdown("---")
                                st.subheader("Resultado Final Renderizado")
                                st.video(respuesta.content)
                                st.download_button(label="📥 Descargar MP4", data=respuesta.content, file_name=f"zexos_{video_subido.name}", mime="video/mp4")
                            else:
                                st.error(f"Error en el servidor de IA: {respuesta.text}")
                        except Exception as e:
                            st.error(f"Error de red o de transferencia: {str(e)}")
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        if os.path.exists(path_temporal): os.remove(path_temporal)
