"""
FFmpeg-based audio processing utilities for podcast creation
"""

import os
import logging
import tempfile
import ffmpeg
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class FFmpegProcessor:
    """Audio processing utilities using FFmpeg for podcast creation"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the FFmpeg processor
        
        Args:
            temp_dir: Directory for temporary files (defaults to system temp dir)
        """
        self.temp_dir = temp_dir or os.getenv("TEMP_AUDIO_DIR", "./temp_audio")
        os.makedirs(self.temp_dir, exist_ok=True)
    
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
        
        # Create output path
        output_path = os.path.join(
            self.temp_dir, 
            f"{os.path.splitext(os.path.basename(audio_path))[0]}.wav"
        )
        
        try:
            # Convert using FFmpeg
            (
                ffmpeg
                .input(audio_path)
                .output(output_path, acodec='pcm_s16le', ar=44100, ac=2)
                .run(quiet=True, overwrite_output=True)
            )
            
            logger.info(f"Converted audio to WAV: {output_path}")
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"Error converting audio to WAV: {str(e)}")
            raise
    
    def extract_segment(self, audio_path: str, start_sec: float, end_sec: float) -> str:
        """
        Extract a segment from an audio file
        
        Args:
            audio_path: Path to the audio file
            start_sec: Start time in seconds
            end_sec: End time in seconds
            
        Returns:
            Path to the extracted segment
        """
        # Create output path
        output_path = os.path.join(
            self.temp_dir, 
            f"{os.path.splitext(os.path.basename(audio_path))[0]}_{int(start_sec)}_{int(end_sec)}.wav"
        )
        
        try:
            # Extract segment using FFmpeg
            (
                ffmpeg
                .input(audio_path, ss=start_sec, to=end_sec)
                .output(output_path, acodec='pcm_s16le', ar=44100, ac=2)
                .run(quiet=True, overwrite_output=True)
            )
            
            logger.info(f"Extracted segment {start_sec}-{end_sec}s to {output_path}")
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"Error extracting segment: {str(e)}")
            raise
    
    def normalize_audio(self, audio_path: str, target_level: float = -18.0) -> str:
        """
        Normalize audio volume
        
        Args:
            audio_path: Path to the audio file
            target_level: Target loudness level in dB
            
        Returns:
            Path to the normalized audio
        """
        # Create output path
        output_path = os.path.join(
            self.temp_dir, 
            f"{os.path.splitext(os.path.basename(audio_path))[0]}_normalized.wav"
        )
        
        try:
            # Normalize using FFmpeg with loudnorm filter
            (
                ffmpeg
                .input(audio_path)
                .filter('loudnorm', i=target_level, lra=7.0, tp=-2.0)
                .output(output_path, acodec='pcm_s16le', ar=44100, ac=2)
                .run(quiet=True, overwrite_output=True)
            )
            
            logger.info(f"Normalized audio to {target_level} dB: {output_path}")
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"Error normalizing audio: {str(e)}")
            raise
    
    def remove_noise(self, audio_path: str, noise_reduction_amount: float = 0.2) -> str:
        """
        Remove background noise from audio
        
        Args:
            audio_path: Path to the audio file
            noise_reduction_amount: Amount of noise reduction (0.0-1.0)
            
        Returns:
            Path to the noise-reduced audio
        """
        # Create output path
        output_path = os.path.join(
            self.temp_dir, 
            f"{os.path.splitext(os.path.basename(audio_path))[0]}_denoised.wav"
        )
        
        try:
            # Apply noise reduction using FFmpeg with afftdn filter
            (
                ffmpeg
                .input(audio_path)
                .filter('afftdn', nr=noise_reduction_amount*10, nf=noise_reduction_amount*5)
                .output(output_path, acodec='pcm_s16le', ar=44100, ac=2)
                .run(quiet=True, overwrite_output=True)
            )
            
            logger.info(f"Removed noise from audio: {output_path}")
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"Error removing noise: {str(e)}")
            raise
    
    def concatenate_audio(self, audio_paths: List[str], crossfade_duration: float = 0.5) -> str:
        """
        Concatenate multiple audio files with crossfade
        
        Args:
            audio_paths: List of paths to audio files
            crossfade_duration: Crossfade duration in seconds
            
        Returns:
            Path to the concatenated audio
        """
        if not audio_paths:
            raise ValueError("No audio files provided for concatenation")
        
        # Create output path
        output_path = os.path.join(
            self.temp_dir, 
            f"concatenated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        )
        
        try:
            # Create a complex filtergraph for concatenation with crossfade
            if len(audio_paths) == 1:
                # Just copy if only one file
                (
                    ffmpeg
                    .input(audio_paths[0])
                    .output(output_path, acodec='pcm_s16le', ar=44100, ac=2)
                    .run(quiet=True, overwrite_output=True)
                )
            else:
                # Build filter complex for concatenation with crossfade
                inputs = []
                for path in audio_paths:
                    inputs.append(ffmpeg.input(path))
                
                # Create filter_complex string
                filter_complex = []
                for i in range(len(audio_paths)):
                    filter_complex.append(f"[{i}:a]")
                
                filter_complex.append(f"concat=n={len(audio_paths)}:v=0:a=1")
                
                if crossfade_duration > 0:
                    filter_complex.append(f"acrossfade=d={crossfade_duration}")
                
                filter_complex.append("[out]")
                
                # Run FFmpeg command
                (
                    ffmpeg
                    .output(*inputs, output_path, filter_complex=''.join(filter_complex), map="[out]", acodec='pcm_s16le', ar=44100, ac=2)
                    .run(quiet=True, overwrite_output=True)
                )
            
            logger.info(f"Concatenated {len(audio_paths)} audio files: {output_path}")
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"Error concatenating audio: {str(e)}")
            raise
    
    def get_audio_duration(self, audio_path: str) -> float:
        """
        Get the duration of an audio file in seconds
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Duration in seconds
        """
        try:
            # Get audio information
            probe = ffmpeg.probe(audio_path)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            if audio_stream:
                duration = float(audio_stream.get('duration', 0))
                logger.info(f"Audio duration: {duration} seconds")
                return duration
            else:
                logger.warning(f"No audio stream found in {audio_path}")
                return 0
        except ffmpeg.Error as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return 0
    
    def export_as_mp3(self, audio_path: str, bitrate: str = '192k') -> str:
        """
        Export audio as MP3
        
        Args:
            audio_path: Path to the audio file
            bitrate: MP3 bitrate
            
        Returns:
            Path to the MP3 file
        """
        # Create output path
        output_path = os.path.join(
            os.path.dirname(audio_path), 
            f"{os.path.splitext(os.path.basename(audio_path))[0]}.mp3"
        )
        
        try:
            # Convert to MP3 using FFmpeg
            (
                ffmpeg
                .input(audio_path)
                .output(output_path, acodec='libmp3lame', ab=bitrate, ar=44100, ac=2)
                .run(quiet=True, overwrite_output=True)
            )
            
            logger.info(f"Exported audio as MP3: {output_path}")
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"Error exporting as MP3: {str(e)}")
            raise
