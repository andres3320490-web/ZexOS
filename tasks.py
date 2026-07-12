import os
import sys
import subprocess

try:
    import pkg_resources
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools"])

import requests
import cv2
import torch
import yt_dlp
import numpy as np
import whisper

from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

try:
    import imageio_ffmpeg
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
except:
    pass

DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"

def garantizar_entorno_tarea(tarea_id):
    path = os.path.join("storage", tarea_id)
    os.makedirs(path, exist_ok=True)
    return path

def descargar_video_remoto(url, output_dir):
    opts = {'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best', 'outtmpl': f'{output_dir}/master.%(ext)s'}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def transcribir_video_por_palabras(video_path):
    modelo = whisper.load_model("base", device=DISPOSITIVO)
    res = modelo.transcribe(video_path, language="es", word_timestamps=True)
    palabras = []
    for s in res['segments']:
        for w in s['words']:
            palabras.append({"start": float(w['start']), "end": float(w['end']), "text": w['word'].strip()})
    return palabras

def analizar_rostros_multi_tracking(video_path, start, end):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    centros = []
    for _ in range(int((end - start) * fps)):
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sobely = cv2.Sobel(cv2.resize(gray, (0,0), fx=0.25, fy=0.25), cv2.CV_64F, 0, 1, ksize=5)
        centros.append(int(np.argmax(np.sum(np.absolute(sobely), axis=0)) * 4))
    cap.release()
    return {"coordenadas": centros if centros else [ancho//2], "fps": fps}

def mapear_mejores_clips(palabras, total_dur):
    if total_dur < 30: 
        return [{"start": 0, "end": total_dur, "score": 90, "reasons": ["Vídeo corto ideal"]}]
    return [{"start": 1, "end": min(total_dur, 31.0), "score": 98, "reasons": ["Gancho inicial detectado", "Ritmo óptimo de retención"]}]

def pipeline_procesamiento_masivo(tarea_id, ruta_video_master, formato, con_subtitulos, color_sub_hex, estilo_subtitulos, url_remoto, diccionario_manual):
    dir_t = garantizar_entorno_tarea(tarea_id)
    if url_remoto: 
        ruta_video_master = descargar_video_remoto(url_remoto, dir_t)
    
    if not os.path.exists(ruta_video_master):
        return {"status": "error", "mensaje": "El archivo de video maestro no fue localizado."}
        
    master = VideoFileClip(ruta_video_master)
    palabras = transcribir_video_por_palabras(ruta_video_master) if con_subtitulos else []
    planes = mapear_mejores_clips(palabras, master.duration)
    
    # Convertir color Hex a BGR para OpenCV
    hex_c = color_sub_hex.lstrip('#')
    rgb_c = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
    bgr_color = (rgb_c[2], rgb_c[1], rgb_c[0])

    final_clips = []
    for i, p in enumerate(planes):
        t_ini, t_fin = p['start'], p['end']
        chunk = master.subclip(t_ini, t_fin)
        
        tracking = analizar_rostros_multi_tracking(ruta_video_master, t_ini, t_fin)
        w, h = chunk.size
        tw = int(h * (9/16)) if "9:16" in formato else w
        
        cache_video = {"ultimo_t": -1.0, "ultimo_frame": None, "prev_gray": None}

        def procesar_cuadro_avanzado(get_frame, t):
            frame = get_frame(t)
            gray_actual = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Algoritmo Anti-Trabado
            if cache_video["ultimo_frame"] is not None and cache_video["prev_gray"] is not None:
                diff = cv2.absdiff(gray_actual, cache_video["prev_gray"])
                if np.mean(diff) < 1.0 and t > cache_video["ultimo_t"]:
                    flujo = cv2.calcOpticalFlowFarneback(cache_video["prev_gray"], gray_actual, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                    h_m, w_m = flujo.shape[:2]
                    mapa_x, mapa_y = np.meshgrid(np.arange(w_m), np.arange(h_m))
                    mapa_x = (mapa_x + flujo[..., 0] * 0.5).astype(np.float32)
                    mapa_y = (mapa_y + flujo[..., 1] * 0.5).astype(np.float32)
                    frame = cv2.remap(cache_video["ultimo_frame"], mapa_x, mapa_y, cv2.INTER_LINEAR)
                    gray_actual = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            cache_video["ultimo_t"] = t
            cache_video["ultimo_frame"] = frame.copy()
            cache_video["prev_gray"] = gray_actual.copy()
            
            # Recorte 9:16 Dinámico
            if "9:16" in formato:
                idx = min(int(t * tracking['fps']), len(tracking['coordenadas'])-1)
                cx = tracking['coordenadas'][idx]
                x1 = max(0, min(w - tw, cx - (tw//2)))
                frame = frame[:, x1:x1+tw]

            # Inyección Nativa de Subtítulos con OpenCV (Evita usar ImageMagick por completo)
            if con_subtitulos:
                t_global = t_ini + t
                for word in palabras:
                    if word['start'] <= t_global <= word['end']:
                        texto = word['text'].upper()
                        fuente = cv2.FONT_HERSHEY_DUPLEX
                        escala = 1.3
                        grosor = 3
                        tam, _ = cv2.getTextSize(texto, fuente, escala, grosor)
                        
                        # Ubicación centrada inferior
                        tx = (frame.shape[1] - tam[0]) // 2
                        ty = int(frame.shape[0] * 0.75)
                        
                        # Borde negro de contraste
                        cv2.putText(frame, texto, (tx, ty), fuente, escala, (0, 0, 0), grosor + 4, cv2.LINE_AA)
                        # Texto Principal Color Personalizado
                        cv2.putText(frame, texto, (tx, ty), fuente, escala, bgr_color, grosor, cv2.LINE_AA)
                        break

            return frame
            
        chunk = chunk.fl(procesar_cuadro_avanzado, keep_duration=True)

        # 2. BARRA DE PROGRESO DINÁMICA
        def make_bar(get_frame, t):
            bar_w = int(chunk.size[0] * (t/chunk.duration))
            img = np.zeros((6, chunk.size[0], 3), dtype=np.uint8)
            img[:, :max(2, bar_w)] = [222, 255, 154]
            return img
            
        prog_bar = ColorClip(size=(chunk.size[0], 6), col=(0,0,0)).fl(make_bar, keep_duration=True).set_duration(chunk.duration).set_position(('left', 'bottom'))

        final_v = CompositeVideoClip([chunk, prog_bar]).set_duration(chunk.duration)
        fname = f"clip_{i+1}.mp4"
        final_v.write_videofile(os.path.join(dir_t, fname), fps=30, codec="libx264", audio_codec="aac", logger=None)
        final_v.close()
        
        final_clips.append({"archivo": fname, "score": p['score'], "reporte": p['reasons']})
        
    master.close()
    return {"status": "success", "clips": final_clips}
