import os
from typing import List, Dict, Any, Optional
import tempfile
import time
from pathlib import Path
import subprocess
from pydantic import BaseModel
from elevenlabs import ElevenLabs, VoiceSettings
from pydub import AudioSegment

from narrative_generator import NarrativeSegment

class AudioGenerator:
   
    def __init__(self):


        api_key = os.environ.get("ELEVEN_API_KEY")
        if not api_key:
            raise ValueError("ELEVEN_API_KEY environment variable not set")
        
        self.client = ElevenLabs(api_key=api_key)
        
        self.voice_id = os.environ.get("ELEVEN_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  
        
        self.stability = float(os.environ.get("ELEVEN_STABILITY", "0.5"))
        self.similarity_boost = float(os.environ.get("ELEVEN_SIMILARITY_BOOST", "0.75"))
        
    def generate_audio(self, narrative_segments: List[NarrativeSegment]) -> str:
        
        if not narrative_segments:
            raise ValueError("No narrative segments provided")
        
        temp_dir = tempfile.mkdtemp()
        segment_files = []
        
        for i, segment in enumerate(narrative_segments):
            try:
                audio = self.client.text_to_speech.convert(
                            voice_id=self.voice_id,
                            model_id="eleven_monolingual_v1",
                            text=segment.text,
                            voice_settings=VoiceSettings(
                                stability=self.stability,
                                similarity_boost=self.similarity_boost
                            )
                        )
                segment_path = os.path.join(temp_dir, f"segment_{i}.wav")
                with open(segment_path, "wb") as f:
                    for chunk in audio:
                        f.write(chunk)

            
                segment_files.append({
                    "path": segment_path,
                    "start_time": segment.start_time,
                    "duration": segment.duration
                })
                
                print(f"Generated audio for segment {i+1}/{len(narrative_segments)}")
                
            except Exception as e:
                print(f"Error generating audio for segment {i}: {str(e)}")
        
        output_path = os.path.join(temp_dir, "narration.wav")
        self._combine_audio_segments(segment_files, output_path)
        
        return output_path
    
    def _combine_audio_segments(self, segment_files: List[Dict[str, Any]], output_path: str) -> None:
           
            try:
                segment_files.sort(key=lambda x: x["start_time"])
                combined = AudioSegment.empty()

                for segment in segment_files:
                    audio = AudioSegment.from_wav(segment["path"])
                    combined += audio

                combined.export(output_path, format="wav")
                print(f"Combined audio saved to: {output_path}")

            except Exception as e:
                print(f"Error combining audio segments: {str(e)}")
                if segment_files:
                    import shutil
                    shutil.copy(segment_files[0]["path"], output_path)
                    print(f"Used fallback: copied first segment to {output_path}")
