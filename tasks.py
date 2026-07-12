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

# Importaciones limpias y protegidas
import cv2
import torch
import yt_dlp
import numpy as np
import whisper
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

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
# 🔥 DESCARGA DIRECTA DESDE OPENAI (BYPASS HUGGING FACE)
# ==============================================================================
def descargar_modelo_whisper_directo(tipo_modelo="base"):
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
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, stream=True, timeout=30)
        if r.status_code == 200:
            with open(ruta_modelo, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)
            return ruta_modelo
    except Exception:
        pass
    return tipo_modelo

def transcribir_video_por_palabras(ruta_video: str) -> list:
    modelo_path = descargar_modelo_whisper_directo("base")
    modelo = whisper.load_model(modelo_path, device=DISPOSITIVO)
    resultado = modelo.transcribe(ruta_video, language="es", word_timestamps=True, fp16=False)
        
    segmentos_palabras = []
    for segmento in resultado.get("segments", []):
        for w in segmento.get("words", []):
            segmentos_palabras.append({
                "start": float(w["start"]),
                "end": float(w["end"]),
                "text": w["word"].strip()
            })
    return segmentos_palabras

def analizar_rostros_multi_tracking(video_path: str, t_inicio: float, t_fin: float):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
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
                scaled_sobel = np.uint8(255 * (abs_sobely / np.max(abs_sobely))) if np.max(abs_sobely) > 0 else reducido
                                
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
        suavizados.append(pos_actual)
                
    return {"coordenadas": suavizados, "fps": fps}

def mapear_mejores_clips(segmentos_palabras, duracion_total, max_clips=3):
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

def construir_bloques_palabras_agrupadas(segmentos_palabras, t_ini, t_fin, max_palabras=3):
    palabras_filtradas = [w for w in segmentos_palabras if t_ini <= w["start"] < t_fin]
    bloques = []
        
    for i in range(0, len(palabras_filtradas), max_palabras):
        grupo = palabras_filtradas[i:i + max_palabras]
        if not grupo: continue # <-- ¡CORREGIDO AQUÍ! (Cambiado de group a grupo)
        bloques.append({
            "start": grupo[0]["start"],
            "end": grupo[-1]["end"],
            "palabras": grupo
        })
    return bloques

def pipeline_procesamiento_masivo(tarea_id: str, ruta_video_master: str, formato: str, con_subtitulos: bool, color_sub_hex: str = "#deff9a", estilo_subtitulos: str = "hormozi", url_remoto: str = "", diccionario_manual: str = "") -> dict:
    dir_trabajo = garantizar_entorno_tarea(tarea_id)
    clips_processed = []
    garantizar_fuente_fisica()
            
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
        
        hex_c = color_sub_hex.lstrip('#')
        rgb_c = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
        bgr_color_destacado = (rgb_c[2], rgb_c[1], rgb_c[0])
                
        for idx, plan in enumerate(planes_de_corte):
            t_ini, t_fin = plan["start"], plan["end"]
            chunk = clip_completo.subclip(t_ini, t_fin)
            
            tracking = analizar_rostros_multi_tracking(ruta_video_master, t_ini, t_fin)
            w_orig, h_orig = chunk.size
            target_w = int(h_orig * (9 / 16)) if ("9:16" in formato or "Short" in formato) else w_orig
            
            bloques_texto = construir_bloques_palabras_agrupadas(segmentos_palabras, t_ini, t_fin) if (con_subtitulos and segmentos_palabras) else []

            def transformar_y_subtitular_cuadros(get_frame, t):
                # .copy() soluciona de raíz el bloqueo de memoria de tipo Read-Only
                frame = get_frame(t).copy()
                t_global = t_ini + t
                
                if "9:16" in formato or "Short" in formato:
                    indice_f = min(int(t * tracking["fps"]), len(tracking["coordenadas"]) - 1)
                    centro_x = tracking["coordenadas"][indice_f]
                    x1 = max(0, min(w_orig - target_w, centro_x - (target_w // 2)))
                    frame = frame[:, x1:x1 + target_w].copy()

                if bloques_texto:
                    for bloque in bloques_texto:
                        if bloque["start"] <= t_global <= bloque["end"]:
                            palabras_texto = []
                            contiene_gancho = False
                            
                            for w in bloque["palabras"]:
                                word_raw = w["text"].strip()
                                palabra_limpia = word_raw.lower().strip(".,¡!¿?")
                                if palabra_limpia in PALABRAS_RETENCION:
                                    contiene_gancho = True
                                emoji = EMOJI_DICTIONARY.get(palabra_limpia, "")
                                palabras_texto.append(f"{emoji}{word_raw}" if emoji else word_raw)
                                                    
                            texto_bloque = " ".join(palabras_texto).upper()
                            
                            fuente = cv2.FONT_HERSHEY_DUPLEX
                            escala = 1.2 if estilo_subtitulos == "hormozi" else 0.9
                            grosor = 3
                            color_texto = bgr_color_destacado if contiene_gancho else (255, 255, 255)
                            
                            tam, _ = cv2.getTextSize(texto_bloque, fuente, escala, grosor)
                            tx = (frame.shape[1] - tam[0]) // 2
                            ty = int(frame.shape[0] * 0.72)
                            
                            cv2.putText(frame, texto_bloque, (tx, ty), fuente, escala, (0, 0, 0), grosor + 4, cv2.LINE_AA)
                            cv2.putText(frame, texto_bloque, (tx, ty), fuente, escala, color_texto, grosor, cv2.LINE_AA)
                            break
                            
                return frame

            chunk = chunk.fl(transformar_y_subtitular_cuadros, keep_duration=True)
            
            nombre_archivo = f"clip_{idx + 1}_viral.mp4"
            ruta_salida_clip = os.path.join(dir_trabajo, nombre_archivo)
                        
            chunk.write_videofile(ruta_salida_clip, fps=30, codec='libx264', audio_codec='aac', logger=None)
            chunk.close()
                        
            clips_processed.append({
                "archivo": nombre_archivo,
                "score": f"{plan['score']}%",
                "reporte": plan["reasons"]
            })
                    
        clip_completo.close()
        return {"status": "success", "clips": clips_processed}
            
    except Exception as err:
        return {"status": "error", "mensaje": str(err)}
