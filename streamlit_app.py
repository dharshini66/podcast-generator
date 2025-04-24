"""
Meeting to Podcast AI Agent - Streamlit Web App
"""

import os
import tempfile
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_player import st_player
import matplotlib.pyplot as plt
from PIL import Image
import time
import json
from datetime import datetime
import base64

# Import project modules
from src.transcription.assembly_client import AssemblyClient
from src.audio.ffmpeg_processor import FFmpegProcessor
from src.tts.voice_generator import VoiceGenerator
from src.podcast.podcast_generator import PodcastGenerator

# Set page configuration
st.set_page_config(
    page_title="Meeting to Podcast AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    with open(os.path.join("static", "css", "style.css")) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

try:
    load_css()
except:
    pass

# Initialize session state variables
if 'podcasts' not in st.session_state:
    st.session_state.podcasts = []
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Upload"

# Create directories if they don't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("output_podcasts", exist_ok=True)
os.makedirs("temp_audio", exist_ok=True)

# Sidebar
with st.sidebar:
    st.image("static/img/logo.png", width=100)
    st.title("Meeting to Podcast AI")
    
    selected = option_menu(
        menu_title=None,
        options=["Upload", "My Podcasts", "Settings"],
        icons=["cloud-upload", "collection-play", "gear"],
        default_index=0,
    )
    
    st.session_state.current_tab = selected
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        "Transform your meetings into engaging podcast snippets using AI. "
        "Upload a meeting recording to get started."
    )
    
    st.markdown("---")
    st.markdown("### Technologies Used")
    st.markdown("- AssemblyAI for transcription")
    st.markdown("- FFmpeg for audio processing")
    st.markdown("- ElevenLabs/Google TTS for voice narration")

# Initialize clients
@st.cache_resource
def load_clients():
    assembly_client = AssemblyClient()
    ffmpeg_processor = FFmpegProcessor()
    voice_generator = VoiceGenerator()
    podcast_generator = PodcastGenerator(
        assembly_client=assembly_client,
        ffmpeg_processor=ffmpeg_processor,
        voice_generator=voice_generator
    )
    return assembly_client, ffmpeg_processor, voice_generator, podcast_generator

assembly_client, ffmpeg_processor, voice_generator, podcast_generator = load_clients()

# Function to get list of generated podcasts
def get_podcasts():
    podcasts = []
    output_dir = "output_podcasts"
    
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            if filename.endswith(('.mp3', '.wav')):
                # Check if metadata file exists
                metadata_path = os.path.join(output_dir, os.path.splitext(filename)[0] + '.json')
                metadata = {}
                
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                
                podcasts.append({
                    'filename': filename,
                    'path': os.path.join(output_dir, filename),
                    'title': metadata.get('title', filename),
                    'description': metadata.get('description', ''),
                    'created_at': metadata.get('created_at', ''),
                    'duration_sec': metadata.get('duration_sec', 0),
                    'key_points': metadata.get('key_points', []),
                })
    
    # Sort podcasts by creation date (newest first)
    podcasts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return podcasts

# Function to create a download link
def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}" class="download-button">Download {file_label}</a>'
    return href

# Function to process uploaded audio
def process_audio(uploaded_file, meeting_title, use_voice_narration):
    try:
        # Save uploaded file
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Process the audio file
        st.session_state.processing = True
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Transcription
        status_text.text("Transcribing audio...")
        transcript = assembly_client.transcribe_audio(temp_path)
        progress_bar.progress(25)
        
        # Step 2: Analyze transcript and identify key segments
        status_text.text("Analyzing transcript for key segments...")
        segments = podcast_generator.analyze_transcript(transcript)
        progress_bar.progress(50)
        
        # Step 3: Process segments
        status_text.text("Processing audio segments...")
        podcast_paths = []
        
        for i, segment in enumerate(segments):
            # Extract segment
            segment_path = ffmpeg_processor.extract_segment(
                temp_path, 
                segment['start_time'], 
                segment['end_time']
            )
            
            # Add voice narration if requested
            if use_voice_narration:
                intro_text = f"Here's a quick snippet from our session on {segment['title']}..."
                outro_text = "That was an interesting point from the meeting."
                
                segment_path = voice_generator.add_narration(
                    segment_path,
                    intro_text,
                    outro_text
                )
            
            # Save to output directory
            podcast_paths.append(segment_path)
            
            # Update progress
            progress_bar.progress(50 + (i + 1) * 50 // len(segments))
        
        # Final step: Complete
        status_text.text("Podcast generation complete!")
        progress_bar.progress(100)
        
        # Update session state
        st.session_state.podcasts = get_podcasts()
        st.session_state.processing = False
        
        return True, podcast_paths
    
    except Exception as e:
        st.error(f"Error processing audio: {str(e)}")
        st.session_state.processing = False
        return False, []

# Main content based on selected tab
if st.session_state.current_tab == "Upload":
    st.title("Upload Meeting Recording")
    
    with st.form("upload_form"):
        meeting_title = st.text_input("Meeting Title", "My Meeting")
        uploaded_file = st.file_uploader("Upload Audio File", type=["mp3", "wav", "m4a"])
        use_voice_narration = st.checkbox("Add AI Voice Narration", value=True)
        
        submit_button = st.form_submit_button("Generate Podcasts")
    
    if submit_button and uploaded_file is not None:
        with st.spinner("Processing your audio file..."):
            success, podcast_paths = process_audio(uploaded_file, meeting_title, use_voice_narration)
            
            if success:
                st.success(f"Generated {len(podcast_paths)} podcast segments!")
                st.session_state.current_tab = "My Podcasts"
                st.experimental_rerun()

elif st.session_state.current_tab == "My Podcasts":
    st.title("My Podcasts")
    
    # Refresh podcast list
    st.session_state.podcasts = get_podcasts()
    
    if not st.session_state.podcasts:
        st.info("No podcasts generated yet. Upload a meeting recording to get started.")
    else:
        # Display podcasts in a grid
        cols = st.columns(2)
        
        for i, podcast in enumerate(st.session_state.podcasts):
            with cols[i % 2]:
                with st.expander(podcast['title'], expanded=True):
                    # Audio player
                    st.audio(podcast['path'])
                    
                    # Description
                    st.markdown(f"**Description:** {podcast['description']}")
                    
                    # Duration
                    duration_min = podcast['duration_sec'] // 60
                    duration_sec = podcast['duration_sec'] % 60
                    st.markdown(f"**Duration:** {duration_min}m {duration_sec}s")
                    
                    # Key points
                    if podcast['key_points']:
                        st.markdown("**Key Points:**")
                        for point in podcast['key_points']:
                            st.markdown(f"- {point}")
                    
                    # Download button
                    st.markdown(
                        get_binary_file_downloader_html(podcast['path'], 'Podcast'),
                        unsafe_allow_html=True
                    )

elif st.session_state.current_tab == "Settings":
    st.title("Settings")
    
    # AssemblyAI settings
    st.header("Transcription Settings")
    assembly_api_key = st.text_input(
        "AssemblyAI API Key",
        value=os.getenv("ASSEMBLY_API_KEY", ""),
        type="password"
    )
    
    # Voice narration settings
    st.header("Voice Narration Settings")
    voice_provider = st.selectbox(
        "Voice Provider",
        options=["ElevenLabs", "Google TTS"],
        index=0
    )
    
    if voice_provider == "ElevenLabs":
        elevenlabs_api_key = st.text_input(
            "ElevenLabs API Key",
            value=os.getenv("ELEVENLABS_API_KEY", ""),
            type="password"
        )
        elevenlabs_voice = st.selectbox(
            "Voice",
            options=["Rachel", "Domi", "Bella", "Antoni", "Thomas", "Charlie"],
            index=0
        )
    else:
        google_credentials = st.text_area(
            "Google Cloud Credentials JSON",
            value="",
            height=100
        )
        google_voice = st.selectbox(
            "Voice",
            options=["en-US-Standard-A", "en-US-Standard-B", "en-US-Standard-C"],
            index=0
        )
    
    # Save settings
    if st.button("Save Settings"):
        # Create .env file with settings
        with open(".env", "w") as f:
            f.write(f"ASSEMBLY_API_KEY={assembly_api_key}\n")
            
            if voice_provider == "ElevenLabs":
                f.write(f"ELEVENLABS_API_KEY={elevenlabs_api_key}\n")
                f.write(f"ELEVENLABS_VOICE={elevenlabs_voice}\n")
                f.write(f"VOICE_PROVIDER=elevenlabs\n")
            else:
                f.write(f"VOICE_PROVIDER=google\n")
                f.write(f"GOOGLE_VOICE={google_voice}\n")
                
                # Save Google credentials to file
                if google_credentials:
                    with open("google_credentials.json", "w") as gc:
                        gc.write(google_credentials)
                    f.write(f"GOOGLE_APPLICATION_CREDENTIALS=google_credentials.json\n")
        
        st.success("Settings saved successfully!")

# Footer
st.markdown("---")
st.markdown(
    "<div class='footer'>Meeting to Podcast AI © 2025</div>",
    unsafe_allow_html=True
)
