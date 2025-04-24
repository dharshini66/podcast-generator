"""
Initialization script for Meeting to Podcast AI Agent
Creates necessary directories and sets up the environment
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Create necessary directories and environment file"""
    # Create directories
    directories = [
        'uploads',
        'output_podcasts',
        'temp_audio'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here

# MeetStream.ai API
MEETSTREAM_API_KEY=your_meetstream_api_key_here
MEETSTREAM_API_URL=https://api.meetstream.ai/v1

# Zoom API Credentials
ZOOM_API_KEY=your_zoom_api_key_here
ZOOM_API_SECRET=your_zoom_api_secret_here
ZOOM_JWT_TOKEN=your_zoom_jwt_token_here

# Application Settings
TEMP_AUDIO_DIR=./temp_audio
OUTPUT_DIR=./output_podcasts
""")
        logger.info("Created .env file. Please update it with your API keys.")
    
    logger.info("Environment setup complete!")

if __name__ == "__main__":
    setup_environment()
    
    # Print instructions
    print("\n" + "="*80)
    print("Meeting to Podcast AI Agent - Setup Complete!")
    print("="*80)
    print("\nTo start the application:")
    print("1. Update your API keys in the .env file")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the application: python app.py")
    print("\nThe web interface will be available at: http://localhost:5000")
    print("="*80)
