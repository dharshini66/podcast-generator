"""
Podcast generation from meeting recordings
"""

import os
import json
import logging
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from src.transcription.assembly_client import AssemblyClient
from src.audio.ffmpeg_processor import FFmpegProcessor
from src.tts.voice_generator import VoiceGenerator

logger = logging.getLogger(__name__)

class PodcastGenerator:
    """Generate podcast snippets from meeting recordings"""
    
    def __init__(self, assembly_client: AssemblyClient, ffmpeg_processor: FFmpegProcessor,
                voice_generator: VoiceGenerator, output_dir: Optional[str] = None):
        """
        Initialize the podcast generator
        
        Args:
            assembly_client: Initialized AssemblyAI client
            ffmpeg_processor: Initialized FFmpeg processor
            voice_generator: Initialized voice generator
            output_dir: Directory to save podcast output (defaults to ./output_podcasts)
        """
        self.assembly_client = assembly_client
        self.ffmpeg_processor = ffmpeg_processor
        self.voice_generator = voice_generator
        
        self.output_dir = output_dir or os.getenv("OUTPUT_DIR", "./output_podcasts")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_from_file(self, audio_path: str, meeting_title: Optional[str] = None,
                         use_voice_narration: bool = True) -> List[str]:
        """
        Generate podcast snippets from an audio file
        
        Args:
            audio_path: Path to the audio file
            meeting_title: Optional title for the meeting
            use_voice_narration: Whether to add AI voice narration
            
        Returns:
            List of paths to generated podcast snippets
        """
        logger.info(f"Generating podcast from file: {audio_path}")
        
        # Set default meeting title if not provided
        if not meeting_title:
            meeting_title = f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Step 1: Convert audio to WAV if needed
        wav_path = self.ffmpeg_processor.convert_to_wav(audio_path)
        
        # Step 2: Transcribe audio
        logger.info("Transcribing audio...")
        transcript = self.assembly_client.transcribe_audio(wav_path)
        
        # Step 3: Analyze transcript to identify key segments
        logger.info("Analyzing transcript for key segments...")
        segments = self.analyze_transcript(transcript)
        
        # Step 4: Process each segment
        podcast_paths = []
        
        for i, segment in enumerate(segments):
            logger.info(f"Processing segment {i+1}/{len(segments)}: {segment.get('title')}")
            
            # Extract segment from audio
            segment_path = self._process_segment(
                wav_path, 
                segment, 
                meeting_title,
                use_voice_narration,
                i
            )
            
            podcast_paths.append(segment_path)
        
        logger.info(f"Generated {len(podcast_paths)} podcast segments")
        return podcast_paths
    
    def analyze_transcript(self, transcript: str) -> List[Dict[str, Any]]:
        """
        Analyze transcript to identify key segments for podcast
        
        Args:
            transcript: Full transcript text
            
        Returns:
            List of segment definitions with timestamps
        """
        # Try to use AssemblyAI's topic detection if available
        try:
            # This is a simplified implementation
            # In a real implementation, you would use more sophisticated analysis
            
            # Split transcript into paragraphs
            paragraphs = [p for p in transcript.split('\n\n') if p.strip()]
            
            # If too few paragraphs, split by sentences
            if len(paragraphs) < 3:
                import re
                paragraphs = re.split(r'(?<=[.!?])\s+', transcript)
            
            # Calculate approximate timestamps (assuming 150 words per minute)
            words = transcript.split()
            total_words = len(words)
            total_duration = total_words / 150 * 60  # in seconds
            
            # Create segments
            segments = []
            words_so_far = 0
            
            for i, paragraph in enumerate(paragraphs):
                if i % 3 == 0 and i < len(paragraphs) - 1:  # Create a segment every 3 paragraphs
                    # Calculate start and end times
                    para_words = sum(len(p.split()) for p in paragraphs[i:min(i+3, len(paragraphs))])
                    start_time = words_so_far / total_words * total_duration
                    end_time = (words_so_far + para_words) / total_words * total_duration
                    words_so_far += para_words
                    
                    # Create segment
                    segment_text = ' '.join(paragraphs[i:min(i+3, len(paragraphs))])
                    segments.append({
                        'title': f"Segment {i//3 + 1}",
                        'description': segment_text[:100] + "...",
                        'text': segment_text,
                        'start_time': start_time,
                        'end_time': end_time,
                        'key_points': self._extract_key_points(segment_text)
                    })
            
            # Ensure we have at least one segment
            if not segments:
                segments.append({
                    'title': "Full Recording",
                    'description': transcript[:100] + "...",
                    'text': transcript,
                    'start_time': 0,
                    'end_time': total_duration,
                    'key_points': self._extract_key_points(transcript)
                })
            
            return segments
            
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            
            # Fallback: create a single segment with the entire recording
            return [{
                'title': "Full Recording",
                'description': transcript[:100] + "...",
                'text': transcript,
                'start_time': 0,
                'end_time': 300,  # Default to 5 minutes
                'key_points': self._extract_key_points(transcript)
            }]
    
    def _extract_key_points(self, text: str, max_points: int = 3) -> List[str]:
        """
        Extract key points from text
        
        Args:
            text: Text to analyze
            max_points: Maximum number of key points to extract
            
        Returns:
            List of key points
        """
        # This is a simplified implementation
        # In a real implementation, you would use NLP to extract key points
        
        # Split into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter out short sentences
        sentences = [s for s in sentences if len(s.split()) > 5]
        
        # Select sentences that might be key points (every N sentences)
        if len(sentences) <= max_points:
            return sentences
        else:
            step = len(sentences) // max_points
            return [sentences[i] for i in range(0, len(sentences), step)][:max_points]
    
    def _process_segment(self, audio_path: str, segment: Dict[str, Any], 
                       meeting_title: str, use_voice_narration: bool,
                       segment_index: int) -> str:
        """
        Process a single segment to create a podcast snippet
        
        Args:
            audio_path: Path to the full audio file
            segment: Segment definition from analysis
            meeting_title: Title of the meeting
            use_voice_narration: Whether to add AI voice narration
            segment_index: Index of the segment
            
        Returns:
            Path to the generated podcast snippet
        """
        # Get segment title
        segment_title = segment.get('title', f"Segment {segment_index+1}")
        
        # Get segment description
        segment_description = segment.get('description', '')
        
        # Get segment timestamps
        start_time = segment.get('start_time', 0)
        end_time = segment.get('end_time', 60)  # Default to 1 minute
        
        # Extract segment from audio
        segment_path = self.ffmpeg_processor.extract_segment(audio_path, start_time, end_time)
        
        # Enhance audio quality
        segment_path = self.ffmpeg_processor.normalize_audio(segment_path)
        segment_path = self.ffmpeg_processor.remove_noise(segment_path)
        
        # Add voice narration if requested
        if use_voice_narration:
            intro_text = f"Here's a quick snippet from our session on {segment_title}..."
            outro_text = "That was an interesting point from the meeting."
            
            segment_path = self.voice_generator.add_narration(
                segment_path,
                intro_text,
                outro_text
            )
        
        # Create output path
        safe_title = "".join(c if c.isalnum() else "_" for c in segment_title)
        output_path = os.path.join(
            self.output_dir,
            f"podcast_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        )
        
        # Copy to output directory
        import shutil
        shutil.copy(segment_path, output_path)
        
        # Get duration
        duration_sec = self.ffmpeg_processor.get_audio_duration(output_path)
        
        # Create metadata file
        metadata = {
            "title": segment_title,
            "description": segment_description,
            "meeting_title": meeting_title,
            "created_at": datetime.now().isoformat(),
            "duration_sec": duration_sec,
            "key_points": segment.get('key_points', [])
        }
        
        metadata_path = os.path.splitext(output_path)[0] + '.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create MP3 version for better compatibility
        try:
            mp3_path = self.ffmpeg_processor.export_as_mp3(output_path)
            
            # Update metadata for MP3
            mp3_metadata_path = os.path.splitext(mp3_path)[0] + '.json'
            with open(mp3_metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Created podcast segment: {mp3_path}")
            return mp3_path
        except Exception as e:
            logger.error(f"Error creating MP3 version: {str(e)}")
            logger.info(f"Created podcast segment: {output_path}")
            return output_path
