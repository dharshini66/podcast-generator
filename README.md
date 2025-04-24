# AI Podcast Generator

An advanced AI agent that creates professional podcasts from meeting recordings and audio files. The system features a modern, futuristic UI and integrates with multiple AI services to deliver high-quality podcast content.

## Features

- **Dual Interface System**:
  - Main Web Interface for uploading and processing audio files
  - Meeting Interface for generating podcasts directly from live meetings

- **Advanced Audio Processing**:
  - Intelligent content extraction and segmentation
  - Background music integration
  - Professional audio mixing with FFmpeg

- **AI-Powered Voice Generation**:
  - Multiple voice options (Default, Male, Female, British, American)
  - Customizable podcast styles (Professional, Casual, Energetic, Calm)
  - Adjustable key segment extraction

- **Meeting Integration**:
  - Zoom meeting connection and recording
  - Real-time transcription during meetings
  - Simulation mode for testing without API keys

- **Modern User Experience**:
  - Dark mode with futuristic UI design
  - Real-time audio visualization
  - Theme toggle for light/dark preferences

## Technologies Used

- **AssemblyAI** for accurate transcription
- **ElevenLabs** for high-quality voice narration
- **FFmpeg** for professional audio processing
- **Google Gemini API** for intelligent content analysis
- **MeetStream.ai API** for meeting integration
- **Flask** for web interface

## Requirements

- Python 3.8+
- FFmpeg (included in the package)
- API keys for:
  - AssemblyAI
  - ElevenLabs
  - Google Gemini (optional)
  - MeetStream.ai (optional for meeting integration)
  - Zoom (optional for meeting integration)

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file with your API keys and credentials

## Usage

### Main Web Interface

1. Start the web interface:
   ```
   .\run_web_interface.bat
   ```
2. Open your browser and go to:
   ```
   http://localhost:5000
   ```
3. Upload an audio file (MP3 or WAV)
4. Customize your podcast settings
5. Generate your podcast

### Meeting Interface

1. Start the meeting interface:
   ```
   .\run_meeting_interface.bat
   ```
2. Open your browser and go to:
   ```
   http://localhost:5001
   ```
3. Join a meeting or use simulation mode
4. Record the meeting
5. Generate a podcast with your preferred settings

## Project Structure

- `src/api/` - API integrations (Google Gemini, MeetStream.ai)
- `src/audio/` - Audio processing utilities
- `src/meetings/` - Meeting integration components
- `src/podcast/` - Podcast generation logic
- `src/transcription/` - Transcription services
- `src/tts/` - Text-to-speech services
- `static/` - UI assets and styles
- `templates/` - Web interface templates
- `*.py` - Main application files

## Batch Files

- `run_web_interface.bat` - Start the main web interface
- `run_meeting_interface.bat` - Start the meeting integration interface
- `run_simple_app.bat` - Run the simplified console version
- `run_streamlit.bat` - Run the Streamlit web interface version
- `run_production.bat` - Run the production version
