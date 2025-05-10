
import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
import tempfile
from pydantic import BaseModel
from scenedetect import detect, ContentDetector
from scenedetect.scene_manager import save_images

class VideoScene(BaseModel):
    start_time: float  # in seconds
    end_time: float  # in seconds
    duration: float  # in seconds
    keyframe_path: str  # path to keyframe image
    scene_type: str  # e.g., "wide-shot", "close-up", etc.

class SceneAnalyzer:

    def __init__(self, threshold: float = 27.0, min_scene_len: int = 15):
       
        self.threshold = threshold
        self.min_scene_len = min_scene_len
    
    def detect_scenes(self, video_path: str) -> List[VideoScene]:
       
        temp_dir = tempfile.mkdtemp()
        
        scene_list = detect(video_path, ContentDetector(
            threshold=self.threshold,
            min_scene_len=self.min_scene_len
        ))
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        scenes = []
        for i, scene in enumerate(scene_list):
            start_frame = scene[0].get_frames()
            end_frame = scene[1].get_frames() - 1
            
            start_time = start_frame / fps
            end_time = end_frame / fps
            duration = end_time - start_time
            
            mid_frame = start_frame + ((end_frame - start_frame) // 2)
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            ret, frame = cap.read()
            
            keyframe_path = os.path.join(temp_dir, f"scene_{i}_frame_{mid_frame}.jpg")
            if ret:
                cv2.imwrite(keyframe_path, frame)
            else:
                keyframe_path = ""
            
            scene_type = self._detect_scene_type(frame) if ret else "unknown"
            
            scenes.append(VideoScene(
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                keyframe_path=keyframe_path,
                scene_type=scene_type
            ))
        
        cap.release()
        
        if not scenes:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps
            
            mid_frame = total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            ret, frame = cap.read()
            
            keyframe_path = os.path.join(temp_dir, f"scene_0_frame_{mid_frame}.jpg")
            if ret:
                cv2.imwrite(keyframe_path, frame)
                scene_type = self._detect_scene_type(frame)
            else:
                keyframe_path = ""
                scene_type = "unknown"
            
            scenes.append(VideoScene(
                start_time=0.0,
                end_time=duration,
                duration=duration,
                keyframe_path=keyframe_path,
                scene_type=scene_type
            ))
            
            cap.release()
        
        return scenes
    
    def _detect_scene_type(self, frame: np.ndarray) -> str:
        
        if frame is None:
            return "unknown"
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.count_nonzero(edges) / edges.size
        
        if edge_density > 0.1:
            return "close-up"
        elif edge_density > 0.05:
            return "medium-shot"
        else:
            return "wide-shot"