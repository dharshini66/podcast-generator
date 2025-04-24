"""
Google Gemini API client for AI text and audio processing
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import Google Generative AI, but provide a fallback if it's not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI not available. AI analysis functionality will be limited.")
    GEMINI_AVAILABLE = False
    # Define a dummy module for compatibility
    class GenaiDummy:
        def configure(self, api_key=None):
            pass
            
        def list_models(self):
            return []
            
        class GenerativeModel:
            def __init__(self, model_name):
                self.model_name = model_name
                
            def generate_content(self, prompt):
                class Response:
                    def __init__(self, text):
                        self.text = text
                
                return Response(f"This is a placeholder response. Google Gemini API is not available.\n\nPrompt: {prompt[:100]}...")
    
    genai = GenaiDummy()

class GeminiClient:
    """Client for interacting with Google's Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini API client
        
        Args:
            api_key: Google Gemini API key (defaults to GOOGLE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        # Check if API key is available
        if not self.api_key:
            logger.warning("Google Gemini API key not provided. Using placeholder responses.")
            self.api_key = "dummy_key"
            self.using_placeholders = True
        else:
            self.using_placeholders = False
        
        # Configure the Gemini API if available
        if GEMINI_AVAILABLE:
            # Configure the Gemini API
            genai.configure(api_key=self.api_key)
            
            # Get available models
            self.models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            logger.info(f"Available Gemini models: {[model.name for model in self.models]}")
            
            # Select the most capable model for our use case
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info(f"Using Gemini model: {self.model.model_name}")
        else:
            # Use dummy model
            self.models = []
            self.model = genai.GenerativeModel('gemini-pro')
            logger.warning("Using placeholder Gemini model due to unavailable API.")
    
    def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze meeting transcript to identify key segments for podcast creation
        
        Args:
            transcript: Full meeting transcript text
            
        Returns:
            Dictionary containing analysis results with key segments and metadata
        """
        prompt = f"""
        Analyze the following meeting transcript and identify 3-5 key segments that would make 
        engaging podcast snippets. For each segment:
        
        1. Identify the start and end points (approximate timestamps or paragraph numbers)
        2. Suggest a title for the snippet
        3. Write a brief description of the content
        4. Explain why this segment would be interesting as a podcast
        5. Rate the segment's potential audience engagement on a scale of 1-10
        
        Meeting Transcript:
        {transcript}
        
        Format your response as a structured JSON with an array of segments.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract and parse the JSON response
            # Note: In a real implementation, you'd want more robust parsing
            analysis_results = response.text
            
            # For now, we'll return a simplified version
            # In production, you'd parse the JSON properly
            return {
                "segments": analysis_results,
                "raw_response": response.text
            }
        except Exception as e:
            logger.error(f"Error analyzing transcript with Gemini: {str(e)}")
            raise
    
    def generate_podcast_intro(self, meeting_title: str, segment_title: str, 
                              segment_description: str) -> str:
        """
        Generate an engaging introduction for a podcast segment
        
        Args:
            meeting_title: Title of the original meeting
            segment_title: Title of the podcast segment
            segment_description: Description of the segment content
            
        Returns:
            Generated introduction text
        """
        prompt = f"""
        Create a brief, engaging podcast introduction for a segment extracted from a meeting.
        
        Meeting title: {meeting_title}
        Segment title: {segment_title}
        Segment description: {segment_description}
        
        The introduction should be conversational, engaging, and brief (30-60 words).
        It should set context for the listener and make them want to hear the segment.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating podcast intro with Gemini: {str(e)}")
            raise
    
    def generate_podcast_outro(self, segment_title: str, key_points: List[str]) -> str:
        """
        Generate a conclusion for a podcast segment
        
        Args:
            segment_title: Title of the podcast segment
            key_points: List of key points from the segment
            
        Returns:
            Generated outro text
        """
        prompt = f"""
        Create a brief, engaging conclusion for a podcast segment.
        
        Segment title: {segment_title}
        Key points from the segment:
        {' '.join(['- ' + point for point in key_points])}
        
        The conclusion should summarize the key takeaways and be brief (20-40 words).
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating podcast outro with Gemini: {str(e)}")
            raise
    
    def extract_key_points(self, segment_transcript: str, max_points: int = 3) -> List[str]:
        """
        Extract key points from a segment transcript
        
        Args:
            segment_transcript: Transcript of the segment
            max_points: Maximum number of key points to extract
            
        Returns:
            List of key points as strings
        """
        prompt = f"""
        Extract the {max_points} most important points from this meeting segment transcript.
        Each point should be a single sentence that captures a key insight or decision.
        
        Transcript:
        {segment_transcript}
        
        Format your response as a numbered list.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Parse the response to extract the key points
            # This is a simplified implementation
            lines = response.text.strip().split('\n')
            key_points = [line.strip() for line in lines if line.strip()]
            
            # Limit to max_points
            return key_points[:max_points]
        except Exception as e:
            logger.error(f"Error extracting key points with Gemini: {str(e)}")
            raise
