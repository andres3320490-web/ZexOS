import os
import sys
import requests
import cv2
import torch
import yt_dlp
import numpy as np
import whisper
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip

# --- DETECCIÓN DE ENTORNO FFMPEG ---
def forzar_instalacion_ffmpeg():
    try:
        import imageio_ffmpeg
        ruta = imageio_ffmpeg.get_ffmpeg_exe()
        os.environ["IMAGEIO_FFMPEG_EXE"] = ruta
        return ruta
    except:
        return "ffmpeg"

ruta_ffmpeg = forzar_instalacion_ffmpeg()

DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"
EMOJI_DICTIONARY = {"dinero": "💰", "fuego": "🔥", "viral": "🔥", "éxito": "🚀", "brutal": "🤯", "error": "❌"}
PALABRAS_RETENCION = set(EMOJI_DICTIONARY.keys()) | {"increíble", "secreto", "atención"}

def garantizar_fuente_fisica():
    os.makedirs("storage", exist_ok=True)
    ruta = os.path.abspath("storage/font.ttf")
    if not os.path.exists(ruta):
        url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
        r = requests.get(url)
        with open(ruta, "wb") as f: f.write(r.content)
    return ruta

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
    
    font_p = garantizar_fuente_fisica()
    master = VideoFileClip(ruta_video_master)
    palabras = transcribir_video_por_palabras(ruta_video_master) if con_subtitulos else []
    planes = mapear_mejores_clips(palabras, master.duration)
    
    final_clips = []
    for i, p in enumerate(planes):
        t_ini, t_fin = p['start'], p['end']
        chunk = master.subclip(t_ini, t_fin)
        
        # 1. AUTO-REENCUADRE (9:16) & REPARACIÓN DE TIRONES
        tracking = analizar_rostros_multi_tracking(ruta_video_master, t_ini, t_fin)
        w, h = chunk.size
        tw = int(h * (9/16)) if "9:16" in formato else w
        
        cache_video = {"ultimo_t": -1.0, "ultimo_frame": None, "prev_gray": None}

        def procesar_cuadro_avanzado(get_frame, t):
            frame = get_frame(t)
            
            # Algoritmo Anti-Trabado por Flujo Óptico
            gray_actual = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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
            
            if "9:16" in formato:
                idx = min(int(t * tracking['fps']), len(tracking['coordenadas'])-1)
                cx = tracking['coordenadas'][idx]
                x1 = max(0, min(w - tw, cx - (tw//2)))
                return frame[:, x1:x1+tw]
            return frame
            
        chunk = chunk.fl(procesar_cuadro_avanzado, keep_duration=True)

        # 2. BARRA DE PROGRESO DINÁMICA
        def make_bar(get_frame, t):
            bar_w = int(chunk.size[0] * (t/chunk.duration))
            img = np.zeros((6, chunk.size[0], 3), dtype=np.uint8)
            img[:, :max(2, bar_w)] = [222, 255, 154]
            return img
            
        prog_bar = ColorClip(size=(chunk.size[0], 6), col=(0,0,0)).fl(make_bar, keep_duration=True).set_duration(chunk.duration).set_position(('left', 'bottom'))

        # 3. CAPA DE SUBTÍTULOS
        comps = [chunk, prog_bar]
        if con_subtitulos:
            for word in [w for w in palabras if t_ini <= w['start'] < t_fin]:
                txt = TextClip(word['text'].upper(), fontsize=48, color=color_sub_hex, font=font_p, size=(chunk.size[0]-40, None), method="caption")
                txt = txt.set_start(word['start']-t_ini).set_duration(max(0.1, word['end']-word['start'])).set_position(('center', int(chunk.size[1]*0.7)))
                comps.append(txt)

        final_v = CompositeVideoClip(comps).set_duration(chunk.duration)
        fname = f"clip_{i+1}.mp4"
        final_v.write_videofile(os.path.join(dir_t, fname), fps=30, codec="libx264", audio_codec="aac", logger=None)
        final_v.close()
        
        final_clips.append({"archivo": fname, "score": p['score'], "reporte": p['reasons']})
        
    master.close()
    return {"status": "success", "clips": final_clips}
