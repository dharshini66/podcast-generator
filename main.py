#!/usr/bin/env python
"""
Meeting to Podcast AI Agent
Main application entry point
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('podcast_agent.log')
    ]
)
logger = logging.getLogger(__name__)

# Import project modules
from src.api.gemini_client import GeminiClient
from src.api.meetstream_client import MeetStreamClient
from src.zoom.zoom_client import ZoomClient
from src.audio.audio_processor import AudioProcessor
from src.podcast.podcast_generator import PodcastGenerator

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Meeting to Podcast AI Agent')
    parser.add_argument('--mode', choices=['live', 'file'], default='live',
                        help='Operation mode: live (join Zoom meeting) or file (process existing recording)')
    parser.add_argument('--meeting-id', help='Zoom meeting ID (required for live mode)')
    parser.add_argument('--meeting-password', help='Zoom meeting password (if required)')
    parser.add_argument('--input-file', help='Path to input audio file (required for file mode)')
    parser.add_argument('--output-dir', help='Directory to save podcast output')
    
    return parser.parse_args()

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'GOOGLE_API_KEY',
        'MEETSTREAM_API_KEY',
        'MEETSTREAM_API_URL'
    ]
    
    # Add Zoom variables if in live mode
    if args.mode == 'live':
        required_vars.extend([
            'ZOOM_API_KEY',
            'ZOOM_API_SECRET',
            'ZOOM_JWT_TOKEN'
        ])
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file")
        sys.exit(1)

def main():
    """Main application entry point."""
    # Parse command line arguments
    global args
    args = parse_arguments()
    
    # Check environment variables
    check_environment()
    
    # Set output directory
    output_dir = args.output_dir or os.getenv('OUTPUT_DIR', './output_podcasts')
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize API clients
    gemini_client = GeminiClient(api_key=os.getenv('GOOGLE_API_KEY'))
    meetstream_client = MeetStreamClient(
        api_key=os.getenv('MEETSTREAM_API_KEY'),
        api_url=os.getenv('MEETSTREAM_API_URL')
    )
    
    # Initialize audio processor
    audio_processor = AudioProcessor()
    
    # Initialize podcast generator
    podcast_generator = PodcastGenerator(
        gemini_client=gemini_client,
        meetstream_client=meetstream_client,
        audio_processor=audio_processor,
        output_dir=output_dir
    )
    
    # Process based on mode
    if args.mode == 'live':
        if not args.meeting_id:
            logger.error("Meeting ID is required for live mode")
            sys.exit(1)
        
        # Initialize Zoom client
        zoom_client = ZoomClient(
            api_key=os.getenv('ZOOM_API_KEY'),
            api_secret=os.getenv('ZOOM_API_SECRET'),
            jwt_token=os.getenv('ZOOM_JWT_TOKEN')
        )
        
        # Join meeting and record
        logger.info(f"Joining Zoom meeting: {args.meeting_id}")
        recording_path = zoom_client.join_and_record_meeting(
            meeting_id=args.meeting_id,
            password=args.meeting_password
        )
        
        # Process recording and generate podcast
        logger.info("Meeting recorded, generating podcast...")
        podcast_generator.generate_from_file(recording_path)
        
    elif args.mode == 'file':
        if not args.input_file:
            logger.error("Input file path is required for file mode")
            sys.exit(1)
        
        if not os.path.exists(args.input_file):
            logger.error(f"Input file not found: {args.input_file}")
            sys.exit(1)
        
        # Process file and generate podcast
        logger.info(f"Processing audio file: {args.input_file}")
        podcast_generator.generate_from_file(args.input_file)
    
    logger.info(f"Podcast generation complete. Output saved to: {output_dir}")

if __name__ == "__main__":
    main()
