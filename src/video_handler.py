
import os
import tempfile
from pathlib import Path
from typing import Union, Dict, Any
import cv2
import requests
from pydantic import BaseModel

class VideoMetadata(BaseModel):
    path: str
    duration: float  # in seconds
    fps: float
    frame_count: int
    width: int
    height: int
    has_audio: bool

class VideoInputHandler:

    def handle_input(self, source: Union[str, Path]) -> VideoMetadata:
        
        source = str(source)
        
        if source.startswith(('http://', 'https://')):
 
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            try:
                response = requests.get(source, stream=True)
                response.raise_for_status()
                
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                
                temp_file.close()
                video_path = temp_file.name
            except Exception as e:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                raise ValueError(f"Failed to download video from URL: {str(e)}")
        else:
            if not os.path.exists(source):
                raise ValueError(f"Video file not found: {source}")
            video_path = source
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Failed to open video: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            duration = frame_count / fps if fps > 0 else 0
            
            has_audio = True  
            
            cap.release()
            
            return VideoMetadata(
                path=video_path,
                duration=duration,
                fps=fps,
                frame_count=frame_count,
                width=width,
                height=height,
                has_audio=has_audio
            )
        except Exception as e:
            raise ValueError(f"Failed to extract video metadata: {str(e)}")