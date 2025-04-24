"""
Meeting interface for AI Podcast Generator.
Provides a web interface for connecting to meetings and generating podcasts in real-time.
"""
import os
import time
import json
import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.utils import secure_filename
from src.meetings.meeting_connector import MeetingConnector
from production_podcast_generator import PodcastGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'temp_audio')
app.config['OUTPUT_FOLDER'] = os.path.join(os.getcwd(), 'output_podcasts')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload size

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Global meeting connector instance
meeting_connector = MeetingConnector()

# Global podcast generator instance
podcast_generator = PodcastGenerator()

@app.route('/')
def index():
    """Home page for meeting interface"""
    meeting_status = meeting_connector.get_meeting_status()
    return render_template('meeting_index.html', meeting_status=meeting_status)

@app.route('/meetings/list')
def list_meetings():
    """List available meetings"""
    meetings_data = meeting_connector.list_available_meetings()
    return jsonify(meetings_data)

@app.route('/meetings/join', methods=['POST'])
def join_meeting():
    """Join a meeting by ID or URL"""
    meeting_id = request.form.get('meeting_id')
    meeting_url = request.form.get('meeting_url')
    
    result = meeting_connector.join_meeting(meeting_id=meeting_id, meeting_url=meeting_url)
    return jsonify(result)

@app.route('/meetings/simulate', methods=['POST'])
def simulate_meeting():
    """Simulate a meeting for testing"""
    duration = int(request.form.get('duration', 60))
    participants = int(request.form.get('participants', 2))
    
    result = meeting_connector.simulate_meeting(
        duration_seconds=duration,
        participants=participants
    )
    return jsonify(result)

@app.route('/meetings/status')
def meeting_status():
    """Get the current meeting status"""
    status = meeting_connector.get_meeting_status()
    return jsonify(status)

@app.route('/meetings/start_recording', methods=['POST'])
def start_recording():
    """Start recording the current meeting"""
    result = meeting_connector.start_recording()
    return jsonify(result)

@app.route('/meetings/stop_recording', methods=['POST'])
def stop_recording():
    """Stop recording and generate podcast"""
    # Stop the recording
    result = meeting_connector.stop_recording()
    
    if not result.get('success'):
        return jsonify(result)
    
    # Get the audio path and generate a podcast
    audio_path = result.get('audio_path')
    title = request.form.get('title', 'Meeting Recording')
    voice = request.form.get('voice', 'default')
    segments = int(request.form.get('segments', 5))
    style = request.form.get('style', 'professional')
    add_music = request.form.get('add_music') == 'true'
    
    # Generate the podcast in a background thread to avoid blocking
    def generate_podcast_thread():
        podcast_result = podcast_generator.generate_podcast(
            audio_path,
            title,
            max_points=segments,
            voice_style=voice,
            podcast_style=style,
            add_background_music=add_music
        )
        
        # Store the result in session for later retrieval
        if podcast_result:
            session['last_podcast'] = {
                'info': podcast_result.get('info'),
                'audio': podcast_result.get('audio'),
                'timestamp': int(time.time())
            }
    
    # Start the podcast generation thread
    thread = threading.Thread(target=generate_podcast_thread)
    thread.daemon = True
    thread.start()
    
    # Return success and let the client poll for completion
    return jsonify({
        'success': True,
        'message': 'Recording stopped and podcast generation started',
        'audio_path': audio_path
    })

@app.route('/meetings/leave', methods=['POST'])
def leave_meeting():
    """Leave the current meeting"""
    result = meeting_connector.leave_meeting()
    return jsonify(result)

@app.route('/meetings/podcast_status')
def podcast_status():
    """Check if the podcast generation is complete"""
    last_podcast = session.get('last_podcast')
    
    if not last_podcast:
        return jsonify({
            'complete': False,
            'message': 'No podcast generation in progress'
        })
    
    # Check if the podcast files exist
    info_path = last_podcast.get('info')
    audio_path = last_podcast.get('audio')
    
    if info_path and os.path.exists(info_path) and audio_path and os.path.exists(audio_path):
        return jsonify({
            'complete': True,
            'info_file': os.path.basename(info_path),
            'audio_file': os.path.basename(audio_path)
        })
    
    return jsonify({
        'complete': False,
        'message': 'Podcast generation in progress'
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
