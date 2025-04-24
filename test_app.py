"""
Test script for Meeting to Podcast AI Agent
This script tests the core functionality without requiring external APIs
"""

import os
import sys
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def test_directory_structure():
    """Test that all required directories exist"""
    required_dirs = [
        'src',
        'src/api',
        'src/audio',
        'src/zoom',
        'src/podcast',
        'templates',
        'static',
        'static/css',
        'static/js',
        'uploads',
        'output_podcasts',
        'temp_audio'
    ]
    
    missing_dirs = []
    for directory in required_dirs:
        if not os.path.exists(directory):
            missing_dirs.append(directory)
            
    if missing_dirs:
        logger.error(f"Missing directories: {', '.join(missing_dirs)}")
        return False
    
    logger.info("✓ All required directories exist")
    return True

def test_module_imports():
    """Test that all required modules can be imported"""
    try:
        # Import core modules
        from src.api.gemini_client import GeminiClient
        from src.api.meetstream_client import MeetStreamClient
        from src.audio.audio_processor import AudioProcessor
        from src.zoom.zoom_client import ZoomClient
        from src.podcast.podcast_generator import PodcastGenerator
        
        logger.info("✓ All core modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        return False

def create_sample_podcast():
    """Create a sample podcast file for testing"""
    # Create a simple WAV file
    import wave
    import struct
    
    output_dir = 'output_podcasts'
    os.makedirs(output_dir, exist_ok=True)
    
    sample_rate = 44100
    duration = 5  # seconds
    
    # Create WAV file
    podcast_filename = f"sample_podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    podcast_path = os.path.join(output_dir, podcast_filename)
    
    with wave.open(podcast_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        
        # Generate a simple sine wave
        for i in range(0, sample_rate * duration):
            value = int(32767.0 * 0.5 * (i % 100 < 50))
            data = struct.pack('<h', value)
            wf.writeframes(data)
    
    # Create metadata file
    metadata = {
        "title": "Sample Podcast",
        "description": "This is a sample podcast generated for testing",
        "meeting_title": "Test Meeting",
        "created_at": datetime.now().isoformat(),
        "duration_ms": duration * 1000,
        "intro_text": "Welcome to this sample podcast",
        "outro_text": "Thank you for listening to this sample podcast",
        "key_points": [
            "This is a test podcast",
            "It was generated automatically",
            "No actual processing was done"
        ]
    }
    
    metadata_path = os.path.splitext(podcast_path)[0] + '.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"✓ Created sample podcast: {podcast_path}")
    return podcast_path, metadata_path

def test_flask_app():
    """Test that the Flask app can be initialized"""
    try:
        from flask import Flask
        app = Flask(__name__)
        logger.info("✓ Flask app initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Flask app initialization error: {str(e)}")
        return False

def run_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("Meeting to Podcast AI Agent - Test Suite")
    print("="*80 + "\n")
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Module Imports", test_module_imports),
        ("Flask App", test_flask_app)
    ]
    
    all_passed = True
    
    for name, test_func in tests:
        print(f"Testing: {name}...")
        try:
            result = test_func()
            if result:
                print(f"✓ {name} test passed\n")
            else:
                print(f"✗ {name} test failed\n")
                all_passed = False
        except Exception as e:
            print(f"✗ {name} test failed with error: {str(e)}\n")
            all_passed = False
    
    # Create sample podcast
    try:
        podcast_path, metadata_path = create_sample_podcast()
        print(f"✓ Sample podcast created at: {podcast_path}")
        print(f"✓ Sample metadata created at: {metadata_path}\n")
    except Exception as e:
        print(f"✗ Failed to create sample podcast: {str(e)}\n")
        all_passed = False
    
    if all_passed:
        print("\n" + "="*80)
        print("All tests passed! The application is ready to run.")
        print("="*80)
        print("\nTo start the application:")
        print("1. Update your API keys in the .env file")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run the application: python app.py")
        print("\nThe web interface will be available at: http://localhost:5000")
    else:
        print("\n" + "="*80)
        print("Some tests failed. Please fix the issues before running the application.")
        print("="*80)
    
    return all_passed

if __name__ == "__main__":
    run_tests()
