"""
Zoom API client for joining and recording meetings
"""

import os
import time
import json
import logging
import tempfile
import requests
import websockets
import asyncio
import wave
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import pyaudio, but provide a fallback if it's not available
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    logger.warning("PyAudio not available. Audio recording functionality will be limited.")
    PYAUDIO_AVAILABLE = False
    # Define a dummy class for compatibility
    class PyAudioDummy:
        paInt16 = 16
        
        def __init__(self):
            pass
            
        def get_sample_size(self, format):
            return 2
            
        def terminate(self):
            pass
    
    pyaudio = PyAudioDummy()

class ZoomClient:
    """Client for interacting with Zoom API and joining meetings"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, 
                jwt_token: Optional[str] = None):
        """
        Initialize the Zoom API client
        
        Args:
            api_key: Zoom API key (defaults to ZOOM_API_KEY env var)
            api_secret: Zoom API secret (defaults to ZOOM_API_SECRET env var)
            jwt_token: Zoom JWT token (defaults to ZOOM_JWT_TOKEN env var)
        """
        self.api_key = api_key or os.getenv("ZOOM_API_KEY")
        self.api_secret = api_secret or os.getenv("ZOOM_API_SECRET")
        self.jwt_token = jwt_token or os.getenv("ZOOM_JWT_TOKEN")
        
        if not all([self.api_key, self.api_secret, self.jwt_token]):
            raise ValueError("Zoom API credentials are required (API key, secret, and JWT token)")
        
        # Set up headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Base URL for Zoom API
        self.api_url = "https://api.zoom.us/v2"
        
        # Set up temporary directory for recordings
        self.temp_dir = os.getenv("TEMP_AUDIO_DIR", "./temp_audio")
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a request to the Zoom API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            
        Returns:
            API response as dictionary
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Zoom API: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def get_meeting_info(self, meeting_id: str) -> Dict[str, Any]:
        """
        Get information about a meeting
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            Meeting information
        """
        return self._make_request("GET", f"/meetings/{meeting_id}")
    
    def get_join_url(self, meeting_id: str, password: Optional[str] = None) -> str:
        """
        Get the URL to join a meeting
        
        Args:
            meeting_id: Zoom meeting ID
            password: Meeting password (if required)
            
        Returns:
            Join URL
        """
        # Get meeting information
        meeting_info = self.get_meeting_info(meeting_id)
        
        # Construct join URL
        join_url = meeting_info.get("join_url", "")
        
        # Add password if provided and not in the URL
        if password and "pwd" not in join_url:
            join_url += f"&pwd={password}"
        
        return join_url
    
    async def _connect_to_meeting_websocket(self, meeting_id: str, password: Optional[str] = None) -> websockets.WebSocketClientProtocol:
        """
        Connect to the Zoom meeting WebSocket
        
        Args:
            meeting_id: Zoom meeting ID
            password: Meeting password (if required)
            
        Returns:
            WebSocket connection
        """
        # This is a simplified implementation
        # In a real implementation, you would need to handle Zoom's WebSocket protocol
        # which is not publicly documented and would require reverse engineering
        
        # For demonstration purposes, we'll use a placeholder WebSocket URL
        # In reality, this would be derived from the meeting join process
        ws_url = f"wss://zoom.us/meeting/ws/{meeting_id}"
        
        # Connect to WebSocket
        websocket = await websockets.connect(ws_url)
        
        # Send join message with credentials
        join_message = {
            "action": "join",
            "meeting_id": meeting_id,
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "password": password
        }
        
        await websocket.send(json.dumps(join_message))
        
        # Wait for confirmation
        response = await websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get("status") != "success":
            raise Exception(f"Failed to join meeting: {response_data.get('error')}")
        
        return websocket
    
    async def _record_audio_stream(self, websocket: websockets.WebSocketClientProtocol, 
                                 output_path: str, duration: Optional[int] = None) -> None:
        """
        Record audio from the WebSocket stream
        
        Args:
            websocket: WebSocket connection
            output_path: Path to save the recording
            duration: Recording duration in seconds (None for unlimited)
        """
        # Set up audio parameters
        format = pyaudio.paInt16
        channels = 1
        rate = 44100
        chunk = 1024
        
        # Initialize PyAudio
        audio = pyaudio.PyAudio()
        
        # Open wave file for writing
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(format))
        wf.setframerate(rate)
        
        # Start time for duration tracking
        start_time = time.time()
        
        try:
            logger.info(f"Recording started, saving to {output_path}")
            
            # Record until duration is reached or connection is closed
            while duration is None or (time.time() - start_time) < duration:
                try:
                    # Receive audio data from WebSocket
                    # In a real implementation, you would need to parse the Zoom WebSocket protocol
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    
                    # Extract audio data from message
                    # This is a placeholder - actual implementation would depend on Zoom's protocol
                    if isinstance(message, bytes):
                        audio_data = message
                    else:
                        # If message is JSON, it might be a control message
                        message_data = json.loads(message)
                        if message_data.get("type") == "audio":
                            audio_data = message_data.get("data").encode("base64")
                        else:
                            continue
                    
                    # Write audio data to file
                    wf.writeframes(audio_data)
                    
                except asyncio.TimeoutError:
                    # No data received within timeout, continue
                    continue
                except websockets.exceptions.ConnectionClosed:
                    # Connection closed
                    logger.info("WebSocket connection closed")
                    break
        
        finally:
            # Close wave file and PyAudio
            wf.close()
            audio.terminate()
            logger.info("Recording stopped")
    
    def join_and_record_meeting(self, meeting_id: str, password: Optional[str] = None, 
                              duration: Optional[int] = None) -> str:
        """
        Join a Zoom meeting and record the audio
        
        Args:
            meeting_id: Zoom meeting ID
            password: Meeting password (if required)
            duration: Recording duration in seconds (None for unlimited)
            
        Returns:
            Path to the recorded audio file
        """
        # Create output file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.temp_dir, f"zoom_meeting_{meeting_id}_{timestamp}.wav")
        
        # Since we can't actually implement the Zoom WebSocket protocol here,
        # we'll provide a simulated implementation for demonstration purposes
        
        logger.info(f"Joining Zoom meeting: {meeting_id}")
        
        # In a real implementation, this would use the WebSocket code above
        # For now, we'll simulate recording by creating an empty audio file
        
        # Create an empty WAV file
        format = pyaudio.paInt16
        channels = 1
        rate = 44100
        
        audio = pyaudio.PyAudio()
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(format))
        wf.setframerate(rate)
        wf.close()
        audio.terminate()
        
        logger.info(f"Meeting recording simulated, saved to: {output_path}")
        
        return output_path
    
    def simulate_recording(self, duration: int = 60) -> str:
        """
        Simulate a recording for testing purposes
        
        Args:
            duration: Simulated recording duration in seconds
            
        Returns:
            Path to the simulated recording file
        """
        # Create output file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.temp_dir, f"simulated_recording_{timestamp}.wav")
        
        # Create a silent WAV file
        format = pyaudio.paInt16
        channels = 1
        rate = 44100
        chunk = 1024
        
        audio = pyaudio.PyAudio()
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(format))
        wf.setframerate(rate)
        
        # Generate silence
        silence = b'\x00' * chunk * channels * (rate // chunk) * duration
        wf.writeframes(silence)
        
        wf.close()
        audio.terminate()
        
        logger.info(f"Simulated recording created: {output_path}")
        
        return output_path
