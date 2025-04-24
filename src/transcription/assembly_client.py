"""
AssemblyAI client for speech-to-text transcription
"""

import os
import time
import logging
import assemblyai as aai
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class AssemblyClient:
    """Client for interacting with AssemblyAI API for transcription"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AssemblyAI client
        
        Args:
            api_key: AssemblyAI API key (defaults to ASSEMBLY_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ASSEMBLY_API_KEY")
        
        # Check if API key is available
        if not self.api_key:
            logger.warning("AssemblyAI API key not provided. Using placeholder responses.")
            self.using_placeholders = True
        else:
            # Configure the AssemblyAI client
            aai.settings.api_key = self.api_key
            self.using_placeholders = False
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file to text using AssemblyAI
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcription text
        """
        # If using placeholders, return dummy response
        if hasattr(self, 'using_placeholders') and self.using_placeholders:
            logger.info(f"Using placeholder transcription for {audio_path}")
            return "This is a placeholder transcript. The actual transcription would appear here."
        
        try:
            # Create a transcriber
            transcriber = aai.Transcriber()
            
            # Start transcription
            logger.info(f"Starting transcription for {audio_path}")
            transcript = transcriber.transcribe(audio_path)
            
            # Return the transcribed text
            if transcript.status == "completed":
                logger.info(f"Transcription completed: {len(transcript.text)} characters")
                return transcript.text
            else:
                logger.error(f"Transcription failed with status: {transcript.status}")
                if transcript.error:
                    logger.error(f"Error: {transcript.error}")
                return ""
        except Exception as e:
            logger.error(f"Error transcribing audio with AssemblyAI: {str(e)}")
            raise
    
    def transcribe_audio_with_speaker_diarization(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio with speaker diarization
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary with transcription and speaker information
        """
        # If using placeholders, return dummy response
        if hasattr(self, 'using_placeholders') and self.using_placeholders:
            logger.info(f"Using placeholder diarized transcription for {audio_path}")
            return {
                "text": "This is a placeholder transcript with speaker diarization.",
                "utterances": [
                    {"speaker": "A", "text": "This is speaker A talking.", "start": 0, "end": 3},
                    {"speaker": "B", "text": "This is speaker B responding.", "start": 3, "end": 6}
                ]
            }
        
        try:
            # Create a transcriber with speaker diarization
            config = aai.TranscriptionConfig(speaker_labels=True)
            transcriber = aai.Transcriber(config=config)
            
            # Start transcription
            logger.info(f"Starting diarized transcription for {audio_path}")
            transcript = transcriber.transcribe(audio_path)
            
            # Process the result
            if transcript.status == "completed":
                logger.info(f"Diarized transcription completed")
                
                # Extract utterances
                utterances = []
                for utterance in transcript.utterances:
                    utterances.append({
                        "speaker": utterance.speaker,
                        "text": utterance.text,
                        "start": utterance.start,
                        "end": utterance.end
                    })
                
                return {
                    "text": transcript.text,
                    "utterances": utterances
                }
            else:
                logger.error(f"Diarized transcription failed with status: {transcript.status}")
                if transcript.error:
                    logger.error(f"Error: {transcript.error}")
                return {"text": "", "utterances": []}
        except Exception as e:
            logger.error(f"Error with diarized transcription: {str(e)}")
            raise
    
    def detect_key_topics(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Detect key topics in the audio
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            List of topics with timestamps
        """
        # If using placeholders, return dummy response
        if hasattr(self, 'using_placeholders') and self.using_placeholders:
            logger.info(f"Using placeholder topic detection for {audio_path}")
            return [
                {"topic": "Introduction", "start": 0, "end": 60, "confidence": 0.9},
                {"topic": "Main Discussion", "start": 60, "end": 180, "confidence": 0.85},
                {"topic": "Conclusion", "start": 180, "end": 240, "confidence": 0.95}
            ]
        
        try:
            # Create a transcriber with topic detection
            config = aai.TranscriptionConfig(auto_chapters=True)
            transcriber = aai.Transcriber(config=config)
            
            # Start transcription
            logger.info(f"Starting topic detection for {audio_path}")
            transcript = transcriber.transcribe(audio_path)
            
            # Process the result
            if transcript.status == "completed" and transcript.chapters:
                logger.info(f"Topic detection completed: {len(transcript.chapters)} topics found")
                
                # Extract topics
                topics = []
                for chapter in transcript.chapters:
                    topics.append({
                        "topic": chapter.headline,
                        "start": chapter.start,
                        "end": chapter.end,
                        "summary": chapter.summary,
                        "gist": chapter.gist
                    })
                
                return topics
            else:
                logger.error(f"Topic detection failed or no topics found")
                return []
        except Exception as e:
            logger.error(f"Error detecting topics: {str(e)}")
            raise
