import os
import warnings
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg or avconv*", category=RuntimeWarning)
from typing import List, Dict, Any
import subprocess
from elevenlabs import ElevenLabs, VoiceSettings
import shutil
from pydub import AudioSegment
import requests
import zipfile

def ensure_ffmpeg():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    tools_dir = os.path.join(project_root, "tools")
    os.makedirs(tools_dir, exist_ok=True)
    ffmpeg_path = os.path.join(tools_dir, "ffmpeg.exe")
    ffprobe_path = os.path.join(tools_dir, "ffprobe.exe")
    if not (os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path)):
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = os.path.join(tools_dir, "ffmpeg.zip")
        try:
            response = requests.get(ffmpeg_url, stream=True)
            response.raise_for_status()
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tools_dir)
            extracted_dir = os.path.join(tools_dir, "ffmpeg-master-latest-win64-gpl", "bin")
            shutil.move(os.path.join(extracted_dir, "ffmpeg.exe"), ffmpeg_path)
            shutil.move(os.path.join(extracted_dir, "ffprobe.exe"), ffprobe_path)
            shutil.rmtree(os.path.join(tools_dir, "ffmpeg-master-latest-win64-gpl"))
            os.remove(zip_path)
        except Exception as e:
            print(f"Error downloading ffmpeg: {e}")
            raise
    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError(f"ffmpeg.exe not found at {ffmpeg_path}")
    if not os.path.exists(ffprobe_path):
        raise FileNotFoundError(f"ffprobe.exe not found at {ffprobe_path}")
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffprobe = ffprobe_path

ensure_ffmpeg()

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
    def generate_audio(self, narrative_segments: List[NarrativeSegment], temp_dir: str = None) -> str:
        if not narrative_segments:
            raise ValueError("No narrative segments provided")
        if temp_dir is None:
            temp_dir = os.path.abspath("temp_audio")
        os.makedirs(temp_dir, exist_ok=True)
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
                    data = b"".join(chunk for chunk in audio)
                    f.write(data)
                segment_files.append({
                    "path": segment_path,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
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
            if not segment_files:
                raise ValueError("No audio segments to combine")
            for segment in segment_files:
                if not os.path.exists(segment['path']):
                    raise FileNotFoundError(f"Segment file not found: {segment['path']}")
            temp_dir = os.path.dirname(output_path)
            file_list_path = os.path.join(temp_dir, "file_list.txt")
            with open(file_list_path, "w") as f:
                for segment in segment_files:
                    abs_path = os.path.abspath(segment['path'])
                    f.write(f"file '{abs_path}'\n")
            with open(file_list_path, 'r') as f:
                print("File list contents:")
                print(f.read())
            ffmpeg_path = AudioSegment.converter
            if not os.path.exists(ffmpeg_path):
                raise FileNotFoundError(f"ffmpeg not found at {ffmpeg_path}")
            ffmpeg_cmd = [
                ffmpeg_path, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", file_list_path,
                "-c", "copy",
                output_path
            ]
            result = subprocess.run(
                ffmpeg_cmd,
                check=True,
                capture_output=True,
                text=True
            )
            os.remove(file_list_path)
        except subprocess.CalledProcessError as e:
            if segment_files:
                shutil.copy(segment_files[0]["path"], output_path)
                print(f"Used fallback: copied first segment to {output_path}")
        except Exception as e:
            print(f"Error combining audio segments: {e}")
            if segment_files:
                shutil.copy(segment_files[0]["path"], output_path)
                print(f"Used fallback: copied first segment to {output_path}")
