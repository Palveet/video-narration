#!/usr/bin/env python3
import os
import argparse
import json
import tempfile
import time
import shutil
from pathlib import Path
from typing import Dict, Optional, Union, List
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import requests

from video_handler import VideoInputHandler
from scene_analyzer import SceneAnalyzer
from narrative_generator import VisualNarrativeGenerator
from audio_generator import AudioGenerator
from output_renderer import OutputRenderer, OutputFormat

load_dotenv()

app = FastAPI(
    title="Video Narration Service",
    description="Generates narrative audio for videos",
    version="1.0.0"
)

input_handler = VideoInputHandler()
scene_analyzer = SceneAnalyzer()
narrative_generator = VisualNarrativeGenerator()
audio_generator = AudioGenerator()
output_renderer = OutputRenderer()

def process_video(
    video_path: str,
    output_dir: str = "output",
    output_format: OutputFormat = OutputFormat.JSON,
    mux_video: bool = False
) -> Dict:
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    unique_output_dir = os.path.join(output_dir, f"{video_name}_{timestamp}")
    Path(unique_output_dir).mkdir(exist_ok=True, parents=True)
    
    temp_dir = os.path.join("temp_audio", f"{video_name}_{timestamp}")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        print(f"Processing video: {video_path}")
        print(f"Output directory: {unique_output_dir}")
        print(f"Temp directory: {temp_dir}")
        
        video_metadata = input_handler.handle_input(video_path)
        
        print("Detecting scenes...")
        scenes = scene_analyzer.detect_scenes(video_path)
        
        print("Generating narrative...")
        narrative = narrative_generator.generate_narrative(scenes, video_metadata)
        
        print("Generating audio...")
        audio_path = audio_generator.generate_audio(narrative, temp_dir)
        
        print("Rendering outputs...")
        output_paths = output_renderer.generate_outputs(
            narrative, 
            audio_path, 
            video_path if mux_video else None,
            unique_output_dir,
            output_format
        )
        
        result = {
            "metadata": video_metadata.model_dump(),
            "scenes": len(scenes),
            "narrative_segments": len(narrative),
            "outputs": output_paths,
            "output_dir": unique_output_dir
        }
        
        return result
        
    finally:
        try:
            if os.path.exists("temp_audio"):
                shutil.rmtree("temp_audio")
                print("Cleaned up temp_audio directory")
        except Exception as e:
            print(f"Warning: Failed to clean up temp_audio directory: {e}")

def cli_main():
    parser = argparse.ArgumentParser(description="Video Narration Service")
    parser.add_argument(
        "video_path", 
        help="Path to video file or URL"
    )
    parser.add_argument(
        "--output-dir", 
        default="output", 
        help="Directory to save outputs"
    )
    parser.add_argument(
        "--format", 
        choices=["json", "srt", "vtt"], 
        default="json",
        help="Format for narration script"
    )
    parser.add_argument(
        "--mux", 
        action="store_true", 
        help="Mux narration with original video"
    )
    
    args = parser.parse_args()
    
    output_format = {
        "json": OutputFormat.JSON,
        "srt": OutputFormat.SRT,
        "vtt": OutputFormat.VTT
    }[args.format]
    
    result = process_video(
        args.video_path,
        args.output_dir,
        output_format,
        args.mux
    )
    
    print(json.dumps(result, indent=2))

@app.post("/narrate")
async def narrate_video(
    video: Optional[UploadFile] = File(None),
    video_url: str = Form(None),
    output_format: str = Form("json"),
    mux_video: bool = Form(False)
):
    if not video and not video_url:
        return {"error": "Either video file or video URL must be provided"}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        if video:
            temp_video_path = Path(temp_dir) / "input_video.mp4"
            with open(temp_video_path, "wb") as f:
                f.write(await video.read())
            video_path = str(temp_video_path)
        else:
            video_path = video_url
            
        format_map = {
            "json": OutputFormat.JSON,
            "srt": OutputFormat.SRT,
            "vtt": OutputFormat.VTT
        }
        output_format_enum = format_map.get(output_format.lower(), OutputFormat.JSON)
        
        result = process_video(
            video_path,
            temp_dir,
            output_format_enum,
            mux_video
        )
        
        return result

if __name__ == "__main__":
    cli_main()