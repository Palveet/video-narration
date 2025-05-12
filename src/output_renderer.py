import os
import json
import enum
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
import shutil
from pydub import AudioSegment

from narrative_generator import NarrativeSegment

class OutputFormat(enum.Enum):
    JSON = "json"
    SRT = "srt"
    VTT = "vtt"

class OutputRenderer:
    
    def generate_outputs(
        self,
        narrative: List[NarrativeSegment],
        audio_path: str,
        video_path: Optional[str] = None,
        output_dir: str = "output",
        output_format: OutputFormat = OutputFormat.JSON
    ) -> Dict[str, str]:

        Path(output_dir).mkdir(exist_ok=True, parents=True)
        
        if output_format == OutputFormat.JSON:
            script_path = self._generate_json_script(narrative, output_dir)
        elif output_format == OutputFormat.SRT:
            script_path = self._generate_srt_script(narrative, output_dir)
        elif output_format == OutputFormat.VTT:
            script_path = self._generate_vtt_script(narrative, output_dir)
        else:
            script_path = self._generate_json_script(narrative, output_dir)
        
        audio_output_path = os.path.join(output_dir, "narration.wav")
        shutil.copy(audio_path, audio_output_path)
        
        muxed_video_path = None
        if video_path:
            muxed_video_path = self._mux_audio_with_video(video_path, audio_output_path, output_dir)
        
        result = {
            "script": script_path,
            "audio": audio_output_path
        }
        
        if muxed_video_path:
            result["muxed_video"] = muxed_video_path
        
        return result
    
    def _generate_json_script(self, narrative: List[NarrativeSegment], output_dir: str) -> str:
       
        script_path = os.path.join(output_dir, "narration_script.json")
        
        segments = [segment.dict() for segment in narrative]
        
        with open(script_path, "w") as f:
            json.dump({"segments": segments}, f, indent=2)
        
        return script_path
    
    def _generate_srt_script(self, narrative: List[NarrativeSegment], output_dir: str) -> str:
      
        script_path = os.path.join(output_dir, "narration_script.srt")
        
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace(".", ",")
        
        with open(script_path, "w") as f:
            for i, segment in enumerate(narrative):
                f.write(f"{i+1}\n")
                f.write(f"{format_time(segment.start_time)} --> {format_time(segment.end_time)}\n")
                f.write(f"{segment.text}\n\n")
        
        return script_path
    
    def _generate_vtt_script(self, narrative: List[NarrativeSegment], output_dir: str) -> str:
      
        script_path = os.path.join(output_dir, "narration_script.vtt")
        
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        
        with open(script_path, "w") as f:
            f.write("WEBVTT\n\n")
            
            for i, segment in enumerate(narrative):
                f.write(f"{i+1}\n")
                f.write(f"{format_time(segment.start_time)} --> {format_time(segment.end_time)}\n")
                f.write(f"{segment.text}\n\n")
        
        return script_path
    
    def _mux_audio_with_video(self, video_path: str, audio_path: str, output_dir: str) -> str:
        print(video_path)
        print(audio_path)
        try:
            output_path = os.path.join(output_dir, "narrated_video.mp4")
            ffmpeg_path = AudioSegment.converter
            ffmpeg_cmd = [
                ffmpeg_path, "-y",
                "-i", video_path,
                "-i", audio_path,
                "-map", "0:v:0",  
                "-map", "1:a:0",  
                "-c:v", "copy",  
                "-shortest",
                output_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True)
            
            return output_path
        
        except Exception as e:
            print(f"Error muxing audio with video: {str(e)}")
            return None