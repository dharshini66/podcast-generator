import os
import sys
import time
import tempfile
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIPodcastGenerator:
    """
    AI Podcast Generator that creates podcast snippets from meeting recordings.
    Uses AssemblyAI for transcription, FFmpeg for audio processing, and 
    ElevenLabs/Google TTS for voice narration.
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
        
        # Default settings
        self.settings = {
            "max_podcast_length": 300,  # 5 minutes in seconds
            "voice_name": "Bella",      # Default ElevenLabs voice
            "intro_template": "Welcome to this podcast about {title}. Here are the key highlights from this meeting.",
            "outro_template": "That concludes our podcast summary of {title}. Thank you for listening!",
            "segment_template": "Key point {number}: {text}",
            "add_background_music": False,
            "background_music_volume": 0.1
        }
    
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
        except (ImportError, Exception) as e:
            print(f"[FAILED] AssemblyAI initialization failed: {str(e)}")
            print("  Using placeholder transcription instead")
        
        # Try to initialize ElevenLabs
        try:
            import elevenlabs
            elevenlabs.api_key = self.elevenlabs_api_key
            self.voice_available = True
            print("[SUCCESS] ElevenLabs voice service initialized")
        except (ImportError, Exception) as e:
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
                os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
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
                except (subprocess.SubprocessError, FileNotFoundError):
                    print("[FAILED] FFmpeg not found. Audio processing will be limited.")
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio file using AssemblyAI or placeholder"""
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
                print("Using placeholder transcription instead")
        
        # Placeholder transcription for testing
        print("Using placeholder transcription")
        return "This is a placeholder transcription. The actual transcription would appear here if AssemblyAI was properly configured."
    
    def extract_key_points(self, transcript, max_points=5):
        """Extract key points from transcript using NLP techniques"""
        print("\nExtracting key points from transcript...")
        
        if not transcript:
            return []
        
        # If we have the Google API key, use it for better extraction
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            try:
                from langchain.llms import GooglePalm
                from langchain.prompts import PromptTemplate
                
                llm = GooglePalm(google_api_key=google_api_key)
                prompt = PromptTemplate(
                    input_variables=["transcript"],
                    template="""
                    Extract the 5 most important key points from this meeting transcript.
                    Format each key point as a single sentence that captures the main idea.
                    
                    Transcript:
                    {transcript}
                    
                    Key Points:
                    """
                )
                
                result = llm(prompt.format(transcript=transcript))
                key_points = [point.strip() for point in result.split("\n") if point.strip()]
                key_points = key_points[:max_points]
                
                print(f"Extracted {len(key_points)} key points using Google Palm")
                return key_points
            except Exception as e:
                print(f"Error using Google Palm for extraction: {str(e)}")
                print("Falling back to simple extraction method")
        
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
        """Generate voice using ElevenLabs or placeholder"""
        if not output_path:
            timestamp = int(time.time())
            output_path = os.path.join(self.temp_dir, f"narration_{timestamp}.mp3")
        
        print(f"\nGenerating voice narration for: {text[:50]}...")
        
        if self.voice_available:
            try:
                import elevenlabs
                # Check which API version is available
                if hasattr(elevenlabs, 'generate'):
                    # New API version
                    audio = elevenlabs.generate(
                        text=text,
                        voice=self.settings["voice_name"],
                        model="eleven_monolingual_v1"
                    )
                elif hasattr(elevenlabs, 'voices') and hasattr(elevenlabs, 'Voice') and hasattr(elevenlabs, 'generate_and_play_audio'):
                    # Alternative API version
                    voices = elevenlabs.voices()
                    voice = next((v for v in voices if v.name.lower() == self.settings["voice_name"].lower()), voices[0])
                    audio = elevenlabs.generate_and_play_audio(
                        text=text,
                        voice=voice,
                        play=False
                    )
                else:
                    # Try direct API call
                    import requests
                    url = f"https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # Default voice ID
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
                print("Using placeholder voice instead")
        
        # If ElevenLabs fails, try Google TTS
        google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if google_creds and os.path.exists(google_creds):
            try:
                from google.cloud import texttospeech
                
                client = texttospeech.TextToSpeechClient()
                synthesis_input = texttospeech.SynthesisInput(text=text)
                
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                )
                
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                
                response = client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                )
                
                with open(output_path, "wb") as out:
                    out.write(response.audio_content)
                
                print(f"Google TTS voice narration saved to: {output_path}")
                return output_path
            except Exception as e:
                print(f"Google TTS error: {str(e)}")
                print("Using placeholder voice instead")
        
        # Create a placeholder audio file
        print("Using placeholder voice file")
        placeholder_path = os.path.join(self.temp_dir, f"placeholder_voice_{int(time.time())}.txt")
        with open(placeholder_path, "w") as f:
            f.write(f"PLACEHOLDER VOICE FILE\nText: {text}\n")
        
        return placeholder_path
    
    def extract_audio_segment(self, audio_path, start_time, end_time, output_path=None):
        """Extract a segment of audio using FFmpeg"""
        if not output_path:
            timestamp = int(time.time())
            output_path = os.path.join(self.temp_dir, f"segment_{timestamp}.mp3")
        
        if not self.ffmpeg_available:
            print(f"FFmpeg not available. Cannot extract audio segment.")
            return None
        
        try:
            import subprocess
            
            ffmpeg_cmd = [
                self.ffmpeg_path,
                "-i", audio_path,
                "-ss", str(start_time),
                "-to", str(end_time),
                "-c:a", "libmp3lame",
                "-q:a", "2",
                output_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            print(f"Extracted audio segment to: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error extracting audio segment: {str(e)}")
            return None
    
    def concatenate_audio(self, audio_files, output_path=None):
        """Concatenate multiple audio files using FFmpeg"""
        if not output_path:
            timestamp = int(time.time())
            output_path = os.path.join(self.output_dir, f"podcast_{timestamp}.mp3")
        
        if not self.ffmpeg_available:
            print(f"FFmpeg not available. Cannot concatenate audio files.")
            return None
        
        try:
            # Create a temporary file list for FFmpeg
            file_list_path = os.path.join(self.temp_dir, f"filelist_{int(time.time())}.txt")
            with open(file_list_path, "w") as f:
                for audio_file in audio_files:
                    if os.path.exists(audio_file):
                        f.write(f"file '{os.path.abspath(audio_file)}'\n")
            
            # Run FFmpeg to concatenate the files
            import subprocess
            
            ffmpeg_cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", file_list_path,
                "-c", "copy",
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
        intro_text = self.settings["intro_template"].format(title=title)
        outro_text = self.settings["outro_template"].format(title=title)
        
        intro_audio = self.generate_voice(intro_text)
        outro_audio = self.generate_voice(outro_text)
        
        # Step 4: Generate podcast segments
        podcast_segments = []
        audio_files = []
        
        # Add intro
        if intro_audio:
            audio_files.append(intro_audio)
        
        # Process each key point
        for i, point in enumerate(key_points):
            segment_title = f"Key Point {i+1}"
            narration_text = self.settings["segment_template"].format(number=i+1, text=point)
            narration_audio = self.generate_voice(narration_text)
            
            if narration_audio:
                audio_files.append(narration_audio)
            
            podcast_segments.append({
                "title": segment_title,
                "text": point,
                "narration": narration_audio
            })
        
        # Add outro
        if outro_audio:
            audio_files.append(outro_audio)
        
        # Step 5: Concatenate all audio files if FFmpeg is available
        final_podcast = None
        if self.ffmpeg_available and all(audio_file.endswith('.mp3') for audio_file in audio_files):
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
        
        # Step 7: Create a JSON metadata file
        podcast_meta_path = os.path.join(self.output_dir, f"podcast_{timestamp}.json")
        
        metadata = {
            "title": title,
            "timestamp": timestamp,
            "date_generated": time.ctime(),
            "intro": intro_text,
            "outro": outro_text,
            "key_points": [{"title": segment["title"], "text": segment["text"]} for segment in podcast_segments],
            "audio_file": os.path.basename(final_podcast) if final_podcast else None
        }
        
        with open(podcast_meta_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        print("\n" + "=" * 60)
        print(f"Podcast generation complete!")
        print(f"Podcast information saved to: {podcast_info_path}")
        if final_podcast:
            print(f"Podcast audio saved to: {final_podcast}")
        print("=" * 60)
        
        return {
            "info": podcast_info_path,
            "audio": final_podcast,
            "metadata": podcast_meta_path
        }
    
    def update_settings(self, new_settings):
        """Update the podcast generator settings"""
        self.settings.update(new_settings)
        print("Settings updated successfully!")
        return self.settings

def print_menu():
    """Print the main menu"""
    print("\n" + "=" * 60)
    print("AI Podcast Generator".center(60))
    print("=" * 60)
    print("1. Generate Podcast from Audio File")
    print("2. View Generated Podcasts")
    print("3. Configure Settings")
    print("4. Exit")
    choice = input("\nSelect an option (1-4): ")
    return choice

def main():
    # Initialize the podcast generator
    generator = AIPodcastGenerator()
    
    while True:
        try:
            choice = print_menu()
            
            if choice == "1":
                # Get audio file path
                print("\nEnter the path to your audio file (MP3 or WAV):")
                audio_path = input("> ").strip()
                
                if not audio_path:
                    print("No file specified. Returning to menu.")
                    continue
                
                if not os.path.exists(audio_path):
                    print(f"File not found: {audio_path}")
                    continue
                
                # Get podcast title
                print("\nEnter a title for your podcast (or press Enter for default):")
                title = input("> ").strip()
                
                # Generate podcast
                generator.generate_podcast(audio_path, title)
                
                input("\nPress Enter to continue...")
            
            elif choice == "2":
                # View generated podcasts
                print("\nGenerated Podcasts:")
                podcasts = []
                
                try:
                    for file in os.listdir(generator.output_dir):
                        if file.startswith("podcast_") and file.endswith(".txt"):
                            podcasts.append(file)
                except Exception as e:
                    print(f"Error listing podcasts: {str(e)}")
                
                if not podcasts:
                    print("No podcasts found.")
                else:
                    for i, podcast in enumerate(podcasts):
                        print(f"{i+1}. {podcast}")
                    
                    print("\nEnter the number of the podcast to view (or 0 to return):")
                    podcast_choice = input("> ").strip()
                    
                    try:
                        podcast_index = int(podcast_choice) - 1
                        if 0 <= podcast_index < len(podcasts):
                            podcast_path = os.path.join(generator.output_dir, podcasts[podcast_index])
                            
                            with open(podcast_path, "r") as f:
                                content = f.read()
                            
                            print("\n" + "=" * 60)
                            print(content)
                            print("=" * 60)
                            
                            # Check if there's a corresponding audio file
                            audio_file = podcast_path.replace(".txt", ".mp3")
                            if os.path.exists(audio_file):
                                print(f"\nPodcast audio available at: {audio_file}")
                    except (ValueError, IndexError):
                        if podcast_choice != "0":
                            print("Invalid selection.")
                
                input("\nPress Enter to continue...")
            
            elif choice == "3":
                # Configure settings
                print("\nCurrent Settings:")
                for key, value in generator.settings.items():
                    print(f"{key}: {value}")
                
                print("\nWhich setting would you like to change? (or 'back' to return)")
                setting_key = input("> ").strip()
                
                if setting_key.lower() == 'back':
                    continue
                
                if setting_key in generator.settings:
                    print(f"\nCurrent value for {setting_key}: {generator.settings[setting_key]}")
                    print(f"Enter new value for {setting_key}:")
                    new_value = input("> ").strip()
                    
                    # Convert value to appropriate type
                    if isinstance(generator.settings[setting_key], bool):
                        new_value = new_value.lower() in ('yes', 'true', 'y', '1')
                    elif isinstance(generator.settings[setting_key], int):
                        try:
                            new_value = int(new_value)
                        except ValueError:
                            print("Invalid value. Setting not updated.")
                            continue
                    elif isinstance(generator.settings[setting_key], float):
                        try:
                            new_value = float(new_value)
                        except ValueError:
                            print("Invalid value. Setting not updated.")
                            continue
                    
                    # Update the setting
                    generator.settings[setting_key] = new_value
                    print(f"Setting {setting_key} updated to: {new_value}")
                else:
                    print(f"Setting {setting_key} not found.")
                
                input("\nPress Enter to continue...")
            
            elif choice == "4":
                print("\nThank you for using the AI Podcast Generator!")
                break
            
            else:
                print("\nInvalid choice. Please try again.")
        except EOFError:
            # Handle EOF errors in interactive mode
            print("\nInteractive input not available. Using menu option 4 (Exit).")
            break
        except KeyboardInterrupt:
            print("\n\nProgram terminated by user.")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
    finally:
        print("\nExiting AI Podcast Generator...")
