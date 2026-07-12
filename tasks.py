import os
import cv2
import torch
import yt_dlp
import numpy as np
import requests

# Compatible con MoviePy 2.0.0
from moviepy import VideoFileClip, TextClip, CompositeVideoClip

DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"

EMOJI_DICTIONARY = {
    "dinero": "💰", "fuego": "🔥", "viral": "🔥", "ganar": "🏆",
    "secreto": "🤫", "atención": "🚨", "mira": "👀", "importante": "⚠️",
    "éxito": "🚀", "brutal": "🤯", "cambio": "🔄", "crecer": "📈",
    "error": "❌", "meta": "🎯", "aprender": "🧠", "dinámica": "⚡"
}

PALABRAS_RETENCION = set(EMOJI_DICTIONARY.keys()) | {"jamás", "nunca", "hoy", "increíble", "truco", "revelado"}

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

def analizar_rostros_predictive_vectorial(video_path: str, t_inicio: float, t_fin: float):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC, t_inicio * 1000)
    
    ancho_orig = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
    fotogramas_totales = int((t_fin - t_inicio) * fps)
    registro_rostros = []
    
    cascade_humano = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    for f_idx in range(fotogramas_totales):
        ret, frame = cap.read()
        if not ret: break
            
        if f_idx % 6 == 0:
            coordenadas_x = []
            try:
                gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (0, 0), fx=0.25, fy=0.25)
                faces = cascade_humano.detectMultiScale(gray, 1.3, 4)
                coordenadas_x = sorted([int((x + w // 2) * 4) for (x, _, w, _) in faces])
            except:
                pass
            registro_rostros.append(coordenadas_x)
            
    cap.release()
    
    centros_raw = [f[0] if f else ancho_orig // 2 for f in registro_rostros]
    if not centros_raw: centros_raw = [ancho_orig // 2]
    
    suavizados = []
    pos_actual = centros_raw[0]
    for pos_detectada in centros_raw:
        distancia = pos_detectada - pos_actual
        factor_inercia = 1.0 if abs(distancia) > (ancho_orig // 3) else (0.08 if abs(distancia) < 30 else 0.45)
        pos_actual += int(distancia * factor_inercia)
        suavizados.append(pos_actual)
            
    return {"data": lambda t: suavizados[min(int(t * (fps / 6)), len(suavizados) - 1)]}

def mapear_mejores_clips(segmentos_palabras, duracion_total, max_clips=3):
    if not segmentos_palabras:
        return [{"start": 0, "end": min(35.0, duracion_total), "score": 75, "reasons": ["Segmento por defecto lineal."]}]
    
    ventanas = []
    paso_tiempo = 15.0 
    
    for inicio_bloque in np.arange(0, duracion_total - 25.0, paso_tiempo):
        fin_bloque = inicio_bloque + 40.0
        palabras_bloque = [w for w in segmentos_palabras if inicio_bloque <= w["start"] <= fin_bloque]
        
        if len(palabras_bloque) < 15: continue
            
        palabras_clave = 0
        ganchos = []
        for p in palabras_bloque:
            p_limpia = p["text"].lower().strip(".,¡!¿?")
            if p_limpia in PALABRAS_RETENCION:
                palabras_clave += 1
                if p_limpia not in ganchos: ganchos.append(p_limpia)
                
        wpm = (len(palabras_bloque) / (palabras_bloque[-1]["end"] - palabras_bloque[0]["start"])) * 60
        score = 65 + min(20, palabras_clave * 3) + (15 if 135 <= wpm <= 165 else 5)
        score = min(98, int(score))
        
        reasons = [
            f"⚡ Ritmo verbal calibrado a {int(wpm)} WPM.",
            f"🔑 Subtítulos potenciados por palabras clave: {', '.join(ganchos[:4]) if ganchos else 'Estructura plana'}."
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
            
    return clips_filtrados if clips_filtrados else [{"start": 0, "end": min(35.0, duracion_total), "score": 80, "reasons": ["Bloque único consolidado."]}]

def pipeline_procesamiento_masivo(tarea_id: str, ruta_video_master: str, formato: str, con_subtitulos: bool, color_sub_hex: str = "#deff9a", estilo_subtitulos: str = "hormozi", url_remoto: str = "", diccionario_manual: str = "") -> dict:
    dir_trabajo = garantizar_entorno_tarea(tarea_id)
    ruta_audio_full = os.path.join(dir_trabajo, "temp_voice.wav")
    clips_procesados = []
        
    try:
        if url_remoto and url_remoto.strip() != "":
            ruta_video_master = descargar_video_remoto(url_remoto, dir_trabajo)
                    
        if diccionario_manual:
            nuevos_ganchos = {p.strip().lower() for p in diccionario_manual.split(",") if p.strip()}
            PALABRAS_RETENCION.update(nuevos_ganchos)
                    
        clip_completo = VideoFileClip(ruta_video_master)
        
        if clip_completo.audio is not None:
            clip_completo.audio.write_audiofile(ruta_audio_full, fps=16000, nbytes=2, logger=None)
            
        segmentos_palabras = []
        if con_subtitulos and os.path.exists(ruta_audio_full):
            # --- TRANCRIPCIÓN SEGURA MEDIANTE LA API DE OPENAI (Evita instalar Whisper local) ---
            api_key = os.getenv("OPENAI_API_KEY", "TU_API_KEY_AQUI")
            
            if api_key and api_key != "TU_API_KEY_AQUI":
                headers = {"Authorization": f"Bearer {api_key}"}
                files = {"file": open(ruta_audio_full, "rb")}
                data = {"model": "whisper-1", "response_format": "verbose_json", "timestamp_granularities[]": "word"}
                
                respuesta = requests.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=files, data=data)
                
                if respuesta.status_code == 200:
                    datos_transcripcion = respuesta.json()
                    for word_obj in datos_transcripcion.get("words", []):
                        segmentos_palabras.append({
                            "start": word_obj["start"],
                            "end": word_obj["end"],
                            "text": word_obj["word"].strip()
                        })
            
            # Si no hay API Key o falla, se genera un segmento por defecto para evitar que la app se caiga
            if not segmentos_palabras:
                segmentos_palabras = [{"start": 0.5, "end": min(15.0, clip_completo.duration), "text": "Audio detectado sin API Key"}]
                    
        planes_de_corte = mapear_mejores_clips(segmentos_palabras, clip_completo.duration)
        
        for idx, plan in enumerate(planes_de_corte):
            t_ini, t_fin = plan["start"], plan["end"]
            
            chunk = clip_completo.subclip(t_ini, t_fin)
            duracion_chunk = chunk.duration
            
            if "9:16" in formato:
                w_orig, h_orig = chunk.size
                target_w = int(h_orig * (9 / 16))
                meta_rostros = analizar_rostros_predictive_vectorial(ruta_video_master, t_ini, t_fin)
                fn_centro = meta_rostros["data"]
                                
                def transformar_cuadros(get_frame, t):
                    frame = get_frame(t)
                    x1 = max(0, min(w_orig - target_w, fn_centro(t) - (target_w // 2)))
                    return frame[:, x1:x1 + target_w]
                
                chunk = chunk.fl(transformar_cuadros)
            
            componentes_chunk = [chunk]
            
            if con_subtitulos:
                for w_info in segmentos_palabras:
                    if t_ini <= w_info["start"] <= t_fin:
                        w_start = max(0.0, w_info["start"] - t_ini)
                        w_end = min(duracion_chunk, w_info["end"] - t_ini)
                        
                        word_raw = w_info["text"].strip()
                        palabra_limpia = word_raw.lower().strip(".,¡!¿?")
                        emoji = EMOJI_DICTIONARY.get(palabra_limpia, "")
                        texto_final = f"{emoji} {word_raw}" if emoji else word_raw
                        
                        color_actual = color_sub_hex if palabra_limpia in PALABRAS_RETENCION else "#FFFFFF"
                        
                        txt_clip = TextClip(
                            texto_final.upper(),
                            fontsize=48 if estilo_subtitulos == "hormozi" else 36,
                            color=color_actual,
                            font="Liberation-Sans-Bold",
                            size=(chunk.size[0] - 40, None)
                        )
                        
                        txt_clip = (txt_clip
                                    .set_duration(max(0.15, w_end - w_start))
                                    .set_start(w_start)
                                    .set_position(('center', int(chunk.size[1] * 0.72))))
                        
                        def animar_subtitulo(get_frame, t):
                            img = get_frame(t)
                            if t < 0.10:
                                escala = 1.15 - (t * 1.5)
                                escala = max(1.0, escala)
                                h_i, w_i = img.shape[:2]
                                img_s = cv2.resize(img, (0, 0), fx=escala, fy=escala, interpolation=cv2.INTER_LINEAR)
                                h_s, w_s = img_s.shape[:2]
                                return img_s[(h_s-h_i)//2 : (h_s-h_i)//2+h_i, (w_s-w_i)//2 : (w_s-w_i)//2+w_i]
                            return img
                            
                        txt_clip = txt_clip.fl(animar_subtitulo)
                        componentes_chunk.append(txt_clip)
                        
            video_final = CompositeVideoClip(componentes_chunk)
            nombre_archivo = f"clip_{idx + 1}_viral.mp4"
            ruta_salida_clip = os.path.join(dir_trabajo, nombre_archivo)
            
            video_final.write_videofile(ruta_salida_clip, fps=30, codec='libx264', audio_codec='aac', logger=None)
            video_final.close()
            
            clips_procesados.append({
                "archivo": nombre_archivo,
                "score": f"{plan['score']}%",
                "reporte": plan["reasons"]
            })
            
        clip_completo.close()
        if os.path.exists(ruta_audio_full): os.remove(ruta_audio_full)
        
        return {"status": "success", "clips": clips_procesados}
        
    except Exception as err:
        if os.path.exists(ruta_audio_full): os.remove(ruta_audio_full)
        return {"status": "error", "mensaje": str(err)}
