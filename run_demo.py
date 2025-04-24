import os
import sys
import time
from ai_podcast_generator import AIPodcastGenerator

def run_demo():
    """Run a demonstration of the AI Podcast Generator with the simulated audio file"""
    print("\n" + "=" * 60)
    print("AI Podcast Generator - Automated Demo".center(60))
    print("=" * 60)
    
    # Find the most recent simulated audio file
    temp_dir = os.path.join(os.getcwd(), "temp_audio")
    simulated_file = None
    
    if os.path.exists(temp_dir):
        json_files = [f for f in os.listdir(temp_dir) if f.startswith("simulated_meeting_") and f.endswith(".json")]
        if json_files:
            # Sort by name (which includes timestamp)
            json_files.sort(reverse=True)
            simulated_file = os.path.join(temp_dir, json_files[0])
    
    if not simulated_file:
        print("No simulated audio file found. Creating one...")
        # Create a simulated audio file
        from create_text_audio import create_text_audio_simulation
        simulated_file = create_text_audio_simulation()
    
    print(f"\nUsing simulated audio file: {simulated_file}")
    
    # Initialize the podcast generator
    generator = AIPodcastGenerator()
    
    # Generate a podcast from the simulated audio
    print("\nGenerating podcast from simulated audio...")
    result = generator.generate_podcast(simulated_file, "Quarterly Team Meeting Demo")
    
    if result:
        print("\nPodcast generation successful!")
        print(f"Podcast information: {result['info']}")
        if result.get('audio'):
            print(f"Podcast audio: {result['audio']}")
        
        # Display the podcast content
        if os.path.exists(result['info']):
            print("\n" + "=" * 60)
            print("PODCAST CONTENT".center(60))
            print("=" * 60)
            
            with open(result['info'], 'r') as f:
                content = f.read()
            
            print(content)
            print("=" * 60)
    else:
        print("\nPodcast generation failed.")
    
    print("\nDemo complete!")

if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        print(f"\nAn error occurred during the demo: {str(e)}")
    
    print("\nPress Enter to exit...")
    try:
        input()
    except EOFError:
        pass
