"""
Meeting connector module for AI Podcast Generator.
Provides functionality to connect to live meetings via Zoom and MeetStream.ai.
"""
import os
import time
import json
import requests
import threading
import tempfile
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MeetingConnector:
    """
    Connects to live meetings and provides real-time audio streaming
    and transcription for podcast generation.
    """
    
    def __init__(self):
        # Load API keys and settings from environment
        self.meetstream_api_key = os.getenv("MEETSTREAM_API_KEY")
        self.meetstream_api_url = os.getenv("MEETSTREAM_API_URL", "https://api.meetstream.ai/v1")
        self.zoom_api_key = os.getenv("ZOOM_API_KEY")
        self.zoom_api_secret = os.getenv("ZOOM_API_SECRET")
        self.zoom_jwt_token = os.getenv("ZOOM_JWT_TOKEN")
        
        # Set up directories
        self.temp_dir = os.getenv("TEMP_AUDIO_DIR", "./temp_audio")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize state
        self.current_meeting = None
        self.recording_active = False
        self.recording_thread = None
        self.audio_chunks = []
        self.transcript_chunks = []
        
        # Check if MeetStream.ai API is available
        self.meetstream_available = self._check_meetstream_api()
        
        # Check if Zoom API is available
        self.zoom_available = self._check_zoom_api()
    
    def _check_meetstream_api(self):
        """Check if MeetStream.ai API is available and configured"""
        if not self.meetstream_api_key or self.meetstream_api_key == "your_meetstream_api_key_here":
            print("[WARNING] MeetStream.ai API key not configured")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.meetstream_api_key}"}
            response = requests.get(f"{self.meetstream_api_url}/status", headers=headers)
            if response.status_code == 200:
                print("[SUCCESS] MeetStream.ai API connection successful")
                return True
            else:
                print(f"[WARNING] MeetStream.ai API returned status code: {response.status_code}")
                return False
        except Exception as e:
            print(f"[WARNING] MeetStream.ai API connection failed: {str(e)}")
            return False
    
    def _check_zoom_api(self):
        """Check if Zoom API is available and configured"""
        if not self.zoom_api_key or self.zoom_api_key == "your_zoom_api_key_here":
            print("[WARNING] Zoom API key not configured")
            return False
        
        if not self.zoom_api_secret or not self.zoom_jwt_token:
            print("[WARNING] Zoom API secret or JWT token not configured")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.zoom_jwt_token}"}
            response = requests.get("https://api.zoom.us/v2/users/me", headers=headers)
            if response.status_code == 200:
                print("[SUCCESS] Zoom API connection successful")
                return True
            else:
                print(f"[WARNING] Zoom API returned status code: {response.status_code}")
                return False
        except Exception as e:
            print(f"[WARNING] Zoom API connection failed: {str(e)}")
            return False
    
    def list_available_meetings(self):
        """List available meetings that can be joined"""
        if not self.zoom_available:
            return {"error": "Zoom API not available", "meetings": []}
        
        try:
            # Get list of scheduled meetings
            headers = {"Authorization": f"Bearer {self.zoom_jwt_token}"}
            response = requests.get("https://api.zoom.us/v2/users/me/meetings", headers=headers)
            
            if response.status_code == 200:
                meetings_data = response.json()
                meetings = []
                
                for meeting in meetings_data.get("meetings", []):
                    meetings.append({
                        "id": meeting.get("id"),
                        "topic": meeting.get("topic"),
                        "start_time": meeting.get("start_time"),
                        "duration": meeting.get("duration"),
                        "join_url": meeting.get("join_url")
                    })
                
                return {"success": True, "meetings": meetings}
            else:
                return {"error": f"Failed to get meetings: {response.status_code}", "meetings": []}
        except Exception as e:
            return {"error": f"Exception while listing meetings: {str(e)}", "meetings": []}
    
    def join_meeting(self, meeting_id=None, meeting_url=None):
        """Join a meeting by ID or URL"""
        if not meeting_id and not meeting_url:
            return {"error": "Meeting ID or URL is required"}
        
        if not self.meetstream_available:
            return {"error": "MeetStream.ai API not available"}
        
        try:
            # Join the meeting via MeetStream.ai
            headers = {"Authorization": f"Bearer {self.meetstream_api_key}"}
            payload = {}
            
            if meeting_id:
                payload["meeting_id"] = meeting_id
            elif meeting_url:
                payload["meeting_url"] = meeting_url
            
            response = requests.post(
                f"{self.meetstream_api_url}/meetings/join", 
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                meeting_data = response.json()
                self.current_meeting = meeting_data
                return {"success": True, "meeting": meeting_data}
            else:
                return {"error": f"Failed to join meeting: {response.status_code}"}
        except Exception as e:
            return {"error": f"Exception while joining meeting: {str(e)}"}
    
    def start_recording(self):
        """Start recording the current meeting"""
        if not self.current_meeting:
            return {"error": "Not connected to any meeting"}
        
        if self.recording_active:
            return {"error": "Recording already in progress"}
        
        # Start recording in a separate thread
        self.recording_active = True
        self.audio_chunks = []
        self.transcript_chunks = []
        
        self.recording_thread = threading.Thread(target=self._recording_worker)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        return {"success": True, "message": "Recording started"}
    
    def _recording_worker(self):
        """Worker thread for recording meeting audio and transcription"""
        try:
            meeting_id = self.current_meeting.get("meeting_id")
            session_id = self.current_meeting.get("session_id")
            
            if not meeting_id or not session_id:
                print("[ERROR] Missing meeting ID or session ID")
                self.recording_active = False
                return
            
            headers = {"Authorization": f"Bearer {self.meetstream_api_key}"}
            
            # Start streaming endpoint
            stream_url = f"{self.meetstream_api_url}/meetings/{meeting_id}/stream"
            stream_params = {"session_id": session_id, "format": "audio"}
            
            with requests.get(stream_url, headers=headers, params=stream_params, stream=True) as response:
                if response.status_code != 200:
                    print(f"[ERROR] Streaming failed with status code: {response.status_code}")
                    self.recording_active = False
                    return
                
                # Process the audio stream
                for chunk in response.iter_content(chunk_size=16384):
                    if not self.recording_active:
                        break
                    
                    if chunk:
                        # Save audio chunk
                        self.audio_chunks.append(chunk)
                        
                        # Get real-time transcription
                        self._get_transcription_update()
                        
                        # Sleep briefly to avoid overwhelming the API
                        time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] Recording worker exception: {str(e)}")
        finally:
            self.recording_active = False
    
    def _get_transcription_update(self):
        """Get transcription updates from MeetStream.ai"""
        try:
            meeting_id = self.current_meeting.get("meeting_id")
            session_id = self.current_meeting.get("session_id")
            
            if not meeting_id or not session_id:
                return
            
            headers = {"Authorization": f"Bearer {self.meetstream_api_key}"}
            transcript_url = f"{self.meetstream_api_url}/meetings/{meeting_id}/transcript"
            transcript_params = {"session_id": session_id}
            
            response = requests.get(transcript_url, headers=headers, params=transcript_params)
            
            if response.status_code == 200:
                transcript_data = response.json()
                
                # Process new transcript segments
                for segment in transcript_data.get("segments", []):
                    if segment not in self.transcript_chunks:
                        self.transcript_chunks.append(segment)
        except Exception as e:
            print(f"[ERROR] Transcription update exception: {str(e)}")
    
    def stop_recording(self):
        """Stop recording the current meeting"""
        if not self.recording_active:
            return {"error": "No recording in progress"}
        
        self.recording_active = False
        
        # Wait for recording thread to finish
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5.0)
        
        # Save the recorded audio to a file
        timestamp = int(time.time())
        audio_path = os.path.join(self.temp_dir, f"meeting_recording_{timestamp}.wav")
        
        with open(audio_path, "wb") as f:
            for chunk in self.audio_chunks:
                f.write(chunk)
        
        # Save the transcript to a file
        transcript_path = os.path.join(self.temp_dir, f"meeting_transcript_{timestamp}.json")
        
        with open(transcript_path, "w") as f:
            json.dump({"transcript": self.transcript_chunks}, f, indent=2)
        
        return {
            "success": True,
            "message": "Recording stopped",
            "audio_path": audio_path,
            "transcript_path": transcript_path
        }
    
    def leave_meeting(self):
        """Leave the current meeting"""
        if not self.current_meeting:
            return {"error": "Not connected to any meeting"}
        
        # Stop recording if active
        if self.recording_active:
            self.stop_recording()
        
        try:
            meeting_id = self.current_meeting.get("meeting_id")
            session_id = self.current_meeting.get("session_id")
            
            if not meeting_id or not session_id:
                self.current_meeting = None
                return {"success": True, "message": "Meeting session cleared"}
            
            # Leave the meeting via MeetStream.ai
            headers = {"Authorization": f"Bearer {self.meetstream_api_key}"}
            leave_url = f"{self.meetstream_api_url}/meetings/{meeting_id}/leave"
            leave_params = {"session_id": session_id}
            
            response = requests.post(leave_url, headers=headers, params=leave_params)
            
            self.current_meeting = None
            
            if response.status_code == 200:
                return {"success": True, "message": "Left meeting successfully"}
            else:
                return {"warning": f"Left meeting with status code: {response.status_code}"}
        except Exception as e:
            self.current_meeting = None
            return {"warning": f"Exception while leaving meeting: {str(e)}"}
    
    def get_meeting_status(self):
        """Get the status of the current meeting"""
        if not self.current_meeting:
            return {"connected": False}
        
        return {
            "connected": True,
            "meeting_id": self.current_meeting.get("meeting_id"),
            "topic": self.current_meeting.get("topic", "Unknown Meeting"),
            "recording": self.recording_active,
            "transcript_chunks": len(self.transcript_chunks),
            "audio_duration_seconds": len(self.audio_chunks) * 0.1  # Approximate duration
        }
    
    def simulate_meeting(self, duration_seconds=60, participants=2):
        """
        Simulate a meeting for testing when real meeting APIs are not available.
        This creates fake audio and transcript data.
        """
        if self.recording_active:
            return {"error": "Recording already in progress"}
        
        # Create a simulated meeting
        self.current_meeting = {
            "meeting_id": f"simulated_{int(time.time())}",
            "session_id": f"sim_session_{int(time.time())}",
            "topic": "Simulated Meeting",
            "simulated": True
        }
        
        # Start simulated recording
        self.recording_active = True
        self.audio_chunks = []
        self.transcript_chunks = []
        
        # Create a thread for simulation
        self.recording_thread = threading.Thread(
            target=self._simulate_recording_worker,
            args=(duration_seconds, participants)
        )
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        return {"success": True, "message": f"Simulated meeting started for {duration_seconds} seconds"}
    
    def _simulate_recording_worker(self, duration_seconds, participants):
        """Worker thread for simulating meeting recording"""
        try:
            # Simulated conversation topics
            topics = [
                "project updates",
                "quarterly goals",
                "marketing strategy",
                "customer feedback",
                "product roadmap",
                "team collaboration"
            ]
            
            # Simulated participant names
            participant_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley"]
            meeting_participants = participant_names[:participants]
            
            # Generate simulated transcript chunks
            start_time = time.time()
            chunk_interval = 5  # Generate a new transcript chunk every 5 seconds
            
            while self.recording_active and (time.time() - start_time) < duration_seconds:
                # Create a simulated audio chunk (just random bytes)
                audio_chunk = os.urandom(16384)  # 16KB of random data
                self.audio_chunks.append(audio_chunk)
                
                # Every chunk_interval, generate a transcript segment
                elapsed = time.time() - start_time
                if int(elapsed) % chunk_interval == 0:
                    topic = topics[int(elapsed / chunk_interval) % len(topics)]
                    speaker = meeting_participants[int(elapsed / chunk_interval) % len(meeting_participants)]
                    
                    transcript_segment = {
                        "speaker": speaker,
                        "text": f"I think we should discuss our {topic} in more detail.",
                        "start_time": elapsed,
                        "end_time": elapsed + chunk_interval - 0.5,
                        "confidence": 0.95
                    }
                    
                    self.transcript_chunks.append(transcript_segment)
                
                # Sleep to simulate real-time recording
                time.sleep(1)
        except Exception as e:
            print(f"[ERROR] Simulation worker exception: {str(e)}")
        finally:
            self.recording_active = False
            
            # Generate a complete simulated transcript
            full_transcript = " ".join([chunk.get("text", "") for chunk in self.transcript_chunks])
            
            # Add the full transcript as the last chunk
            self.transcript_chunks.append({
                "speaker": "SYSTEM",
                "text": full_transcript,
                "start_time": 0,
                "end_time": duration_seconds,
                "confidence": 0.98,
                "is_full_transcript": True
            })
