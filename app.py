import subprocess
import sys

# --- ENMASCARAMIENTO Y REPARACIÓN GLOBAL DE PYTHON 3.12 ---
try:
    import pkg_resources
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools"])
    import pkg_resources

import os
import uuid
import streamlit as st
from streamlit_cookies_controller import CookieController

# Asegurar importación limpia del módulo local tasks.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tasks import garantizar_entorno_tarea, pipeline_procesamiento_masivo

cookie_controller = CookieController()

# --- CONFIGURACIÓN VISUAL ORIGINAL ---
st.set_page_config(page_title="ZexOS AI Studio", page_icon="⚡", layout="wide")

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

# --- SIMULACIÓN DE LA BASE DE DATOS (SUB-BASE PREVIA) ---
if "subbase_usuarios" not in st.session_state:
    st.session_state.subbase_usuarios = {
        "admin@zexos.com": {"vip": True, "minutos_usados": 0},
    }
if "cuentas_creadas_ip" not in st.session_state:
    st.session_state.cuentas_creadas_ip = 1  # Simulación de contador de cuentas locales

saved_email = cookie_controller.get("zexos_user_email")
email_usuario = st.text_input("Ingresar cuenta vinculada:", value=saved_email if saved_email else "").strip()

if not email_usuario:
    st.info("💡 Introduce tu dirección de acceso seguro para iniciar los clústeres de renderizado.")
    st.stop()

# --- LÓGICA DE CONTROL DE CUENTAS (MÁXIMO 3 PARA NO-VIP) ---
if email_usuario not in st.session_state.subbase_usuarios:
    if st.session_state.cuentas_creadas_ip >= 3:
        st.error("❌ Has alcanzado el límite máximo de 3 cuentas permitidas para usuarios No-VIP en esta infraestructura.")
        st.info("💡 Para registrar más cuentas o remover este límite, adquiere el plan VIP.")
        
        url_paypal_bloqueo = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=andres3320490@gmail.com&item_name=ZexOS%20AI%20Studio%20VIP&amount=10.00&currency_code=USD"
        st.markdown(f'<a href="{url_paypal_bloqueo}" target="_blank"><button style="background-color:#deff9a; color:#05070a; border:none; padding:12px; border-radius:10px; font-weight:bold; width:100%; cursor:pointer;">🌟 DESBLOQUEAR ACCESO VIP ($10/mes)</button></a>', unsafe_allow_html=True)
        st.stop()
    else:
        st.session_state.subbase_usuarios[email_usuario] = {"vip": False, "minutos_usados": 0}
        st.session_state.cuentas_creadas_ip += 1

cookie_controller.set("zexos_user_email", email_usuario)

# Obtener estado actual del usuario desde la sub-base
es_vip = st.session_state.subbase_usuarios[email_usuario]["vip"]
minutos_consumidos = st.session_state.subbase_usuarios[email_usuario]["minutos_usados"]

# --- SIDEBAR ORIGINAL CON AGREGADOS DE ESTADO VIP & PAYPAL ---
st.sidebar.subheader("🛠️ Panel de Configuración Experta")

if es_vip:
    st.sidebar.markdown('Tu Estado: <span class="vip-badge">👑 VIP PREMIUM</span>', unsafe_allow_html=True)
    st.sidebar.caption("⚡ Almacenamiento en Hugging Face: Máximo 4GB habilitado.")
    st.sidebar.caption("⏱️ Tiempo de procesamiento: Infinito.")
else:
    st.sidebar.markdown('Tu Estado: <span class="free-badge">👤 NO-VIP (FREE)</span>', unsafe_allow_html=True)
    st.sidebar.caption("⚠️ Almacenamiento en Hugging Face: Limitado a 2GB (4GB VIP).")
    st.sidebar.caption(f"⏱️ Minutos Disponibles: {120 - minutos_consumidos} de 120 min.")
    
    st.sidebar.markdown("---")
    st.sidebar.write("🏆 **Mejora a VIP por solo $10/mes:**")
    url_paypal_sidebar = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=andres3320490@gmail.com&item_name=ZexOS%20AI%20Studio%20VIP&amount=10.00&currency_code=USD"
    st.sidebar.markdown(f'<a href="{url_paypal_sidebar}" target="_blank"><button style="background-color:#deff9a; color:#05070a; border:none; padding:10px; border-radius:8px; font-weight:bold; width:100%; cursor:pointer;">💳 Pagar $10 con PayPal</button></a>', unsafe_allow_html=True)
    st.sidebar.caption("Envía el comprobante para activación inmediata.")
    st.sidebar.markdown("---")

formato = st.sidebar.selectbox("Geometría del Cuadro", options=["Short Vertical (9:16)", "Cinema Traditional (16:9)"])
