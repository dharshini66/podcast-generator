import os
import time
import json

def create_text_audio_simulation():
    """Create a simulated audio file (text-based) for testing the podcast generator"""
    # Create temp directory if it doesn't exist
    temp_dir = os.path.join(os.getcwd(), "temp_audio")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create a simulated audio file (JSON format with transcript)
    timestamp = int(time.time())
    output_file = os.path.join(temp_dir, f"simulated_meeting_{timestamp}.json")
    
    meeting_transcript = {
        "title": "Quarterly Team Meeting",
        "duration": "00:15:30",
        "date": time.ctime(),
        "transcript": """
Welcome to our quarterly team meeting. Today we'll be discussing our Q1 results and plans for Q2.

First, let's talk about our sales performance. We've seen a 15% increase in sales compared to the same quarter last year. This is primarily due to the new product line we launched in February.

The marketing team has prepared a new campaign that will launch next month. Initial focus groups have shown very positive responses to the concept.

We also need to discuss the upcoming product release. The development team has been working hard to include all the requested features. We're on track for a June release.

The mobile app development is progressing well. We've completed about 75% of the planned features and are now focusing on UI improvements based on user feedback.

Speaking of feedback, customer satisfaction ratings have improved by 8 points since our last update. The changes to our support system seem to be working well.

One area we need to focus on is improving our response time to support tickets. Currently, our average response time is 6 hours, and we'd like to get that down to 4 hours by the end of Q2.

The HR department has announced new training programs that will be available to all employees starting next month. These include technical skills workshops and leadership development courses.

Finally, let's discuss the budget for the next quarter. We've allocated additional resources to the R&D department to accelerate our innovation pipeline.

Thank you all for attending. Please send any follow-up questions to your department heads.
        """
    }
    
    # Write the simulated audio data to a JSON file
    with open(output_file, 'w') as f:
        json.dump(meeting_transcript, f, indent=2)
    
    print(f"\nSimulated audio file created at: {output_file}")
    return output_file

if __name__ == "__main__":
    print("Creating simulated audio file for testing...")
    simulated_file = create_text_audio_simulation()
    
    print("\nSimulated audio file created successfully!")
    print(f"File path: {simulated_file}")
    print("\nYou can now use this file to test the AI Podcast Generator.")
    print("Run run_podcast_generator.bat and when prompted for the audio file path, enter:")
    print(f"> {simulated_file}")
    print("\nNote: Since this is a simulated audio file, the podcast generator will use")
    print("the transcript directly instead of performing transcription.")
    
    try:
        input("\nPress Enter to exit...")
    except EOFError:
        pass
