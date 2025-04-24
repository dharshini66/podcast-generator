"""
Web interface for the Meeting to Podcast AI Agent
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

from src.api.gemini_client import GeminiClient
from src.api.meetstream_client import MeetStreamClient
from src.zoom.zoom_client import ZoomClient
from src.audio.audio_processor import AudioProcessor
from src.podcast.podcast_generator import PodcastGenerator

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Set up directories
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output_podcasts')
TEMP_AUDIO_FOLDER = os.path.join(os.getcwd(), 'temp_audio')

# Create directories if they don't exist
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, TEMP_AUDIO_FOLDER]:
    os.makedirs(folder, exist_ok=True)
    logger.info(f"Ensured directory exists: {folder}")

# Initialize Flask app
app = Flask(__name__)

# Initialize clients
gemini_client = None
meetstream_client = None
audio_processor = None
podcast_generator = None
zoom_client = None

try:
    gemini_client = GeminiClient(api_key=os.getenv('GOOGLE_API_KEY'))
    logger.info("Initialized Google Gemini client")
except Exception as e:
    logger.error(f"Error initializing Google Gemini client: {str(e)}")
    gemini_client = GeminiClient(api_key="dummy_key")  # Fallback with dummy key

try:
    meetstream_client = MeetStreamClient(
        api_key=os.getenv('MEETSTREAM_API_KEY'),
        api_url=os.getenv('MEETSTREAM_API_URL')
    )
    logger.info("Initialized MeetStream client")
except Exception as e:
    logger.error(f"Error initializing MeetStream client: {str(e)}")
    meetstream_client = MeetStreamClient(api_key="dummy_key", api_url="https://api.meetstream.ai/v1")  # Fallback

try:
    audio_processor = AudioProcessor(temp_dir=TEMP_AUDIO_FOLDER)
    logger.info("Initialized Audio Processor")
except Exception as e:
    logger.error(f"Error initializing Audio Processor: {str(e)}")
    audio_processor = AudioProcessor(temp_dir=TEMP_AUDIO_FOLDER)  # Try again

try:
    podcast_generator = PodcastGenerator(
        gemini_client=gemini_client,
        meetstream_client=meetstream_client,
        audio_processor=audio_processor,
        output_dir=OUTPUT_FOLDER
    )
    logger.info("Initialized Podcast Generator")
except Exception as e:
    logger.error(f"Error initializing Podcast Generator: {str(e)}")

# Initialize Zoom client if credentials are available
if all([os.getenv('ZOOM_API_KEY'), os.getenv('ZOOM_API_SECRET'), os.getenv('ZOOM_JWT_TOKEN')]):
    try:
        zoom_client = ZoomClient(
            api_key=os.getenv('ZOOM_API_KEY'),
            api_secret=os.getenv('ZOOM_API_SECRET'),
            jwt_token=os.getenv('ZOOM_JWT_TOKEN')
        )
        logger.info("Initialized Zoom client")
    except Exception as e:
        logger.error(f"Error initializing Zoom client: {str(e)}")
        zoom_client = None
else:
    logger.warning("Zoom credentials not found. Zoom integration will be disabled.")
    zoom_client = None

# Routes
@app.route('/')
def index():
    """Render the main dashboard"""
    # Get list of generated podcasts
    podcasts = []
    if os.path.exists(OUTPUT_FOLDER):
        for filename in os.listdir(OUTPUT_FOLDER):
            if filename.endswith('.wav'):
                # Check if metadata file exists
                metadata_path = os.path.join(OUTPUT_FOLDER, os.path.splitext(filename)[0] + '.json')
                metadata = {}
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                
                podcasts.append({
                    'filename': filename,
                    'path': f'/podcasts/{filename}',
                    'title': metadata.get('title', filename),
                    'description': metadata.get('description', ''),
                    'created_at': metadata.get('created_at', ''),
                    'duration_ms': metadata.get('duration_ms', 0),
                })
    
    # Sort podcasts by creation date (newest first)
    podcasts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render_template('index.html', podcasts=podcasts, zoom_enabled=zoom_client is not None)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload for processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save the uploaded file
    filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    # Get meeting title from form
    meeting_title = request.form.get('meeting_title', f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    try:
        # Process the file
        podcast_paths = podcast_generator.generate_from_file(file_path, meeting_title)
        
        # Return success response
        return jsonify({
            'success': True,
            'message': f'Generated {len(podcast_paths)} podcast segments',
            'podcasts': [os.path.basename(path) for path in podcast_paths]
        })
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/join_zoom', methods=['POST'])
def join_zoom():
    """Join a Zoom meeting and record"""
    if zoom_client is None:
        return jsonify({'error': 'Zoom integration is not configured'}), 400
    
    meeting_id = request.form.get('meeting_id')
    meeting_password = request.form.get('meeting_password', '')
    meeting_title = request.form.get('meeting_title', f"Zoom Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if not meeting_id:
        return jsonify({'error': 'Meeting ID is required'}), 400
    
    try:
        # Join meeting and record
        recording_path = zoom_client.join_and_record_meeting(
            meeting_id=meeting_id,
            password=meeting_password
        )
        
        # Process recording
        podcast_paths = podcast_generator.generate_from_file(recording_path, meeting_title)
        
        # Return success response
        return jsonify({
            'success': True,
            'message': f'Generated {len(podcast_paths)} podcast segments from Zoom meeting',
            'podcasts': [os.path.basename(path) for path in podcast_paths]
        })
    except Exception as e:
        logger.error(f"Error joining Zoom meeting: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/simulate', methods=['POST'])
def simulate_recording():
    """Simulate a recording for testing"""
    try:
        # Create a simulated recording
        recording_path = zoom_client.simulate_recording(duration=60)
        
        # Process the simulated recording
        meeting_title = request.form.get('meeting_title', f"Simulated Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        podcast_paths = podcast_generator.generate_from_file(recording_path, meeting_title)
        
        # Return success response
        return jsonify({
            'success': True,
            'message': f'Generated {len(podcast_paths)} podcast segments from simulated recording',
            'podcasts': [os.path.basename(path) for path in podcast_paths]
        })
    except Exception as e:
        logger.error(f"Error simulating recording: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/podcasts/<filename>')
def serve_podcast(filename):
    """Serve podcast files"""
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/api/podcasts')
def list_podcasts():
    """API endpoint to list all podcasts"""
    podcasts = []
    if os.path.exists(OUTPUT_FOLDER):
        for filename in os.listdir(OUTPUT_FOLDER):
            if filename.endswith('.wav'):
                # Check if metadata file exists
                metadata_path = os.path.join(OUTPUT_FOLDER, os.path.splitext(filename)[0] + '.json')
                metadata = {}
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                
                podcasts.append({
                    'filename': filename,
                    'url': f'/podcasts/{filename}',
                    'title': metadata.get('title', filename),
                    'description': metadata.get('description', ''),
                    'created_at': metadata.get('created_at', ''),
                    'duration_ms': metadata.get('duration_ms', 0),
                    'key_points': metadata.get('key_points', []),
                })
    
    # Sort podcasts by creation date (newest first)
    podcasts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return jsonify(podcasts)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
