import os
import sys
import subprocess
import requests

# ==============================================================================
# 🚀 PARCHE DE ENTORNO REFORZADO: Vinculación para MoviePy y Whisper
# ==============================================================================
def forzar_instalacion_ffmpeg():
    """Descarga e inyecta un binario estático para que tanto MoviePy como Whisper lo encuentren."""
    try:
        import imageio_ffmpeg
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "imageio-ffmpeg"])
        import imageio_ffmpeg
    
    ruta_binario = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ruta_binario
    
    dir_binario = os.path.dirname(ruta_binario)
    if dir_binario not in os.environ["PATH"]:
        os.environ["PATH"] = dir_binario + os.pathsep + os.environ["PATH"]
        
    return ruta_binario

ruta_ffmpeg_activa = forzar_instalacion_ffmpeg()

try:
    from moviepy.config import change_settings
    change_settings({"FFMPEG_BINARY": ruta_ffmpeg_activa})
except Exception as e:
    print(f"Advertencia al configurar MoviePy de forma interna: {e}")

# Ahora se importan las librerías de forma segura
import cv2
import torch
import yt_dlp
import numpy as np
import whisper
from moviepy import VideoFileClip, TextClip, CompositeVideoClip

# ==============================================================================
# ⚙️ CONFIGURACIÓN DE DISPOSITIVO Y VARIABLES GLOBALES
# ==============================================================================
DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"

EMOJI_DICTIONARY = {
    "dinero": "💰", "fuego": "🔥", "viral": "🔥", "ganar": "🏆",
    "secreto": "🤫", "atención": "🚨", "mira": "👀", "importante": "⚠️",
    "éxito": "🚀", "brutal": "🤯", "cambio": "🔄", "crecer": "📈",
    "error": "❌", "meta": "🎯", "aprender": "🧠", "dinámica": "⚡",
    "locura": "🤪", "redes": "📱", "truco": "💡", "ahora": "⏱️", "nunca": "🚫"
}

PALABRAS_RETENCION = set(EMOJI_DICTIONARY.keys()) | {"jamás", "hoy", "increíble", "revelado", "atención", "importante"}

def garantizar_fuente_fisica() -> str:
    directory_storage = os.path.abspath("storage")
    os.makedirs(directory_storage, exist_ok=True)
    ruta_fuente = os.path.join(directory_storage, "fuente_subtitulos.ttf")
    
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
# 🔥 DESCARGA DIRECTA DESDE OPENAI (BYPASS HUGGING FACE)
# ==============================================================================
def descargar_modelo_whisper_directo(tipo_modelo="base"):
    """Descarga el modelo directamente desde OpenAI si Hugging Face bloquea la petición."""
    urls_openai = {
        "tiny": "https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf779f1bc05673c1d6e34246bb4824feb690f6f00a83e3a1e6ec/tiny.pt",
        "base": "https://openaipublic.azureedge.net/main/whisper/models/ed441706eeac0471e65b24ac180941d769942d9c3a40e9d7729e2e43510db25a/base.pt"
    }
    
    dir_modelos = os.path.expanduser("~/.cache/whisper")
    os.makedirs(dir_modelos, exist_ok=True)
    ruta_modelo = os.path.join(dir_modelos, f"{tipo_modelo}.pt")
    
    if os.path.exists(ruta_modelo) and os.path.getsize(ruta_modelo) > 100000000:
        return ruta_modelo
        
    url = urls_openai.get(tipo_modelo, urls_openai["base"])
    print(f"📥 Descargando modelo {tipo_modelo} directamente desde los servidores de OpenAI...")
    
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, stream=True, timeout=30)
        if r.status_code == 200:
            with open(ruta_modelo, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)
            print("✅ Descarga directa completada exitosamente.")
            return ruta_modelo
    except Exception as e:
        print(f"Error en descarga directa: {e}. Se intentará el método por defecto.")
    
    return tipo_modelo

def transcribir_video_por_palabras(ruta_video: str) -> list:
    modelo_path = descargar_modelo_whisper_directo("base")
    
    print(f"📦 Cargando modelo Whisper en {DISPOSITIVO}...")
    modelo = whisper.load_model(modelo_path, device=DISPOSITIVO)
    print("🎙️ Transcribiendo audio latente palabra por palabra...")
    
    resultado = modelo.transcribe(ruta_video, language="es", word_timestamps=True, fp16=False)
    
    segmentos_palabras = []
    for segmento in resultado.get("segments", []):
        for w in segmento.get("words", []):
            segmentos_palabras.append({
                "start": float(w["start"]),
                "end": float(w["end"]),
                "text": str(w["word"]).strip()
            })
    return segments_palabras

def analizar_rostros_multi_tracking(video_path: str, t_inicio: float, t_fin: float):
    cap = cv2.VideoCapture(video_path)
    fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC, t_inicio * 1000)
    
    ancho_orig = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
    fotogramas_totales = int((t_fin - t_inicio) * fps)
    centros_fotogramas = []

    for f_idx in range(fotogramas_totales):
        ret, frame = cap.read()
        if not ret: break
            
        if f_idx % 4 == 0:  
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                reducido = cv2.resize(gray, (0, 0), fx=0.25, fy=0.25)
                
                sobely = cv2.Sobel(reducido, cv2.CV_64F, 0, 1, ksize=5)
                abs_sobely = np.absolute(sobely)
                max_sobel = np.max(abs_sobely)
                scaled_sobel = np.uint8(255 * (abs_sobely / max_sobel)) if max_sobel > 0 else reducido
                
                column_sums = np.sum(scaled_sobel, axis=0)
                centro_estimado = int(np.argmax(column_sums) * 4)
                
                if 0 < centro_estimado < ancho_orig:
                    centros_fotogramas.append(centro_estimado)
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
    
    suavizados = []
    pos_actual = centros_fotogramas[0]
    for pos_detectada in centros_fotogramas:
        distancia = pos_detectada - pos_actual
        factor_inercia = 0.50 if abs(distancia) > (ancho_orig // 4) else 0.12
        pos_actual += int(distancia * factor_inercia)
        suavizados.append(int(pos_actual))
            
    return {"coordenadas": suavizados, "fps": fps}

def mapear_mejores_clips(segmentos_palabras, duracion_total, max_clips=3):
    if duracion_total < 25.0 or not segmentos_palabras:
        return [{"start": 0.0, "end": float(duracion_total), "score": 98, "reasons": ["Ajuste inteligente al 100% de la duración del video."]}]
    
    ventanas = []
    paso_tiempo = 10.0 
    
    inicio_bloque = 0.0
    while inicio_bloque < (duracion_total - 15.0):
        fin_bloque = min(float(duracion_total), inicio_bloque + 30.0)
        palabras_bloque = [w for w in segmentos_palabras if inicio_bloque <= w["start"] <= fin_bloque]
        
        if len(palabras_bloque) < 5:
            inicio_bloque += paso_tiempo
            continue
            
        palabras_clave = 0
        ganchos = []
        for p in palabras_bloque:
            p_limpia = p["text"].lower().strip(".,¡!¿?")
            if p_limpia in PALABRAS_RETENCION:
                palabras_clave += 1
                if p_limpia not in ganchos: ganchos.append(p_limpia)
                
        duracion_real_bloque = palabras_bloque[-1]["end"] - palabras_bloque[0]["start"]
        wpm = (len(palabras_bloque) / duracion_real_bloque) * 60 if duracion_real_bloque > 0.1 else 140
        
        score = 65 + min(20, palabras_clave * 5) + (13 if 130 <= wpm <= 170 else 5)
        score = min(99, int(score))
        
        reasons = [
            f"⚡ Ritmo conversacional calibrado a {int(wpm)} WPM.",
            f"🔑 Retención maximizada por palabras de impacto: {', '.join(ganchos[:3]) if ganchos else 'Discurso fluido'}."
        ]
        
        ventanas.append({
            "start": float(palabras_bloque[0]["start"]),
            "end": float(palabras_bloque[-1]["end"]),
            "score": int(score),
            "reasons": reasons
        })
        inicio_bloque += paso_tiempo
        
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
            
    return clips_filtrados if clips_filtrados else [{"start": 0.0, "end": float(duracion_total), "score": 85, "reasons": ["Segmento óptimo adaptado."]}]

def construir_bloques_palabras_agrupadas(segmentos_palabras, t_ini, t_fin, max_palabras=3):
    palabras_filtradas = [w for w in segmentos_palabras if t_ini <= w["start"] < t_fin]
    bloques = []
    
    for i in range(0, len(palabras_filtradas), max_palabras):
        grupo = palabras_filtradas[i:i + max_palabras]
        if not grupo: continue
        bloques.append({
            "start": float(grupo[0]["start"]),
            "end": float(grupo[-1]["end"]),
            "palabras": grupo  
        })
    return bloques

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
        duracion_total = float(clip_completo.duration)
            
        segmentos_palabras = []
        if con_subtitulos:
            segmentos_palabras = transcribir_video_por_palabras(ruta_video_master)
                    
        planes_de_corte = mapear_mejores_clips(segmentos_palabras, duracion_total)
        
        for idx, plan in enumerate(planes_de_corte):
            t_ini, t_fin = float(plan["start"]), float(plan["end"])
            
            # --- CORRECCIÓN CLAVE MOVIEPY v2.0 ---
            chunk = clip_completo.slice(t_ini, t_fin)
            duracion_chunk = float(chunk.duration)
            
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
            
            if con_subtitulos and segmentos_palabras:
                bloques_texto = construir_bloques_palabras_agrupadas(segmentos_palabras, t_ini, t_fin)
                
                for bloque in bloques_texto:
                    b_start = float(bloque["start"] - t_ini)
                    b_end = float(bloque["end"] - t_ini)
                    
                    techo_maximo = duracion_chunk - 0.02
                    if b_start >= techo_maximo: continue
                    
                    b_start = max(0.0, b_start)
                    b_end = min(techo_maximo, b_end)
                    duracion_bloque = max(0.08, b_end - b_start)
                    
                    palabras_texto = []
                    for w in bloque["palabras"]:
                        word_raw = str(w["text"]).strip()
                        palabra_limpia = word_raw.lower().strip(".,¡!¿?")
                        emoji = EMOJI_DICTIONARY.get(palabra_limpia, "")
                        palabras_texto.append(f"{emoji} {word_raw}" if emoji else word_raw)
                        
                    texto_completo_bloque = " ".join(palabras_texto).upper()
                    
                    contiene_gancho = any(str(w["text"]).lower().strip(".,¡!¿?") in PALABRAS_RETENCION for w in bloque["palabras"])
                    color_bloque = color_sub_hex if contiene_gancho else "#FFFFFF"
                    
                    txt_clip = TextClip(
                        text=texto_completo_bloque,
                        font_size=44 if estilo_subtitulos == "hormozi" else 34,
                        color=color_bloque,
                        font=ruta_fuente_absoluta,
                        size=(chunk.size[0] - 60, None)
                    )
                    
                    txt_clip = (txt_clip
                                .with_duration(duracion_bloque)
                                .with_start(b_start)
                                .with_position(('center', int(chunk.size[1] * 0.70))))
                    
                    componentes_chunk.append(txt_clip)
            
            video_final = CompositeVideoClip(componentes_chunk).with_duration(duracion_chunk)
            nombre_archivo = f"clip_{idx + 1}_viral.mp4"
            ruta_salida_clip = os.path.join(dir_trabajo, nombre_archivo)
            
            video_final.write_videofile(ruta_salida_clip, fps=30, codec='libx264', audio_codec='aac', logger=None)
            video_final.close()
            
            clips_processed.append({
                "archivo": nombre_archivo,
                "score": int(plan["score"]),
                "reporte": plan["reasons"]
            })
            
        clip_completo.close()
        return {"status": "success", "clips": clips_processed}
        
    except Exception as err:
        return {"status": "error", "mensaje": str(err)}
