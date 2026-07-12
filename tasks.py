import os
import sys
import cv2
import torch
import yt_dlp
import requests
import numpy as np
import whisper

# ==============================================================================
# 🛠️ PARCHE INTEGRAL DEFINITIVO: Configuración Forzada de FFmpeg en MoviePy 2.0
# ==============================================================================
try:
    import imageio_ffmpeg
    ruta_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ruta_ffmpeg
    
    # Forzar directamente la configuración interna de MoviePy 2.0
    from moviepy.config import change_settings
    change_settings({"FFMPEG_BINARY": ruta_ffmpeg})
except Exception as e:
    print(f"Advertencia al configurar FFmpeg: {e}")

# Importación directa y segura para MoviePy 2.0.0
from moviepy import VideoFileClip, TextClip, CompositeVideoClip

DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"

# Diccionario inteligente para la inyección automática de Emojis de Retención
EMOJI_DICTIONARY = {
    "dinero": "💰", "fuego": "🔥", "viral": "🔥", "ganar": "🏆",
    "secreto": "🤫", "atención": "🚨", "mira": "👀", "importante": "⚠️",
    "éxito": "🚀", "brutal": "🤯", "cambio": "🔄", "crecer": "📈",
    "error": "❌", "meta": "🎯", "aprender": "🧠", "dinámica": "⚡",
    "locura": "🤪", "redes": "📱", "truco": "💡", "ahora": "⏱️", "nunca": "🚫"
}

PALABRAS_RETENCION = set(EMOJI_DICTIONARY.keys()) | {"jamás", "hoy", "increíble", "revelado", "atención", "importante"}

def garantizar_fuente_fisica() -> str:
    """Descarga una fuente TTF tipográfica real para evitar problemas con fuentes del sistema."""
    directorio_storage = os.path.abspath("storage")
    os.makedirs(directorio_storage, exist_ok=True)
    ruta_fuente = os.path.join(directorio_storage, "fuente_subtitulos.ttf")
    
    if os.path.exists(ruta_fuente) and os.path.getsize(ruta_fuente) > 10000:
        return ruta_fuente

    url_fuente = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
    try:
        respuesta = requests.get(url_fuente, timeout=15, stream=True)
        if respuesta.status_code == 200:
            with open(ruta_fuente, "wb") as archivo:
                for chunk in respuesta.iter_content(chunk_size=8192):
                    archivo.write(chunk)
    except Exception:
        pass
    return ruta_fuente

def garantizar_entorno_tarea(tarea_id: str) -> str:
    ruta_tarea = os.path.join("storage", tarea_id)
    os.makedirs(ruta_tarea, exist_ok=True)
    return ruta_tarea

def descargar_video_remoto(url: str, ruta_salida_dir: str) -> str:
    opciones = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(ruta_salida_dir, 'video_master_%(id)s.%(ext)s'),
        'silent': True, 
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(opciones) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# =================================
