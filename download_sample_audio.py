import os
import requests
import time

def download_sample_audio():
    """Download a sample audio file for testing the podcast generator"""
    # Create temp directory if it doesn't exist
    temp_dir = os.path.join(os.getcwd(), "temp_audio")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Sample audio URL (this is a public domain audio file)
    audio_url = "https://www2.cs.uic.edu/~i101/SoundFiles/StarWars3.wav"
    
    # Generate output file path
    timestamp = int(time.time())
    output_file = os.path.join(temp_dir, f"sample_meeting_{timestamp}.wav")
    
    try:
        print(f"Downloading sample audio from: {audio_url}")
        response = requests.get(audio_url, stream=True)
        response.raise_for_status()
        
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"\nSample audio file downloaded to: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error downloading sample audio: {str(e)}")
        
        # If download fails, create a text file as a placeholder
        placeholder_file = os.path.join(temp_dir, f"sample_meeting_{timestamp}.txt")
        with open(placeholder_file, "w") as f:
            f.write("This is a placeholder for a sample meeting recording.\n")
            f.write("The actual audio file could not be downloaded.\n")
            f.write("You can still test the podcast generator with your own audio file.")
        
        print(f"\nPlaceholder file created at: {placeholder_file}")
        return placeholder_file

if __name__ == "__main__":
    print("Downloading sample audio file for testing...")
    sample_file = download_sample_audio()
    
    if sample_file and sample_file.endswith(('.mp3', '.wav')):
        print("\nSample audio file downloaded successfully!")
        print(f"File path: {sample_file}")
        print("\nYou can now use this file to test the AI Podcast Generator.")
        print("Run run_podcast_generator.bat and select option 1 to generate a podcast.")
        print("When prompted for the audio file path, enter:")
        print(f"> {sample_file}")
    else:
        print("\nFailed to download sample audio file.")
        print("Please use your own audio file for testing.")
    
    print("\nPress Enter to exit...")
    try:
        input()
    except EOFError:
        pass
