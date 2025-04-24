"""
MeetStream.ai API client for meeting transcription and analysis
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class MeetStreamClient:
    """Client for interacting with MeetStream.ai API"""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize the MeetStream.ai API client
        
        Args:
            api_key: MeetStream.ai API key (defaults to MEETSTREAM_API_KEY env var)
            api_url: MeetStream.ai API base URL (defaults to MEETSTREAM_API_URL env var)
        """
        self.api_key = api_key or os.getenv("MEETSTREAM_API_KEY")
        self.api_url = api_url or os.getenv("MEETSTREAM_API_URL")
        
        # Check if API credentials are available
        if not self.api_key:
            logger.warning("MeetStream.ai API key not provided. Using placeholder responses.")
            self.api_key = "dummy_key"
            self.using_placeholders = True
        else:
            self.using_placeholders = False
            
        if not self.api_url:
            logger.warning("MeetStream.ai API URL not provided. Using placeholder URL.")
            self.api_url = "https://api.meetstream.ai/v1"
        
        # Set up headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     files: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a request to the MeetStream.ai API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            files: Files to upload
            
        Returns:
            API response as dictionary
        """
        # If using placeholders, return dummy responses
        if hasattr(self, 'using_placeholders') and self.using_placeholders:
            logger.info(f"Using placeholder response for {method} {endpoint}")
            
            # Generate appropriate placeholder responses based on the endpoint
            if endpoint.endswith('/upload'):
                return {
                    "success": True,
                    "recording_id": "placeholder_recording_123",
                    "message": "Placeholder recording uploaded successfully"
                }
            elif '/transcription' in endpoint:
                return {
                    "success": True,
                    "transcript": "This is a placeholder transcript. The actual transcription would appear here.",
                    "confidence": 0.95
                }
            elif '/segments/extract' in endpoint:
                return {
                    "success": True,
                    "segments": [
                        {"id": "segment_1", "start": 0, "end": 60000, "title": "Placeholder Segment 1"},
                        {"id": "segment_2", "start": 60000, "end": 120000, "title": "Placeholder Segment 2"}
                    ]
                }
            elif '/audio/enhance' in endpoint:
                return {
                    "success": True,
                    "enhanced_audio_url": "https://example.com/placeholder_enhanced_audio.wav"
                }
            elif '/podcasts/create' in endpoint:
                return {
                    "success": True,
                    "podcast_id": "placeholder_podcast_123",
                    "url": "https://example.com/placeholder_podcast.wav"
                }
            else:
                return {
                    "success": True,
                    "message": f"Placeholder response for {method} {endpoint}"
                }
        
        # Make actual API request if not using placeholders
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == "POST":
                if files:
                    # For file uploads, don't use the JSON content-type header
                    headers = self.headers.copy()
                    if "Content-Type" in headers:
                        del headers["Content-Type"]
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
                    response = requests.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to MeetStream.ai API: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def upload_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Upload an audio file for processing
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            API response with upload details
        """
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'file': (os.path.basename(audio_file_path), audio_file, 'audio/mpeg')
            }
            
            data = {
                'name': os.path.basename(audio_file_path),
                'description': 'Meeting recording for podcast creation'
            }
            
            return self._make_request('POST', '/recordings/upload', data=data, files=files)
    
    def get_transcription(self, recording_id: str) -> Dict[str, Any]:
        """
        Get the transcription for a recording
        
        Args:
            recording_id: ID of the recording
            
        Returns:
            Transcription data
        """
        return self._make_request('GET', f'/recordings/{recording_id}/transcription')
    
    def get_recording_status(self, recording_id: str) -> Dict[str, Any]:
        """
        Get the status of a recording
        
        Args:
            recording_id: ID of the recording
            
        Returns:
            Recording status data
        """
        return self._make_request('GET', f'/recordings/{recording_id}')
    
    def extract_segments(self, recording_id: str, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract segments from a recording
        
        Args:
            recording_id: ID of the recording
            segments: List of segment definitions with start and end times
            
        Returns:
            API response with extracted segments
        """
        data = {
            'recording_id': recording_id,
            'segments': segments
        }
        
        return self._make_request('POST', '/segments/extract', data=data)
    
    def enhance_audio(self, segment_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance audio quality for a segment
        
        Args:
            segment_id: ID of the segment
            options: Enhancement options (noise reduction, normalization, etc.)
            
        Returns:
            API response with enhanced audio details
        """
        data = {
            'segment_id': segment_id,
            'options': options
        }
        
        return self._make_request('POST', '/audio/enhance', data=data)
    
    def create_podcast(self, name: str, description: str, segment_ids: List[str],
                      intro_text: Optional[str] = None, outro_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a podcast from segments
        
        Args:
            name: Podcast name
            description: Podcast description
            segment_ids: List of segment IDs to include
            intro_text: Optional text for TTS intro
            outro_text: Optional text for TTS outro
            
        Returns:
            API response with podcast details
        """
        data = {
            'name': name,
            'description': description,
            'segment_ids': segment_ids
        }
        
        if intro_text:
            data['intro_text'] = intro_text
        
        if outro_text:
            data['outro_text'] = outro_text
        
        return self._make_request('POST', '/podcasts/create', data=data)
    
    def get_podcast_status(self, podcast_id: str) -> Dict[str, Any]:
        """
        Get the status of a podcast
        
        Args:
            podcast_id: ID of the podcast
            
        Returns:
            Podcast status data
        """
        return self._make_request('GET', f'/podcasts/{podcast_id}')
