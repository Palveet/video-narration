# Video Narration Service

A Python service that automatically generates narrative audio for videos in a storytelling manner. The service analyzes video content, generates a compelling narrative, and creates synchronized audio narration.

## Features

- Automatic scene detection and analysis
- AI-powered narrative generation
- High-quality text-to-speech conversion
- Multiple output formats (JSON, SRT, VTT)
- REST API support
- Command-line interface

## Prerequisites

- Python 3.8 or higher (I have used Python 3.12)
- FFmpeg (automatically downloaded if not present)
- OpenAI API key
- ElevenLabs API key

## Installation

1. Clone the repository:
```bash
git clone git@github.com:Palveet/video-narration.git
cd video-narration
```

2. Create and activate a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:

Option 1 - Using .env file (Recommended):
```bash
# Copy the example env file
cp env.example .env

# Edit .env file and add your API keys
OPENAI_API_KEY=your_openai_key_here
ELEVEN_API_KEY=your_eleven_labs_key_here
```

Option 2 - Setting environment variables directly:
```bash
# Windows
set OPENAI_API_KEY=your_openai_key_here
set ELEVEN_API_KEY=your_eleven_labs_key_here

# Linux/Mac
export OPENAI_API_KEY=your_openai_key_here
export ELEVEN_API_KEY=your_eleven_labs_key_here
```

Note: The .env file method is recommended as it's more secure and easier to manage. The file is automatically loaded by python-dotenv when the application starts.

## Usage

### Command Line Interface

Process a video file:
```bash
python src/main.py path/to/video.mp4 --output-dir output --format json
```

Options:
- `--output-dir`: Directory to save outputs (default: "output")
- `--format`: Output format (json, srt, vtt) (default: "json")

### REST API

Start the API server:
```bash
uvicorn src.main:app --reload
```

API Endpoint:
- POST `/narrate`
  - Parameters:
    - `video`: Video file (multipart/form-data)
    - `video_url`: URL of the video (string)
    - `output_format`: Output format (json, srt, vtt)

## Output Structure

The service generates:
1. Narration script (JSON/SRT/VTT)
2. Audio narration (WAV)

Output files are saved in a timestamped directory:
```
output/
  video_name_YYYYMMDD_HHMMSS/
    narration_script.json
    narration.wav
```

## Testing

Run the test suite:
```bash
# Install package in development mode
pip install -e .

# Run tests
pytest tests/
```

Test requirements:
- OpenAI API key
- ElevenLabs API key
- Sample video file at `sample_data/sample_video.mp4`

## Project Structure

```
video-narration/
├── src/
│   ├── main.py              # Main application and API
│   ├── scene_analyzer.py    # Video scene detection
│   ├── narrative_generator.py # AI narrative generation
│   ├── audio_generator.py   # Text-to-speech conversion
│   ├── output_renderer.py   # Output format handling
│   └── video_handler.py     # Video metadata handling
├── tests/
│   ├── test_alignment.py    # Scene-narrative alignment tests
│   └── test_pipeline.py     # Full pipeline tests
├── sample_data/             # Sample videos for testing
├── output/                  # Generated outputs
├── tools/                   # FFmpeg and other tools
├── requirements.txt         # Python dependencies
├── env.example             # Example environment variables file
└── README.md               # This file
```

## Dependencies

- scenedetect[opencv]: Scene detection
- opencv-python: Video processing
- openai: GPT-4 for narrative generation
- elevenlabs: Text-to-speech conversion
- fastapi: REST API
- pydub: Audio processing
- pytest: Testing framework
- python-dotenv: Environment variable management

## Acknowledgments

- OpenAI for GPT-4
- ElevenLabs for text-to-speech
- FFmpeg for video/audio processing