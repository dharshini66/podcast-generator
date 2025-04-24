import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MinimalPodcastGenerator:
    def __init__(self):
        self.assembly_api_key = os.getenv("ASSEMBLY_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
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
            # Set API key using the correct method for the installed version
            elevenlabs.api_key = self.elevenlabs_api_key
            self.voice_available = True
            print("[SUCCESS] ElevenLabs voice service initialized")
        except (ImportError, Exception) as e:
            print(f"[FAILED] ElevenLabs initialization failed: {str(e)}")
            print("  Using placeholder voice generation instead")
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio file using AssemblyAI or placeholder"""
        print(f"\nTranscribing audio: {os.path.basename(audio_path)}")
        
        if not os.path.exists(audio_path):
            print(f"Error: Audio file not found at {audio_path}")
            return None
        
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
        
        # Placeholder transcription
        print("Using placeholder transcription")
        return "This is a placeholder transcription. The actual transcription would appear here if AssemblyAI was properly configured."
    
    def generate_voice(self, text, output_path=None):
        """Generate voice using ElevenLabs or placeholder"""
        if not output_path:
            timestamp = int(time.time())
            output_path = os.path.join(self.temp_dir, f"narration_{timestamp}.mp3")
        
        print(f"\nGenerating voice narration for: {text[:50]}...")
        
        if self.voice_available:
            try:
                import elevenlabs
                audio = elevenlabs.generate(
                    text=text,
                    voice="Bella",
                    model="eleven_monolingual_v1"
                )
                
                # Save the audio to file
                with open(output_path, "wb") as f:
                    f.write(audio)
                
                print(f"Voice narration saved to: {output_path}")
                return output_path
            except Exception as e:
                print(f"Voice generation error: {str(e)}")
                print("Using placeholder voice instead")
        
        # Create a placeholder audio file
        print("Using placeholder voice file")
        placeholder_path = os.path.join(self.temp_dir, "placeholder_voice.txt")
        with open(placeholder_path, "w") as f:
            f.write(f"PLACEHOLDER VOICE FILE\nText: {text}\n")
        
        return placeholder_path
    
    def extract_key_points(self, transcript):
        """Extract key points from transcript"""
        print("\nExtracting key points from transcript...")
        
        if not transcript:
            return []
        
        # Simple extraction - in a real implementation, this would use NLP
        sentences = transcript.split(". ")
        key_points = []
        
        # Take every third sentence as a key point (simplified approach)
        for i, sentence in enumerate(sentences):
            if i % 3 == 0 and len(sentence) > 20:  # Only longer sentences
                key_points.append(sentence)
        
        # Limit to 5 key points
        key_points = key_points[:5]
        
        print(f"Extracted {len(key_points)} key points")
        return key_points
    
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
        for i, point in enumerate(key_points):
            segment_title = f"Key Point {i+1}"
            narration_text = f"Key point {i+1}: {point}"
            narration_audio = self.generate_voice(narration_text)
            
            podcast_segments.append({
                "title": segment_title,
                "text": point,
                "narration": narration_audio
            })
        
        # Step 5: Save podcast information
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
        
        print("\n" + "=" * 60)
        print(f"Podcast generation complete!")
        print(f"Podcast information saved to: {podcast_info_path}")
        print("=" * 60)
        
        return podcast_info_path

def print_menu():
    """Print the main menu"""
    print("\n" + "=" * 60)
    print("AI Podcast Generator".center(60))
    print("=" * 60)
    print("1. Generate Podcast from Audio File")
    print("2. View Generated Podcasts")
    print("3. Exit")
    choice = input("\nSelect an option (1-3): ")
    return choice

def main():
    # Initialize the podcast generator
    generator = MinimalPodcastGenerator()
    
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
                    except (ValueError, IndexError):
                        if podcast_choice != "0":
                            print("Invalid selection.")
                
                input("\nPress Enter to continue...")
            
            elif choice == "3":
                print("\nThank you for using the AI Podcast Generator!")
                break
            
            else:
                print("\nInvalid choice. Please try again.")
        except EOFError:
            # Handle EOF errors in interactive mode
            print("\nInteractive input not available. Using menu option 3 (Exit).")
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
