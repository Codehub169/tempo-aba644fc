import streamlit as st
import yt_dlp
import os
import tempfile

# Page configuration
st.set_page_config(
    page_title="YouTube to MP3",
    page_icon="🎵",  # Changed from "\tvango " to a music emoji
    layout="centered"
)

# Design System & Custom CSS
SECONDARY_COLOR = "#F0F2F6"  # Light Grey
ACCENT_COLOR = "#007BFF"     # Blue
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
    box-shadow: 0 0 0 2px {ACCENT_COLOR}40; /* Subtle focus ring */
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
    """Remove characters that are problematic for filenames and ensure it's not empty."""
    name = str(name) # Ensure name is a string
    name = name.replace('/', '_').replace('\\', '_').replace(':', '_')
    name = name.replace('*', '_').replace('?', '_').replace('"', '_')
    name = name.replace('<', '_').replace('>', '_').replace('|', '_')
    # Remove any leading/trailing whitespace and reduce multiple spaces to one
    name = " ".join(name.split())
    if not name:  # If name is empty after sanitization
        name = "untitled_audio"
    return name

def download_and_convert_video(youtube_url, temp_dir):
    """Downloads audio from YouTube and converts it to MP3 using yt-dlp."""
    try:
        # Step 1: Get video info (including title) for our desired filename
        # Using 'extract_flat': 'in_playlist' is okay for single videos too.
        ydl_info_opts = {'quiet': True, 'noplaylist': True, 'skip_download': True, 'extract_flat': 'in_playlist'}
        with yt_dlp.YoutubeDL(ydl_info_opts) as ydl_info:
            info_pre_download = ydl_info.extract_info(youtube_url, download=False)
            video_title = info_pre_download.get('title', 'youtube_audio') # Default if title not found
            sanitized_base_name = sanitize_filename(video_title)
            user_facing_mp3_filename = f"{sanitized_base_name}.mp3"

        # Step 2: Download and convert to MP3 using yt-dlp
        output_filename_template_for_yt_dlp = os.path.join(temp_dir, f"{sanitized_base_name}.%(ext)s")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_filename_template_for_yt_dlp,
            'noplaylist': True,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192', # Corresponds to 192k bitrate
            }],
            'keepvideo': False, # Remove original downloaded file if different format
        }

        final_mp3_path_from_yt_dlp = None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict_after_download = ydl.extract_info(youtube_url, download=True)
            
            if 'requested_downloads' in info_dict_after_download and info_dict_after_download['requested_downloads']:
                final_mp3_path_from_yt_dlp = info_dict_after_download['requested_downloads'][0]['filepath']
            elif '_filename' in info_dict_after_download: # Fallback for some cases
                final_mp3_path_from_yt_dlp = info_dict_after_download['_filename']
            else:
                # Construct expected path if info_dict doesn't provide it clearly
                final_mp3_path_from_yt_dlp = os.path.join(temp_dir, f"{sanitized_base_name}.mp3")

            if not final_mp3_path_from_yt_dlp or not os.path.exists(final_mp3_path_from_yt_dlp):
                # Last resort: search the directory for an mp3 file with the sanitized base name
                expected_mp3_in_dir = os.path.join(temp_dir, f"{sanitized_base_name}.mp3")
                if os.path.exists(expected_mp3_in_dir):
                    final_mp3_path_from_yt_dlp = expected_mp3_in_dir
                else: # if not found, try any mp3
                    mp3_files_in_dir = [f for f in os.listdir(temp_dir) if f.endswith('.mp3')]
                    if mp3_files_in_dir:
                        final_mp3_path_from_yt_dlp = os.path.join(temp_dir, mp3_files_in_dir[0])
                    else:
                        raise FileNotFoundError("MP3 file not found after yt-dlp processing.")
        
        # Ensure the file is named as per our sanitization for user download
        path_with_user_facing_name = os.path.join(temp_dir, user_facing_mp3_filename)

        if os.path.abspath(final_mp3_path_from_yt_dlp) != os.path.abspath(path_with_user_facing_name):
            if os.path.exists(path_with_user_facing_name):
                 os.remove(path_with_user_facing_name) # Remove if a different file exists at target
            os.rename(final_mp3_path_from_yt_dlp, path_with_user_facing_name)
        
        return path_with_user_facing_name, user_facing_mp3_filename

    except yt_dlp.utils.DownloadError as e:
        st.session_state.error_message = f"Error downloading or processing video: {str(e)}"
        return None, None
    except FileNotFoundError as e:
        st.session_state.error_message = f"File processing error: {str(e)}"
        return None, None
    except Exception as e:
        st.session_state.error_message = f"An unexpected error occurred: {str(e)}"
        return None, None

# --- Streamlit App UI ---
st.title("YouTube to MP3 Converter 🎵")
st.write("Paste a YouTube video URL below to convert it to an MP3 audio file.")

# Initialize session state variables
if 'mp3_file_path' not in st.session_state:
    st.session_state.mp3_file_path = None
if 'mp3_file_name' not in st.session_state:
    st.session_state.mp3_file_name = None
if 'mp3_download_data' not in st.session_state:
    st.session_state.mp3_download_data = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'last_url' not in st.session_state:
    st.session_state.last_url = ""

# YouTube URL Input
youtube_url = st.text_input("YouTube Video URL", placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# Download & Convert Button
if st.button("Convert to MP3", key="convert_button"):
    if youtube_url:
        # Reset state if new URL or previous conversion failed/wasn't completed
        if youtube_url != st.session_state.last_url or not st.session_state.mp3_download_data:
            st.session_state.mp3_file_path = None
            st.session_state.mp3_file_name = None
            st.session_state.mp3_download_data = None
            st.session_state.error_message = None
        st.session_state.last_url = youtube_url
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with st.status("Processing your request...", expanded=True) as status:
                st.write("⏳ Fetching video information...") # Removed \x0c, added emoji
                mp3_path, mp3_name = download_and_convert_video(youtube_url, temp_dir)
                
                if mp3_path and mp3_name:
                    st.write("✅ Conversion successful!") # Added emoji
                    status.update(label="Conversion Complete!", state="complete", expanded=False)
                    
                    with open(mp3_path, "rb") as fp:
                        st.session_state.mp3_download_data = fp.read()
                    st.session_state.mp3_file_path = "processed" # Flag to indicate success
                    st.session_state.mp3_file_name = mp3_name
                    st.session_state.error_message = None # Clear any previous errors
                else:
                    # Error message is set in download_and_convert_video
                    status.update(label="Conversion Failed", state="error", expanded=True)
                    st.session_state.mp3_file_path = None
                    st.session_state.mp3_file_name = None
                    st.session_state.mp3_download_data = None # Clear data on failure
    else:
        st.session_state.error_message = "Please enter a YouTube URL."
        st.session_state.mp3_file_path = None
        st.session_state.mp3_file_name = None
        st.session_state.mp3_download_data = None # Clear data on input error

# Display Error Messages
if st.session_state.error_message:
    # Corrected HTML formatting for error message display
    st.markdown(f'<div class="error-message">⚠️ {st.session_state.error_message}</div>', unsafe_allow_html=True)

# Display Download Link/Button
if st.session_state.mp3_file_path == "processed" and st.session_state.mp3_file_name and st.session_state.mp3_download_data:
    # Removed \x0c, added emoji
    st.markdown(f'<div class="success-message">🎉 Your MP3 is ready! Click below to download.</div>', unsafe_allow_html=True)
    st.download_button(
        label=f"Download {st.session_state.mp3_file_name}",
        data=st.session_state.mp3_download_data,
        file_name=st.session_state.mp3_file_name,
        mime="audio/mpeg",
        key="download_mp3_button"
    )
    st.markdown("---")
    st.caption("_Note: The download link will disappear if you enter a new URL or refresh the page before downloading._")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666666;'>Simple YouTube to MP3 Converter by Your App</div>", unsafe_allow_html=True)
