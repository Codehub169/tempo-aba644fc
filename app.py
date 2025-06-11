import streamlit as st
import yt_dlp
from pydub import AudioSegment
import os
import tempfile
import shutil

# Page configuration
st.set_page_config(
    page_title="YouTube to MP3",
    page_icon="🎵",
    layout="centered"
)

# Design System & Custom CSS
PRIMARY_COLOR = "#FF0000"  # YouTube Red (use subtly)
SECONDARY_COLOR = "#F0F2F6" # Light Grey
ACCENT_COLOR = "#007BFF"    # Blue
TEXT_COLOR = "#333333"
SUCCESS_COLOR = "#28A745"
ERROR_COLOR = "#DC3545"

custom_css = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Poppins:wght@600;700&display=swap');

body {{
    font-family: 'Inter', sans-serif;
    color: {TEXT_COLOR};
    background-color: {SECONDARY_COLOR};
}}

.stTextInput input {{
    font-family: 'Inter', sans-serif;
    border-radius: 5px;
    border: 1px solid #DDDDDD;
}}

.stButton button {{
    font-family: 'Poppins', sans-serif;
    background-color: {ACCENT_COLOR};
    color: white;
    border-radius: 5px;
    padding: 0.5rem 1rem;
    border: none;
    transition: background-color 0.3s ease;
}}

.stButton button:hover {{
    background-color: #0056b3; /* Darker blue on hover */
}}

.stButton button:focus {{
    outline: none;
    box-shadow: 0 0 0 2px {{ACCENT_COLOR}}40; /* Subtle focus ring */
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: 'Poppins', sans-serif;
    color: {TEXT_COLOR};
}}

.success-message {{
    color: {SUCCESS_COLOR};
    background-color: #e9f7ef;
    padding: 10px;
    border-radius: 5px;
    border-left: 5px solid {SUCCESS_COLOR};
}}

.error-message {{
    color: {ERROR_COLOR};
    background-color: #fdecea;
    padding: 10px;
    border-radius: 5px;
    border-left: 5px solid {ERROR_COLOR};
}}
"""
st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

# Helper function to sanitize filename
def sanitize_filename(name):
    """Remove characters that are problematic for filenames."""
    # Remove or replace characters like /, \, :, *, ?, \", <, >, |
    name = name.replace('/', '_').replace('\\', '_').replace(':', '_')
    name = name.replace('*', '_').replace('?', '_').replace('"', '\'_').replace('<', '_')
    name = name.replace('>', '_').replace('|', '_')
    # Remove any leading/trailing whitespace and reduce multiple spaces to one
    name = " ".join(name.split())
    return name


def download_and_convert_video(youtube_url, temp_dir):
    """Downloads audio from YouTube and converts it to MP3."""
    try:
        # Download audio using yt-dlp
        ydl_opts = {{
            'format': 'bestaudio/best', # Download best audio quality
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'), # Save with video title
            'noplaylist': True, # Download only single video
            'quiet': True,
            'merge_output_format': None, # To ensure we get the raw audio file
            'postprocessors': [{'key': 'FFmpegExtractAudio'}], # Extract audio, don't specify codec yet
        }}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            original_filename = ydl.prepare_filename(info_dict)
            # yt-dlp might add its own audio extension (e.g. .m4a, .webm, .opus)
            # We need to find the actual downloaded file name
            downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
            if not downloaded_files:
                raise FileNotFoundError("Downloaded audio file not found in temporary directory.")
            
            # Assuming the first file is the one we want if multiple somehow appear (shouldn't with noplaylist)
            # or if title had problematic chars leading to different actual filename
            audio_file_path_original_ext = os.path.join(temp_dir, downloaded_files[0]) 

        # Sanitize title for MP3 filename
        video_title = info_dict.get('title', 'youtube_audio')
        sanitized_title = sanitize_filename(video_title)
        mp3_filename = f"{{sanitized_title}}.mp3"
        mp3_file_path = os.path.join(temp_dir, mp3_filename)

        # Convert to MP3 using pydub
        audio = AudioSegment.from_file(audio_file_path_original_ext)
        audio.export(mp3_file_path, format="mp3", bitrate="192k")
        
        # Clean up original downloaded file if it's different from mp3_file_path
        if audio_file_path_original_ext != mp3_file_path and os.path.exists(audio_file_path_original_ext):
             os.remove(audio_file_path_original_ext)

        return mp3_file_path, mp3_filename

    except yt_dlp.utils.DownloadError as e:
        st.session_state.error_message = f"Error downloading video: {{str(e)}}"
        return None, None
    except Exception as e:
        st.session_state.error_message = f"An error occurred: {{str(e)}}"
        return None, None

# --- Streamlit App UI ---
st.title("YouTube to MP3 Converter 🎵")
st.write("Paste a YouTube video URL below to convert it to an MP3 audio file.")

# Initialize session state variables
if 'mp3_file_path' not in st.session_state:
    st.session_state.mp3_file_path = None
if 'mp3_file_name' not in st.session_state:
    st.session_state.mp3_file_name = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'last_url' not in st.session_state:
    st.session_state.last_url = ""

# YouTube URL Input
youtube_url = st.text_input("YouTube Video URL", placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# Download & Convert Button
if st.button("Convert to MP3", key="convert_button"):
    if youtube_url:
        if youtube_url != st.session_state.last_url:
            # Reset previous state if new URL
            st.session_state.mp3_file_path = None
            st.session_state.mp3_file_name = None
            st.session_state.error_message = None
        st.session_state.last_url = youtube_url
        
        # Create a temporary directory for processing files
        # This directory will be automatically cleaned up when the 'with' block exits
        # or when the script finishes if not handled carefully with Streamlit's reruns.
        # For files meant for download, it's safer to read them into memory.
        with tempfile.TemporaryDirectory() as temp_dir:
            with st.status("Processing your request...", expanded=True) as status:
                st.write("🔗 Fetching video information...")
                mp3_path, mp3_name = download_and_convert_video(youtube_url, temp_dir)
                
                if mp3_path and mp3_name:
                    st.write("✅ Conversion successful!")
                    status.update(label="Conversion Complete!", state="complete", expanded=False)
                    
                    # Read the MP3 file into memory for the download button
                    with open(mp3_path, "rb") as fp:
                        st.session_state.mp3_download_data = fp.read()
                    st.session_state.mp3_file_path = "processed" # Indicate success
                    st.session_state.mp3_file_name = mp3_name
                    st.session_state.error_message = None # Clear any previous errors
                else:
                    # Error message is already set in session_state by download_and_convert_video
                    status.update(label="Conversion Failed", state="error", expanded=True)
                    st.session_state.mp3_file_path = None # Ensure no download button shows
                    st.session_state.mp3_file_name = None
    else:
        st.session_state.error_message = "Please enter a YouTube URL."
        st.session_state.mp3_file_path = None
        st.session_state.mp3_file_name = None

# Display Error Messages
if st.session_state.error_message:
    st.markdown(f'<div class="error-message">⚠️ {{st.session_state.error_message}}</div>', unsafe_allow_html=True)

# Display Download Link/Button
if st.session_state.mp3_file_path == "processed" and st.session_state.mp3_file_name and hasattr(st.session_state, 'mp3_download_data'):
    st.markdown(f'<div class="success-message">🎉 Your MP3 is ready! Click below to download.</div>', unsafe_allow_html=True)
    st.download_button(
        label=f"Download {{st.session_state.mp3_file_name}}",
        data=st.session_state.mp3_download_data,
        file_name=st.session_state.mp3_file_name,
        mime="audio/mpeg",
        key="download_mp3_button"
    )
    st.markdown("---_Note: The download link will disappear if you enter a new URL or refresh the page before downloading._---")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666666;'>Simple YouTube to MP3 Converter by Your App</div>", unsafe_allow_html=True)
