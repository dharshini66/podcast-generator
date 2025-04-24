import os
import time
import subprocess
from pathlib import Path

def create_sample_audio():
    """Create a sample audio file using FFmpeg for testing the podcast generator"""
    # Get FFmpeg path from .env file
    ffmpeg_path = None
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('FFMPEG_PATH='):
                    ffmpeg_path = line.strip().split('=', 1)[1].strip()
                    break
    
    if not ffmpeg_path or not os.path.exists(ffmpeg_path):
        print("FFmpeg not found. Cannot create sample audio.")
        return None
    
    # Create temp directory if it doesn't exist
    temp_dir = os.path.join(os.getcwd(), "temp_audio")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create a text file with sample content
    sample_text = """
    Welcome to this sample meeting recording.
    
    In today's meeting, we discussed the quarterly results and found that sales have increased by 15%.
    
    The marketing team presented their new campaign which will launch next month.
    
    We also talked about the upcoming product release and the features that will be included.
    
    The development team reported good progress on the mobile app.
    
    Customer feedback has been positive regarding the latest updates.
    
    We need to focus on improving our response time to support tickets.
    
    The HR department announced new training programs for all employees.
    
    Finally, we discussed the budget for the next quarter and agreed on the priorities.
    
    Thank you all for attending the meeting.
    """
    
    text_file = os.path.join(temp_dir, "sample_text.txt")
    with open(text_file, "w") as f:
        f.write(sample_text)
    
    # Generate sample audio using FFmpeg
    timestamp = int(time.time())
    output_file = os.path.join(temp_dir, f"sample_meeting_{timestamp}.mp3")
    
    try:
        # Use FFmpeg to generate audio from text
        cmd = [
            ffmpeg_path,
            "-f", "lavfi",
            "-i", "sine=frequency=1000:duration=10",
            "-af", "aevalsrc=0:duration=10",
            output_file
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"\nSample audio file created at: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error creating sample audio: {str(e)}")
        return None

if __name__ == "__main__":
    print("Creating sample audio file for testing...")
    sample_file = create_sample_audio()
    
    if sample_file:
        print("\nSample audio file created successfully!")
        print(f"File path: {sample_file}")
        print("\nYou can now use this file to test the AI Podcast Generator.")
        print("Run run_podcast_generator.bat and select option 1 to generate a podcast.")
        print("When prompted for the audio file path, enter:")
        print(f"> {sample_file}")
    else:
        print("\nFailed to create sample audio file.")
    
    input("\nPress Enter to exit...")
