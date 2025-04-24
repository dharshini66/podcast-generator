"""
Audio processing utilities for podcast creation
"""

import os
import logging
import tempfile
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pydub import AudioSegment
from scipy.io import wavfile
from scipy import signal
from moviepy.editor import AudioFileClip

logger = logging.getLogger(__name__)

# Try to import speech_recognition, but provide a fallback if it's not available
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    logger.warning("Speech Recognition not available. Transcription functionality will be limited.")
    SR_AVAILABLE = False
    # Define a dummy class for compatibility
    class RecognizerDummy:
        def __init__(self):
            pass
            
        def record(self, source):
            return None
            
        def recognize_google(self, audio_data):
            raise Exception("Speech Recognition not available")
    
    class SrDummy:
        class AudioFile:
            def __init__(self, filename=None):
                pass
                
            def __enter__(self):
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        
        UnknownValueError = Exception
        RequestError = Exception
        
        def __init__(self):
            pass
            
        def Recognizer(self):
            return RecognizerDummy()
    
    sr = SrDummy()

class AudioProcessor:
    """Audio processing utilities for podcast creation"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the audio processor
        
        Args:
            temp_dir: Directory for temporary files (defaults to system temp dir)
        """
        self.temp_dir = temp_dir or os.getenv("TEMP_AUDIO_DIR", "./temp_audio")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize speech recognizer
        if SR_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = sr.Recognizer()
    
    def convert_to_wav(self, audio_path: str) -> str:
        """
        Convert audio file to WAV format if needed
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Path to the WAV file
        """
        # Check if already WAV
        if audio_path.lower().endswith('.wav'):
            return audio_path
        
        # Load audio file
        try:
            audio = AudioSegment.from_file(audio_path)
        except Exception as e:
            logger.error(f"Error loading audio file: {str(e)}")
            raise
        
        # Create output path
        output_path = os.path.join(
            self.temp_dir, 
            f"{os.path.splitext(os.path.basename(audio_path))[0]}.wav"
        )
        
        # Export as WAV
        audio.export(output_path, format="wav")
        logger.info(f"Converted audio to WAV: {output_path}")
        
        return output_path
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcription text
        """
        # Check if speech recognition is available
        if not SR_AVAILABLE:
            logger.warning("Speech Recognition not available. Returning placeholder transcript.")
            return "This is a placeholder transcript. Speech Recognition is not available."
            
        # Ensure audio is in WAV format
        wav_path = self.convert_to_wav(audio_path)
        
        # Load audio file
        with sr.AudioFile(wav_path) as source:
            audio_data = self.recognizer.record(source)
        
        try:
            # Attempt transcription
            transcript = self.recognizer.recognize_google(audio_data)
            logger.info(f"Transcription completed: {len(transcript)} characters")
            return transcript
        except sr.UnknownValueError:
            logger.error("Google Speech Recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service: {str(e)}")
            raise
    
    def detect_silence(self, audio_path: str, min_silence_len: int = 1000, 
                      silence_thresh: int = -40) -> List[Tuple[int, int]]:
        """
        Detect silent segments in audio
        
        Args:
            audio_path: Path to the audio file
            min_silence_len: Minimum length of silence in milliseconds
            silence_thresh: Silence threshold in dB
            
        Returns:
            List of (start_ms, end_ms) tuples for silent segments
        """
        # Load audio
        audio = AudioSegment.from_file(audio_path)
        
        # Detect silence using pydub's detect_silence
        from pydub.silence import detect_silence
        silence_ranges = detect_silence(
            audio, 
            min_silence_len=min_silence_len, 
            silence_thresh=silence_thresh
        )
        
        # Convert to milliseconds
        silence_ranges = [(start, end) for start, end in silence_ranges]
        
        return silence_ranges
    
    def extract_segment(self, audio_path: str, start_ms: int, end_ms: int) -> str:
        """
        Extract a segment from an audio file
        
        Args:
            audio_path: Path to the audio file
            start_ms: Start time in milliseconds
            end_ms: End time in milliseconds
            
        Returns:
            Path to the extracted segment
        """
        # Load audio
        audio = AudioSegment.from_file(audio_path)
        
        # Extract segment
        segment = audio[start_ms:end_ms]
        
        # Create output path
        output_path = os.path.join(
            self.temp_dir, 
            f"{os.path.splitext(os.path.basename(audio_path))[0]}_{start_ms}_{end_ms}.wav"
        )
        
        # Export segment
        segment.export(output_path, format="wav")
        logger.info(f"Extracted segment {start_ms}-{end_ms}ms to {output_path}")
        
        return output_path
    
    def normalize_audio(self, audio_path: str, target_dBFS: float = -20.0) -> str:
        """
        Normalize audio volume
        
        Args:
            audio_path: Path to the audio file
            target_dBFS: Target dB Full Scale level
            
        Returns:
            Path to the normalized audio
        """
        # Load audio
        audio = AudioSegment.from_file(audio_path)
        
        # Calculate change in dB
        change_in_dBFS = target_dBFS - audio.dBFS
        
        # Apply gain
        normalized_audio = audio.apply_gain(change_in_dBFS)
        
        # Create output path
        output_path = os.path.join(
            self.temp_dir, 
            f"{os.path.splitext(os.path.basename(audio_path))[0]}_normalized.wav"
        )
        
        # Export normalized audio
        normalized_audio.export(output_path, format="wav")
        logger.info(f"Normalized audio to {target_dBFS} dBFS: {output_path}")
        
        return output_path
    
    def remove_noise(self, audio_path: str) -> str:
        """
        Remove background noise from audio
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Path to the noise-reduced audio
        """
        # Load audio file
        sample_rate, audio_data = wavfile.read(audio_path)
        
        # Convert to float
        audio_data = audio_data.astype(np.float32)
        
        # Normalize
        audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Apply noise reduction
        # This is a simplified implementation using a basic filter
        # In a real implementation, you'd use more sophisticated noise reduction
        b, a = signal.butter(5, 0.1, 'high')
        filtered_audio = signal.filtfilt(b, a, audio_data)
        
        # Create output path
        output_path = os.path.join(
            self.temp_dir, 
            f"{os.path.splitext(os.path.basename(audio_path))[0]}_denoised.wav"
        )
        
        # Save filtered audio
        wavfile.write(output_path, sample_rate, (filtered_audio * 32767).astype(np.int16))
        logger.info(f"Removed noise from audio: {output_path}")
        
        return output_path
    
    def concatenate_audio(self, audio_paths: List[str], crossfade_ms: int = 500) -> str:
        """
        Concatenate multiple audio files with crossfade
        
        Args:
            audio_paths: List of paths to audio files
            crossfade_ms: Crossfade duration in milliseconds
            
        Returns:
            Path to the concatenated audio
        """
        if not audio_paths:
            raise ValueError("No audio files provided for concatenation")
        
        # Load the first audio file
        result = AudioSegment.from_file(audio_paths[0])
        
        # Add the rest with crossfade
        for audio_path in audio_paths[1:]:
            next_segment = AudioSegment.from_file(audio_path)
            result = result.append(next_segment, crossfade=crossfade_ms)
        
        # Create output path
        output_path = os.path.join(
            self.temp_dir, 
            f"concatenated_{os.path.basename(audio_paths[0])}"
        )
        
        # Export concatenated audio
        result.export(output_path, format="wav")
        logger.info(f"Concatenated {len(audio_paths)} audio files: {output_path}")
        
        return output_path
    
    def add_intro_outro(self, audio_path: str, intro_text: Optional[str] = None, 
                       outro_text: Optional[str] = None) -> str:
        """
        Add TTS intro and outro to audio
        
        Args:
            audio_path: Path to the audio file
            intro_text: Text for intro (will be converted to speech)
            outro_text: Text for outro (will be converted to speech)
            
        Returns:
            Path to the audio with intro/outro
        """
        # Load main audio
        main_audio = AudioSegment.from_file(audio_path)
        
        # Create empty segments for intro and outro
        intro_audio = AudioSegment.silent(duration=0)
        outro_audio = AudioSegment.silent(duration=0)
        
        # In a real implementation, you would use a TTS service here
        # For now, we'll just log that this would happen
        if intro_text:
            logger.info(f"Would generate TTS for intro: {intro_text}")
            # Placeholder for intro (1 second of silence)
            intro_audio = AudioSegment.silent(duration=1000)
        
        if outro_text:
            logger.info(f"Would generate TTS for outro: {outro_text}")
            # Placeholder for outro (1 second of silence)
            outro_audio = AudioSegment.silent(duration=1000)
        
        # Combine intro, main audio, and outro
        result = intro_audio + main_audio + outro_audio
        
        # Create output path
        output_path = os.path.join(
            self.temp_dir, 
            f"{os.path.splitext(os.path.basename(audio_path))[0]}_with_intro_outro.wav"
        )
        
        # Export result
        result.export(output_path, format="wav")
        logger.info(f"Added intro/outro to audio: {output_path}")
        
        return output_path
