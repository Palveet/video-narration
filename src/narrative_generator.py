import os
import base64
from typing import List, Dict, Any, Optional
import time
from pydantic import BaseModel
import json
import cv2
import numpy as np
from openai import OpenAI

from scene_analyzer import VideoScene
from video_handler import VideoMetadata

class NarrativeSegment(BaseModel):
    start_time: float
    end_time: float
    duration: float
    text: str
    scene_idx: int

class VisualNarrativeGenerator:
   
    def __init__(self):

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"  
    
    def generate_narrative(self, scenes: List[VideoScene], video_metadata: VideoMetadata) -> List[NarrativeSegment]:
        
        scene_descriptions = []
        for i, scene in enumerate(scenes):
            if not os.path.exists(scene.keyframe_path):
                description = f"Scene {i+1} (unknown content)"
            else:
                description = self._analyze_frame(scene.keyframe_path, i)
            
            scene_descriptions.append({
                "scene_idx": i,
                "start_time": scene.start_time,
                "end_time": scene.end_time,
                "duration": scene.duration,
                "description": description,
                "scene_type": scene.scene_type,
            })
        
        return self._generate_storytelling_narrative(scene_descriptions, video_metadata)
    
    def _analyze_frame(self, image_path: str, scene_idx: int) -> str:
       
        try:

            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a highly skilled filmmaker and storyteller. Describe what's happening in this image in detail, focusing on elements that would be important for creating a compelling narrative. Consider characters, actions, emotions, setting, and mood."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"This is a key frame from scene {scene_idx+1} of a video. Describe what you see in rich, descriptive detail."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                        ]
                    }
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error analyzing frame: {str(e)}")
            return f"Scene {scene_idx+1} (analysis failed)"
    
    def _generate_storytelling_narrative(
        self, 
        scene_descriptions: List[Dict[str, Any]],
        video_metadata: VideoMetadata
    ) -> List[NarrativeSegment]:
       
        try:

            scenes_json = json.dumps(scene_descriptions, indent=2)
            
            prompt = f"""
            You are a master storyteller creating a compelling narrative for a {video_metadata.duration:.1f} second video.
            
            Here are the scenes in the video with their descriptions:
            {scenes_json}
            
            Create a cohesive, engaging narration script that tells a story based on these scenes. 
            The narration should:
            1. Flow like an audiobook or documentary, not just describe what's on screen
            2. Have a beginning, middle, and end structure
            3. Use vivid language and appropriate pacing
            4. Fit within the time constraints of each scene
            
            Format your response as a JSON array of segments, each with:
            - scene_idx: the scene index
            - start_time: time in seconds when narration starts
            - end_time: time in seconds when narration ends
            - text: the narration text (aim for ~130-150 words per minute)
            
            Make sure narration covers the entire video duration with no large gaps.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a master storyteller and filmmaker creating narration for videos."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            segments = []
            for segment in result.get("segments", []):
                segments.append(NarrativeSegment(
                    start_time=segment["start_time"],
                    end_time=segment["end_time"],
                    duration=segment["end_time"] - segment["start_time"],
                    text=segment["text"],
                    scene_idx=segment["scene_idx"]
                ))
            
            if not segments and scene_descriptions:
                segments.append(NarrativeSegment(
                    start_time=0.0,
                    end_time=video_metadata.duration,
                    duration=video_metadata.duration,
                    text="The video shows a sequence of scenes that tell a story.",
                    scene_idx=0
                ))
            
            return segments
            
        except Exception as e:
            print(f"Error generating narrative: {str(e)}")
            
            segments = []
            for scene in scene_descriptions:
                segments.append(NarrativeSegment(
                    start_time=scene["start_time"],
                    end_time=scene["end_time"],
                    duration=scene["duration"],
                    text=f"In this scene, {scene['description']}",
                    scene_idx=scene["scene_idx"]
                ))
            
            return segments