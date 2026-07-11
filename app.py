import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from tasks import async_render_worker

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "online", "engine": "ZexOS SaaS Backend"}

@app.post("/procesar")
async def procesar_video(
    file: UploadFile = File(...),
    formato: str = Form(...),
    con_subtitulos: str = Form(...)
):
    tarea_id = f"job_{uuid.uuid4().hex[:10]}"
    temp_dir = os.path.join("storage", f"temp_{tarea_id}")
    os.makedirs(temp_dir, exist_ok=True)
    ruta_input = os.path.join(temp_dir, file.filename)
    
    try:
        with open(ruta_input, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        is_sub = con_subtitulos.lower() == "true"
        
        # Ejecutar renderizador
        resultado = async_render_worker(
            tarea_id=tarea_id,
            ruta_video_master=ruta_input,
            formato=formato,
            con_subtitulos=is_sub,
            color_sub_hex="#deff9a"
        )
        
        if resultado["status"] == "success" and os.path.exists(resultado["file"]):
            # Inyectamos las métricas de Opus Clip en las cabeceras HTTP
            headers = {
                "X-Viral-Score": str(resultado.get("viral_score", "85%")),
                "X-Analisis-Popularidad": str(resultado.get("analisis_popularidad", "Buen ritmo de retención."))
            }
            return FileResponse(
                resultado["file"], 
                media_type="video/mp4", 
                filename="render.mp4", 
                headers=headers
            )
        else:
            return JSONResponse(status_code=500, content={"error": resultado.get("message", "Fallo desconocido")})
            
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
