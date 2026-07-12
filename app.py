import os
import uuid
import streamlit as st
from tasks import garantizar_entorno_tarea, pipeline_procesamiento_masivo

# Configuración de la página
st.set_page_config(
    page_title="IA Clip Cutter Pro",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 IA Clip Cutter Pro")
st.subheader("Corta y optimiza tus videos horizontales para Shorts, Reels y TikToks (Soporta Humanos y VTubers)")

# Crear layout de columnas para mantener limpia la interfaz operativa
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📥 Entrada de Video")
    video_url = st.text_input("Enlace de Video (YouTube, Twitch, TikTok, X, etc.):", "")
    
    st.write("O sube un archivo local:")
    video_file = st.file_uploader("Selecciona un archivo de video (.mp4, .mov):", type=["mp4", "mov"])

with col2:
    st.header("⚙️ Configuración del Short")
    formato = st.selectbox("Formato de salida:", ["9:16 (Short/Reel/TikTok)", "16:9 (Horizontal Original)"])
    
    con_subtitulos = st.checkbox("Generar Subtítulos con IA (Estilo Viral)", value=True)
    
    color_sub = st.color_picker("Color para palabras de impacto / ganchos:", "#deff9a")
    
    estilo_subtitulos = st.radio("Estilo de texto:", ["hormozi", "estándar"], index=0, horizontal=True)
    
    diccionario_manual = st.text_area(
        "Palabras clave de retención personalizadas (separadas por comas):",
        placeholder="ejemplo: imperdible, truco, dinero, dios, épico"
    )

st.markdown("---")

# Botón de ejecución
if st.button("🚀 Iniciar Procesamiento con IA", use_container_width=True):
    # Validar que tengamos una fuente de video válida
    if not video_url.strip() and not video_file:
        st.error("❌ Por favor, proporciona una URL de video o sube un archivo local.")
    else:
        tarea_id = str(uuid.uuid4())
        dir_trabajo = garantizar_entorno_tarea(tarea_id)
        ruta_video_input = ""
        
        # Guardar archivo si es local
        if video_file:
            ruta_video_input = os.path.join(dir_trabajo, "video_subido.mp4")
            with open(ruta_video_input, "wb") as f:
                f.write(video_file.getbuffer())
        
        with st.status("🛸 Ejecutando Pipeline Multi-Capa de IA...", expanded=True) as status:
            st.write("🎙️ Inicializando Whisper y analizando el audio latente...")
            
            # Ejecutar el procesamiento masivo desde tasks.py
            resultado = pipeline_procesamiento_masivo(
                tarea_id=tarea_id,
                ruta_video_master=ruta_video_input,
                formato=formato,
                con_subtitulos=con_subtitulos,
                color_sub_hex=color_sub,
                estilo_subtitulos=estilo_subtitulos,
                url_remoto=video_url,
                diccionario_manual=diccionario_manual
            )
            
            if resultado["status"] == "success":
                status.update(label="✅ ¡Clips virales generados con éxito!", state="complete")
                st.balloons()
                
                st.header("🎉 Resultados Obtenidos")
                
                # Desplegar los videos resultantes en un grid visual limpio
                for clip in resultado["clips"]:
                    ruta_absoluta_clip = os.path.join("storage", tarea_id, clip["archivo"])
                    
                    with st.container():
                        st.markdown(f"### 📹 {clip['archivo'].replace('_', ' ').title()}")
                        st.subheader(f"📊 Puntuación de Viralidad: `{clip['score']}`")
                        
                        # Mostrar razones del clip
                        for razon in clip["reporte"]:
                            st.caption(razon)
                            
                        # Renderizar el reproductor de video nativo
                        if os.path.exists(ruta_absoluta_clip):
                            with open(ruta_absoluta_clip, "rb") as f_video:
                                st.video(f_video.read())
                                
                            # Botón de descarga
                            with open(ruta_absoluta_clip, "rb") as f_download:
                                st.download_button(
                                    label=f"💾 Descargar {clip['archivo']}",
                                    data=f_download,
                                    file_name=clip["archivo"],
                                    mime="video/mp4",
                                    key=f"dl_{clip['archivo']}"
                                )
                        else:
                            st.error("No se pudo localizar el archivo físico del clip.")
                        st.markdown("---")
            else:
                status.update(label="❌ El proceso ha fallado", state="error")
                st.error(f"Error detectado en el backend: {resultado['mensaje']}")
