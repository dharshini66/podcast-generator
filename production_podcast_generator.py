import os
import sys
import time
import json
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PodcastGenerator:
    """
    Production-ready AI Podcast Generator that creates podcast snippets from meeting recordings.
    Uses AssemblyAI for transcription, FFmpeg for audio processing, and 
    ElevenLabs for voice narration.
    """
    
    def __init__(self):
        # Load API keys and settings from environment
        self.assembly_api_key = os.getenv("ASSEMBLY_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.ffmpeg_path = os.getenv("FFMPEG_PATH")
        
        # Set up directories
        self.temp_dir = os.getenv("TEMP_AUDIO_DIR", "./temp_audio")
        self.output_dir = os.getenv("OUTPUT_DIR", "./output_podcasts")
        
        # Create directories if they don't exist
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize API clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize API clients with proper error handling"""
        self.transcription_available = False
        self.voice_available = False
        self.ffmpeg_available = False
        
        # Try to initialize AssemblyAI
        try:
            import assemblyai as aai
            aai.settings.api_key = self.assembly_api_key
            self.transcriber = aai.Transcriber()
            self.transcription_available = True
            print("[SUCCESS] AssemblyAI transcription service initialized")
        except Exception as e:
            print(f"[FAILED] AssemblyAI initialization failed: {str(e)}")
            print("  Using placeholder transcription instead")
        
        # Try to initialize ElevenLabs
        try:
            import elevenlabs
            elevenlabs.api_key = self.elevenlabs_api_key
            self.voice_available = True
            print("[SUCCESS] ElevenLabs voice service initialized")
        except Exception as e:
            print(f"[FAILED] ElevenLabs initialization failed: {str(e)}")
            print("  Using placeholder voice generation instead")
        
        # Check if FFmpeg is available
        if self.ffmpeg_path and os.path.exists(self.ffmpeg_path):
            self.ffmpeg_available = True
            print(f"[SUCCESS] FFmpeg found at: {self.ffmpeg_path}")
        else:
            # Try to find FFmpeg in the project directory
            ffmpeg_paths = [
                os.path.join(os.getcwd(), "ffmpeg", "ffmpeg-7.1.1-essentials_build", "bin", "ffmpeg.exe"),
                os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe"),
                "C:/Users/dhars/OneDrive/Desktop/hackathon 3.0/ffmpeg/ffmpeg-7.1.1-essentials_build/bin/ffmpeg.exe"
            ]
            
            for path in ffmpeg_paths:
                if os.path.exists(path):
                    self.ffmpeg_path = path
                    self.ffmpeg_available = True
                    print(f"[SUCCESS] FFmpeg found at: {path}")
                    break
            
            # If still not found, try system PATH
            if not self.ffmpeg_available:
                try:
                    import subprocess
                    subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    self.ffmpeg_available = True
                    print("[SUCCESS] FFmpeg found in system PATH")
                except Exception:
                    print("[FAILED] FFmpeg not found. Audio processing will be limited.")
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio file using AssemblyAI"""
        print(f"\nTranscribing audio: {os.path.basename(audio_path)}")
        
        if not os.path.exists(audio_path):
            print(f"Error: Audio file not found at {audio_path}")
            return None
        
        # Check if this is a simulated audio file (JSON)
        if audio_path.endswith('.json'):
            try:
                with open(audio_path, 'r') as f:
                    data = json.load(f)
                if 'transcript' in data:
                    print("Using transcript from simulated audio file")
                    return data['transcript']
            except Exception as e:
                print(f"Error reading simulated audio file: {str(e)}")
        
        if self.transcription_available:
            try:
                import assemblyai as aai
                print("Uploading to AssemblyAI (this may take a moment)...")
                transcript = self.transcriber.transcribe(audio_path)
                print("Transcription complete!")
                return transcript.text
            except Exception as e:
                print(f"Transcription error: {str(e)}")
        
        print("Transcription failed. Please check your AssemblyAI API key.")
        return None
    
    def extract_key_points(self, transcript, max_points=5):
        """Extract key points from transcript"""
        print("\nExtracting key points from transcript...")
        
        if not transcript:
            return []
        
        # Simple extraction - in a real implementation, this would use more sophisticated NLP
        sentences = transcript.split(". ")
        key_points = []
        
        # Take every third sentence as a key point (simplified approach)
        for i, sentence in enumerate(sentences):
            if i % 3 == 0 and len(sentence) > 20:  # Only longer sentences
                key_points.append(sentence)
        
        # Limit to max_points
        key_points = key_points[:max_points]
        
        print(f"Extracted {len(key_points)} key points")
        return key_points
    
    def generate_voice(self, text, output_path=None):
        """Generate voice using ElevenLabs"""
        if not output_path:
            timestamp = int(time.time())
            output_path = os.path.join(self.temp_dir, f"narration_{timestamp}.mp3")
        
        print(f"\nGenerating voice narration for: {text[:50]}...")
        
        if self.voice_available:
            try:
                # Direct API call to ElevenLabs
                import requests
                url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # Default voice ID
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.elevenlabs_api_key
                }
                data = {
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.5
                    }
                }
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()
                audio = response.content
                
                # Save the audio to file
                with open(output_path, "wb") as f:
                    f.write(audio)
                
                print(f"Voice narration saved to: {output_path}")
                return output_path
            except Exception as e:
                print(f"Voice generation error: {str(e)}")
        
        print("Voice generation failed. Using FFmpeg to create silent audio.")
        
        # Create a silent audio file as a fallback
        if self.ffmpeg_available:
            try:
                silent_cmd = [
                    self.ffmpeg_path,
                    "-f", "lavfi",
                    "-i", "anullsrc=r=44100:cl=mono",
                    "-t", "3",  # 3 seconds of silence
                    "-q:a", "0",
                    "-y",
                    output_path
                ]
                subprocess.run(silent_cmd, check=True, capture_output=True)
                print(f"Created silent audio at: {output_path}")
                return output_path
            except Exception as e:
                print(f"Error creating silent audio: {str(e)}")
        
        # Create a placeholder text file as a last resort
        placeholder_path = os.path.join(self.temp_dir, f"placeholder_voice_{int(time.time())}.txt")
        with open(placeholder_path, "w") as f:
            f.write(f"PLACEHOLDER VOICE FILE\nText: {text}\n")
        
        return placeholder_path
    
    def concatenate_audio(self, audio_files, output_path=None):
        """Concatenate multiple audio files using FFmpeg"""
        if not output_path:
            timestamp = int(time.time())
            output_path = os.path.join(self.output_dir, f"podcast_{timestamp}.mp3")
        
        if not self.ffmpeg_available:
            print(f"FFmpeg not available. Cannot concatenate audio files.")
            return None
        
        # Filter out non-audio files
        audio_files = [f for f in audio_files if f.endswith(('.mp3', '.wav'))]
        
        if not audio_files:
            print("No audio files to concatenate.")
            return None
        
        try:
            # Create a temporary file list for FFmpeg
            file_list_path = os.path.join(self.temp_dir, f"filelist_{int(time.time())}.txt")
            with open(file_list_path, "w") as f:
                for audio_file in audio_files:
                    if os.path.exists(audio_file):
                        f.write(f"file '{os.path.abspath(audio_file)}'\n")
            
            # Run FFmpeg to concatenate the files
            ffmpeg_cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", file_list_path,
                "-c", "copy",
                "-y",
                output_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            print(f"Concatenated audio saved to: {output_path}")
            
            # Clean up the temporary file list
            os.remove(file_list_path)
            
            return output_path
        except Exception as e:
            print(f"Error concatenating audio: {str(e)}")
            return None
    
    def generate_podcast(self, audio_path, title=None):
        """Generate a podcast from an audio file"""
        if not title:
            title = os.path.basename(audio_path).split(".")[0]
        
        print("\n" + "=" * 60)
        print(f"Generating podcast for: {title}")
        print("=" * 60)
        
        # Step 1: Transcribe the audio
        transcript = self.transcribe_audio(audio_path)
        if not transcript:
            print("Transcription failed. Cannot generate podcast.")
            return None
        
        # Step 2: Extract key points
        key_points = self.extract_key_points(transcript)
        if not key_points:
            print("No key points extracted. Cannot generate podcast.")
            return None
        
        # Step 3: Generate intro and outro
        intro_text = f"Welcome to this podcast about {title}. Here are the key highlights from this meeting."
        outro_text = f"That concludes our podcast summary of {title}. Thank you for listening!"
        
        intro_audio = self.generate_voice(intro_text)
        outro_audio = self.generate_voice(outro_text)
        
        # Step 4: Generate podcast segments
        podcast_segments = []
        audio_files = []
        
        # Add intro
        if intro_audio and intro_audio.endswith(('.mp3', '.wav')):
            audio_files.append(intro_audio)
        
        # Process each key point
        for i, point in enumerate(key_points):
            segment_title = f"Key Point {i+1}"
            narration_text = f"Key point {i+1}: {point}"
            narration_audio = self.generate_voice(narration_text)
            
            if narration_audio and narration_audio.endswith(('.mp3', '.wav')):
                audio_files.append(narration_audio)
            
            podcast_segments.append({
                "title": segment_title,
                "text": point,
                "narration": narration_audio
            })
        
        # Add outro
        if outro_audio and outro_audio.endswith(('.mp3', '.wav')):
            audio_files.append(outro_audio)
        
        # Step 5: Concatenate all audio files if FFmpeg is available
        final_podcast = None
        if self.ffmpeg_available and audio_files:
            timestamp = int(time.time())
            final_podcast = os.path.join(self.output_dir, f"podcast_{timestamp}.mp3")
            self.concatenate_audio(audio_files, final_podcast)
        
        # Step 6: Save podcast information
        timestamp = int(time.time())
        podcast_info_path = os.path.join(self.output_dir, f"podcast_{timestamp}.txt")
        
        with open(podcast_info_path, "w") as f:
            f.write(f"PODCAST: {title}\n")
            f.write(f"Generated: {time.ctime()}\n\n")
            f.write(f"INTRO: {intro_text}\n")
            f.write("KEY POINTS:\n")
            
            for i, segment in enumerate(podcast_segments):
                f.write(f"\n{i+1}. {segment['title']}\n")
                f.write(f"   {segment['text']}\n")
            
            f.write(f"\nOUTRO: {outro_text}\n")
            
            if final_podcast:
                f.write(f"\nFULL PODCAST AUDIO: {os.path.basename(final_podcast)}\n")
        
        print("\n" + "=" * 60)
        print(f"Podcast generation complete!")
        print(f"Podcast information saved to: {podcast_info_path}")
        if final_podcast:
            print(f"Podcast audio saved to: {final_podcast}")
        print("=" * 60)
        
        return {
            "info": podcast_info_path,
            "audio": final_podcast
        }

def process_audio_file(audio_path, title=None):
    """Process an audio file and generate a podcast"""
    generator = PodcastGenerator()
    return generator.generate_podcast(audio_path, title)

if __name__ == "__main__":
    # Check if an audio file was provided as a command-line argument
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        title = sys.argv[2] if len(sys.argv) > 2 else None
        
        if os.path.exists(audio_path):
            process_audio_file(audio_path, title)
        else:
            print(f"Error: Audio file not found at {audio_path}")
    else:
        print("Usage: python production_podcast_generator.py <audio_file_path> [title]")
        print("\nExample: python production_podcast_generator.py meeting_recording.mp3 'Quarterly Meeting'")
