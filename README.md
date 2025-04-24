# Meeting to Podcast AI Agent

An AI agent that automatically creates micro podcasts from meeting recordings. The agent can join Zoom meetings, record audio, and intelligently segment the content into podcast snippets.

## Features

- Zoom meeting integration for automatic recording
- Audio processing and segmentation
- Intelligent content extraction using Google Gemini API
- Podcast generation with MeetStream.ai API integration
- Easy-to-use interface for managing recordings and podcasts

## Requirements

- Python 3.8+
- Google Gemini API key
- MeetStream.ai API key
- Zoom API credentials

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file with your API keys and credentials

## Usage

1. Start the agent:
   ```
   python main.py
   ```
2. Configure Zoom meeting details
3. Let the agent join the meeting and record
4. After the meeting, the agent will process the audio and generate podcast snippets

## Project Structure

- `src/api/` - API integrations (Google Gemini, MeetStream.ai)
- `src/audio/` - Audio processing utilities
- `src/zoom/` - Zoom meeting integration
- `src/podcast/` - Podcast generation logic
