import streamlit as st
from PIL import Image
import subprocess
import mimetypes
import re
import tempfile
import imageio_ffmpeg as ffmpeg

st.set_page_config(page_title="Mauz Global Converter Cloud", layout="wide")
st.title("🌐 Mauz Global Converter Pro (Cloud, Tempfile)")

uploaded_file = st.file_uploader("Datei hochladen", type=None)
if uploaded_file:
    # tempfile für Input
    with tempfile.NamedTemporaryFile(delete=False) as tmp_input:
        tmp_input.write(uploaded_file.getbuffer())
        input_path = tmp_input.name

    # Auto-Type Discovery
    mime_type, _ = mimetypes.guess_type(uploaded_file.name)
    if mime_type:
        if mime_type.startswith("image"):
            file_type = "Bild"
        elif mime_type.startswith("video"):
            file_type = "Video"
        elif mime_type.startswith("audio"):
            file_type = "Audio"
        else:
            file_type = st.selectbox("Dateityp konnte nicht automatisch erkannt werden:", ["Bild", "Video", "Audio"])
    else:
        file_type = st.selectbox("Dateityp auswählen:", ["Bild", "Video", "Audio"])

    st.write(f"Erkannter Typ: **{file_type}**")

    try:
        if file_type == "Bild":
            img = Image.open(uploaded_file)
            st.image(img, caption="Original Bild", use_column_width=True)

            width = st.number_input("Breite in px (0 = Original)", value=0)
            height = st.number_input("Höhe in px (0 = Original)", value=0)
            if width > 0 and height > 0:
                img = img.resize((width, height))

            target_format = st.selectbox("Ziel-Format", ["PNG", "JPEG", "WEBP"])
            if st.button("Konvertieren Bild"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{target_format.lower()}") as tmp_output:
                    img.save(tmp_output.name)
                    st.success("Bild konvertiert!")
                    st.download_button("Download", open(tmp_output.name, "rb"), file_name=f"converted.{target_format.lower()}")

        else:
            target_format = st.selectbox(
                "Ziel-Format", 
                ["mp4","avi","mov","mkv"] if file_type=="Video" else ["mp3","wav","ogg","flac"]
            )

            # tempfile für Output
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{target_format}") as tmp_output:
                output_path = tmp_output.name

            progress_bar = st.progress(0)
            status_text = st.empty()

            # Dauer aus FFmpeg auslesen
            def get_duration(path):
                result = subprocess.run([ffmpeg.get_ffmpeg_exe(), "-i", path], stderr=subprocess.PIPE, text=True)
                m = re.search(r"Duration: (\d+):(\d+):([\d\.]+)", result.stderr)
                if m:
                    h, m_, s = m.groups()
                    return int(h)*3600 + int(m_)*60 + float(s)
                return None

            duration = get_duration(input_path)
            if not duration:
                duration = 1

            if st.button("Konvertieren"):
                with st.spinner("Konvertiere..."):
                    cmd = [ffmpeg.get_ffmpeg_exe(), "-y", "-i", input_path, output_path]
                    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True, bufsize=1)

                    for line in process.stderr:
                        match = re.search(r"time=(\d+):(\d+):([\d\.]+)", line)
                        if match:
                            h, m_, s = match.groups()
                            elapsed = int(h)*3600 + int(m_)*60 + float(s)
                            progress = min(elapsed/duration, 1.0)
                            progress_bar.progress(progress)
                            eta = max(duration - elapsed, 0)
                            status_text.text(f"ETA: {int(eta)} Sekunden")

                    process.wait()

                    st.success(f"{file_type} konvertiert!")
                    if file_type=="Video":
                        st.video(output_path)
                    else:
                        st.audio(output_path)
                    st.download_button("Download", open(output_path,"rb"), file_name=f"converted.{target_format}")

    except Exception as e:
        st.error(f"Fehler bei der Konvertierung: {e}")
        st.warning("Fallback: Originaldatei wird zum Download angeboten.")
        st.download_button("Download Original", open(input_path,"rb"), file_name=uploaded_file.name)