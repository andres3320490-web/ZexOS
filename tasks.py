import os
import sys
import cv2
import torch
import yt_dlp
import requests
import numpy as np
import whisper

# ==============================================================================
# 🛠️ PARCHE CRÍTICO: Configuración de FFmpeg para Servidores Cloud (Streamlit)
# ==============================================================================
if not os.environ.get("IMAGEIO_FFMPEG_EXE"):
    try:
        import imageio_ffmpeg
        os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass

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

# ==============================================================================
# 🔥 MEJORA IA 1: Transcripción de Audio Real (Estilo Opus Clip / Wisecut)
# ==============================================================================
def transcribir_video_por_palabras(ruta_video: str) -> list:
    """Utiliza OpenAI Whisper para mapear palabras con timestamps de forma milimétrica."""
    print(f"📦 Cargando modelo Whisper en {DISPOSITIVO}...")
    modelo = whisper.load_model("base", device=DISPOSITIVO)
    print("🎙️ Transcribiendo audio latente palabra por palabra...")
    resultado = modelo.transcribe(ruta_video, language="es", word_timestamps=True)
    
    segmentos_palabras = []
    for segmento in resultado.get("segments", []):
        for w in segmento.get("words", []):
            segmentos_palabras.append({
                "start": float(w["start"]),
                "end": float(w["end"]),
                "text": w["word"].strip()
            })
    return segmentos_palabras

# ==============================================================================
# 🔥 MEJORA IA 2: Visión Artificial y Multi-Tracking Cinemático de Rostros
# ==============================================================================
def analizar_rostros_multi_tracking(video_path: str, t_inicio: float, t_fin: float):
    """
    Rastrea múltiples rostros simultáneamente, calcula el centro promedio 
    de masa de la escena y suaviza el movimiento por inercia física (paneo fluido).
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC, t_inicio * 1000)
    
    ancho_orig = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
    fotogramas_totales = int((t_fin - t_inicio) * fps)
    centros_fotogramas = []
    
    cascade_humano = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    for f_idx in range(fotogramas_totales):
        ret, frame = cap.read()
        if not ret: break
            
        if f_idx % 4 == 0:  # Muestreo acelerado
            try:
                gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (0, 0), fx=0.25, fy=0.25)
                faces = cascade_humano.detectMultiScale(gray, 1.2, 5)
                
                if len(faces) > 0:
                    # Multi-tracking: baricentro exacto de todos los rostros detectados
                    centros_x = [int((x + w // 2) * 4) for (x, _, w, _) in faces]
                    centro_escena = int(np.mean(centros_x))
                    centros_fotogramas.append(centro_escena)
                else:
                    centros_fotogramas.append(ancho_orig // 2)
            except:
                centros_fotogramas.append(ancho_orig // 2)
        else:
            if centros_fotogramas:
                centros_fotogramas.append(centros_fotogramas[-1])
            else:
                centros_fotogramas.append(ancho_orig // 2)
            
    cap.release()
    
    if not centros_fotogramas: centros_fotogramas = [ancho_orig // 2]
    
    # Algoritmo de suavizado cinemático
    suavizados = []
    pos_actual = centros_fotogramas[0]
    for pos_detectada in centros_fotogramas:
        distancia = pos_detectada - pos_actual
        factor_inercia = 0.60 if abs(distancia) > (ancho_orig // 4) else 0.15
        pos_actual += int(distancia * factor_inercia)
        suavizados.append(pos_actual)
            
    return {"coordenadas": suavizados, "fps": fps}

# ==============================================================================
# 🔥 MEJORA IA 3: Curación de Clips Cortos Adaptativa y Puntuación Viral
# ==============================================================================
def mapear_mejores_clips(segmentos_palabras, duracion_total, max_clips=3):
    """
    Si el video es corto, no lo rompe y procesa el 100%. Si es largo, analiza 
    las métricas de velocidad verbal (WPM) y palabras clave para aislar los mejores ganchos.
    """
    if duracion_total < 25.0 or not segmentos_palabras:
        return [{"start": 0.0, "end": duracion_total, "score": 98, "reasons": ["Ajuste inteligente al 100% de la duración del video."]}]
    
    ventanas = []
    paso_tiempo = 10.0 
    
    for inicio_bloque in np.arange(0, duracion_total - 15.0, paso_tiempo):
        fin_bloque = min(duracion_total, inicio_bloque + 30.0)
        palabras_bloque = [w for w in segmentos_palabras if inicio_bloque <= w["start"] <= fin_bloque]
        
        if len(palabras_bloque) < 5: continue
            
        palabras_clave = 0
        ganchos = []
        for p in palabras_bloque:
            p_limpia = p["text"].lower().strip(".,¡!¿?")
            if p_limpia in PALABRAS_RETENCION:
                palabras_clave += 1
                if p_limpia not in ganchos: ganchos.append(p_limpia)
                
        wpm = (len(palabras_bloque) / (palabras_bloque[-1]["end"] - palabras_bloque[0]["start"])) * 60 if len(palabras_bloque) > 1 else 140
        score = 65 + min(20, palabras_clave * 5) + (13 if 130 <= wpm <= 170 else 5)
        score = min(99, int(score))
        
        reasons = [
            f"⚡ Ritmo conversacional calibrado a {int(wpm)} WPM.",
            f"🔑 Retención maximizada por palabras de impacto: {', '.join(ganchos[:3]) if ganchos else 'Discurso fluido'}."
        ]
        
        ventanas.append({
            "start": palabras_bloque[0]["start"],
            "end": palabras_bloque[-1]["end"],
            "score": score,
            "reasons": reasons
        })
        
    ventanas = sorted(ventanas, key=lambda x: x["score"], reverse=True)
    clips_filtrados = []
    for v in ventanas:
        colision = False
        for c in clips_filtrados:
            if max(v["start"], c["start"]) < min(v["end"], c["end"]):
                colision = True
                break
        if not colision:
            clips_filtrados.append(v)
            if len(clips_filtrados) >= max_clips: break
            
    return clips_filtrados if clips_filtrados else [{"start": 0.0, "end": duracion_total, "score": 85, "reasons": ["Segmento óptimo adaptado."]}]

# ==============================================================================
# 🚀 PIPELINE DE PROCESAMIENTO MULTI-CAPA DEFINITIVO
# ==============================================================================
def pipeline_procesamiento_masivo(tarea_id: str, ruta_video_master: str, formato: str, con_subtitulos: bool, color_sub_hex: str = "#deff9a", estilo_subtitulos: str = "hormozi", url_remoto: str = "", diccionario_manual: str = "") -> dict:
    dir_trabajo = garantizar_entorno_tarea(tarea_id)
    clips_processed = []
    ruta_fuente_absoluta = garantizar_fuente_fisica()
        
    try:
        if url_remoto and url_remoto.strip() != "":
            ruta_video_master = descargar_video_remoto(url_remoto, dir_trabajo)
                    
        if diccionario_manual:
            nuevos_ganchos = {p.strip().lower() for p in diccionario_manual.split(",") if p.strip()}
            PALABRAS_RETENCION.update(nuevos_ganchos)
                    
        clip_completo = VideoFileClip(ruta_video_master)
        duracion_total = clip_completo.duration
            
        segmentos_palabras = []
        if con_subtitulos:
            segmentos_palabras = transcribir_video_por_palabras(ruta_video_master)
                    
        planes_de_corte = mapear_mejores_clips(segmentos_palabras, duracion_total)
        
        for idx, plan in enumerate(planes_de_corte):
            t_ini, t_fin = plan["start"], plan["end"]
            
            chunk = clip_completo[t_ini:t_fin]
            duracion_chunk = chunk.duration
            
            # Reencuadre dinámico inteligente asistido por el Multi-Tracking de la cámara
            if "9:16" in formato or "Short" in formato:
                tracking = analizar_rostros_multi_tracking(ruta_video_master, t_ini, t_fin)
                w_orig, h_orig = chunk.size
                target_w = int(h_orig * (9 / 16))
                
                def transformar_cuadros_tracking(get_frame, t):
                    frame = get_frame(t)
                    indice_f = min(int(t * tracking["fps"]), len(tracking["coordenadas"]) - 1)
                    centro_x = tracking["coordenadas"][indice_f]
                    
                    x1 = centro_x - (target_w // 2)
                    x1 = max(0, min(w_orig - target_w, x1))
                    return frame[:, x1:x1 + target_w]
                
                chunk = chunk.transform(transformar_cuadros_tracking, apply_to=["mask", "audio"])
            
            componentes_chunk = [chunk]
            
            if con_subtitulos:
                for w_info in segmentos_palabras:
                    if t_ini <= w_info["start"] < t_fin:
                        w_start = w_info["start"] - t_ini
                        w_end = w_info["end"] - t_ini
                        
                        # Blindaje matemático matemático anti-desbordamientos en videos cortos
                        techo_maximo = duracion_chunk - 0.02
                        if w_start >= techo_maximo: continue
                            
                        w_start = max(0.0, w_start)
                        w_end = min(techo_maximo, w_end)
                        duracion_sub = max(0.05, w_end - w_start)
                        
                        if (w_start + duracion_sub) > techo_maximo:
                            w_start = max(0.0, techo_maximo - duracion_sub)
                        
                        word_raw = w_info["text"].strip()
                        palabra_limpia = word_raw.lower().strip(".,¡!¿?")
                        
                        emoji = EMOJI_DICTIONARY.get(palabra_limpia, "")
                        texto_final = f"{emoji} {word_raw}" if emoji else word_raw
                        color_actual = color_sub_hex if palabra_limpia in PALABRAS_RETENCION else "#FFFFFF"
                        
                        txt_clip = TextClip(
                            text=texto_final.upper(),
                            font_size=46 if estilo_subtitulos == "hormozi" else 36,
                            color=color_actual,
                            font=ruta_fuente_absoluta,
                            size=(chunk.size[0] - 50, None)
                        )
                        
                        txt_clip = (txt_clip
                                    .with_duration(duracion_sub)
                                    .with_start(w_start)
                                    .with_position(('center', int(chunk.size[1] * 0.70))))
                        
                        componentes_chunk.append(txt_clip)
            
            # SOLUCIÓN CRÍTICA PARA MOVIEPY 2.0.0: Renderizar con duración forzada restrictiva (.with_duration)
            video_final = CompositeVideoClip(componentes_chunk).with_duration(duracion_chunk)
            nombre_archivo = f"clip_{idx + 1}_viral.mp4"
            ruta_salida_clip = os.path.join(dir_trabajo, nombre_archivo)
            
            video_final.write_videofile(ruta_salida_clip, fps=30, codec='libx264', audio_codec='aac', logger=None)
            video_final.close()
            
            clips_processed.append({
                "archivo": nombre_archivo,
                "score": f"{plan['score']}%",
                "reporte": plan["reasons"]
            })
            
        clip_completo.close()
        return {"status": "success", "clips": clips_processed}
        
    except Exception as err:
        return {"status": "error", "mensaje": str(err)}
