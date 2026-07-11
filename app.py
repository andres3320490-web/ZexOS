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
        
    # 2. Validación de Límites por IP vía Supabase
    try:
        res_ip = supabase.table("registro_ips").select("*").eq("ip_address", user_ip).execute()
        cuentas_asociadas = [fila["email"] for fila in res_ip.data] if res_ip.data else []
        
        if correo_ingresado_limpio not in cuentas_asociadas:
            if len(cuentas_asociadas) >= 2:
                st.error(f"⛔ **LÍMITE DE IP EXCEDIDO:** Esta dirección IP (`{user_ip}`) ya ha alcanzado el máximo de 2 cuentas permitidas para el plan gratuito.")
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
    st.sidebar.markdown('<div class="pro-box"><span style="font-size: 14px;">💎 <b>UPGRADE A VIP RENDER</b></span><br><span style="color: #deff9a; font-size: 20
