"""
Voice generator for podcast narration using ElevenLabs and Google TTS
"""

import os
import logging
import tempfile
import json
from typing import Optional, Dict, Any
import requests
from google.cloud import texttospeech
import ffmpeg

logger = logging.getLogger(__name__)

class VoiceGenerator:
    """Generate voice narration for podcasts using various TTS providers"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the voice generator
        
        Args:
            temp_dir: Directory for temporary files (defaults to system temp dir)
        """
        self.temp_dir = temp_dir or os.getenv("TEMP_AUDIO_DIR", "./temp_audio")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Get provider from environment
        self.provider = os.getenv("VOICE_PROVIDER", "elevenlabs").lower()
        
        # Initialize ElevenLabs if selected
        if self.provider == "elevenlabs":
            self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
            self.elevenlabs_voice = os.getenv("ELEVENLABS_VOICE", "Rachel")
            
            if not self.elevenlabs_api_key:
                logger.warning("ElevenLabs API key not provided. Using placeholder responses.")
                self.using_placeholders = True
            else:
                self.using_placeholders = False
        
        # Initialize Google TTS if selected
        elif self.provider == "google":
            try:
                self.google_voice = os.getenv("GOOGLE_VOICE", "en-US-Standard-A")
                self.google_client = texttospeech.TextToSpeechClient()
                self.using_placeholders = False
            except Exception as e:
                logger.warning(f"Error initializing Google TTS: {str(e)}")
                logger.warning("Using placeholder responses.")
                self.using_placeholders = True
        
        else:
            logger.warning(f"Unknown voice provider: {self.provider}. Using placeholder responses.")
            self.using_placeholders = True
    
    def generate_voice(self, text: str, output_path: Optional[str] = None) -> str:
        """
        Generate voice audio from text
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save the audio file (if None, a temporary file is created)
            
        Returns:
            Path to the generated audio file
        """
        # Create output path if not provided
        if not output_path:
            output_path = os.path.join(
                self.temp_dir, 
                f"voice_{hash(text) % 10000:04d}.wav"
            )
        
        # If using placeholders, create a silent audio file
        if hasattr(self, 'using_placeholders') and self.using_placeholders:
            logger.info(f"Using placeholder voice for text: {text[:50]}...")
            self._create_silent_audio(output_path, duration=len(text.split()) * 0.3)  # Rough estimate
            return output_path
        
        # Generate voice based on provider
        if self.provider == "elevenlabs":
            return self._generate_elevenlabs_voice(text, output_path)
        elif self.provider == "google":
            return self._generate_google_voice(text, output_path)
        else:
            # Fallback to placeholder
            logger.warning(f"Unknown provider {self.provider}, using placeholder")
            self._create_silent_audio(output_path, duration=len(text.split()) * 0.3)
            return output_path
    
    def _generate_elevenlabs_voice(self, text: str, output_path: str) -> str:
        """
        Generate voice using ElevenLabs API
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file
            
        Returns:
            Path to the generated audio file
        """
        try:
            # ElevenLabs API endpoint
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._get_elevenlabs_voice_id()}"
            
            # Request headers
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            
            # Request data
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            # Make request
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            # Save audio to file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Generated ElevenLabs voice: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error generating ElevenLabs voice: {str(e)}")
            # Fallback to placeholder
            self._create_silent_audio(output_path, duration=len(text.split()) * 0.3)
            return output_path
    
    def _generate_google_voice(self, text: str, output_path: str) -> str:
        """
        Generate voice using Google TTS
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file
            
        Returns:
            Path to the generated audio file
        """
        try:
            # Set up the voice request
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=self.google_voice
            )
            
            # Select the type of audio file
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=44100
            )
            
            # Perform the text-to-speech request
            response = self.google_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            # Save the audio to file
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            logger.info(f"Generated Google TTS voice: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error generating Google TTS voice: {str(e)}")
            # Fallback to placeholder
            self._create_silent_audio(output_path, duration=len(text.split()) * 0.3)
            return output_path
    
    def _create_silent_audio(self, output_path: str, duration: float = 3.0) -> None:
        """
        Create a silent audio file
        
        Args:
            output_path: Path to save the audio file
            duration: Duration of silence in seconds
        """
        try:
            # Create silent audio using FFmpeg
            (
                ffmpeg
                .input(f"anullsrc=r=44100:cl=stereo", f="lavfi", t=duration)
                .output(output_path, acodec='pcm_s16le', ar=44100, ac=2)
                .run(quiet=True, overwrite_output=True)
            )
            
            logger.info(f"Created silent audio: {output_path}")
        except Exception as e:
            logger.error(f"Error creating silent audio: {str(e)}")
            # Create an empty file as last resort
            with open(output_path, 'wb') as f:
                f.write(b'')
    
    def _get_elevenlabs_voice_id(self) -> str:
        """
        Get the ElevenLabs voice ID for the selected voice
        
        Returns:
            Voice ID string
        """
        # Voice name to ID mapping
        voice_ids = {
            "Rachel": "21m00Tcm4TlvDq8ikWAM",
            "Domi": "AZnzlk1XvdvUeBnXmlld",
            "Bella": "EXAVITQu4vr4xnSDxMaL",
            "Antoni": "ErXwobaYiN019PkySvjV",
            "Thomas": "GBv7mTt0atIp3Br8iCZE",
            "Charlie": "IKne3meq5aSn9XLyUdCD"
        }
        
        # Return the ID for the selected voice, or Rachel as default
        return voice_ids.get(self.elevenlabs_voice, voice_ids["Rachel"])
    
    def add_narration(self, audio_path: str, intro_text: Optional[str] = None, 
                     outro_text: Optional[str] = None) -> str:
        """
        Add narration intro and outro to an audio file
        
        Args:
            audio_path: Path to the audio file
            intro_text: Text for intro narration
            outro_text: Text for outro narration
            
        Returns:
            Path to the audio with narration added
        """
        try:
            # Create temporary directory for files
            temp_dir = tempfile.mkdtemp(dir=self.temp_dir)
            
            # Generate intro if provided
            intro_path = None
            if intro_text:
                intro_path = os.path.join(temp_dir, "intro.wav")
                self.generate_voice(intro_text, intro_path)
            
            # Generate outro if provided
            outro_path = None
            if outro_text:
                outro_path = os.path.join(temp_dir, "outro.wav")
                self.generate_voice(outro_text, outro_path)
            
            # Create output path
            output_path = os.path.join(
                self.temp_dir, 
                f"{os.path.splitext(os.path.basename(audio_path))[0]}_with_narration.wav"
            )
            
            # Concatenate files
            files_to_concat = []
            if intro_path:
                files_to_concat.append(intro_path)
            
            files_to_concat.append(audio_path)
            
            if outro_path:
                files_to_concat.append(outro_path)
            
            # If only one file, just copy it
            if len(files_to_concat) == 1:
                (
                    ffmpeg
                    .input(files_to_concat[0])
                    .output(output_path, acodec='pcm_s16le', ar=44100, ac=2)
                    .run(quiet=True, overwrite_output=True)
                )
            else:
                # Build filter complex for concatenation
                inputs = []
                for path in files_to_concat:
                    inputs.append(ffmpeg.input(path))
                
                # Create filter_complex string
                filter_complex = []
                for i in range(len(files_to_concat)):
                    filter_complex.append(f"[{i}:a]")
                
                filter_complex.append(f"concat=n={len(files_to_concat)}:v=0:a=1")
                filter_complex.append("[out]")
                
                # Run FFmpeg command
                (
                    ffmpeg
                    .output(*inputs, output_path, filter_complex=''.join(filter_complex), map="[out]", acodec='pcm_s16le', ar=44100, ac=2)
                    .run(quiet=True, overwrite_output=True)
                )
            
            logger.info(f"Added narration to audio: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error adding narration: {str(e)}")
            # Return original file if there's an error
            return audio_path
