import os
import sys
import unittest
from pathlib import Path
import tempfile
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from main import process_video
from output_renderer import OutputFormat

class TestPipeline(unittest.TestCase):

    
    @classmethod
    def setUpClass(cls):

        if not os.environ.get("OPENAI_API_KEY"):
            raise unittest.SkipTest("OPENAI_API_KEY environment variable not set")
        if not os.environ.get("ELEVEN_API_KEY"):
            raise unittest.SkipTest("ELEVEN_API_KEY environment variable not set")
        
        cls.sample_video_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "sample_data", 
            "video1.mp4"
        )
        
        if not os.path.exists(cls.sample_video_path):
            raise unittest.SkipTest(f"Test video not found: {cls.sample_video_path}")
    
    def test_full_pipeline(self):

        with tempfile.TemporaryDirectory() as temp_dir:
            result = process_video(
                self.sample_video_path,
                temp_dir,
                OutputFormat.JSON,
                mux_video=True
            )
            
            self.assertTrue(os.path.exists(result["outputs"]["script"]))
            self.assertTrue(os.path.exists(result["outputs"]["audio"]))
            if "muxed_video" in result["outputs"]:
                self.assertTrue(os.path.exists(result["outputs"]["muxed_video"]))
            
            with open(result["outputs"]["script"]) as f:
                script_data = json.load(f)
                self.assertIn("segments", script_data)
                self.assertIsInstance(script_data["segments"], list)
                self.assertGreater(len(script_data["segments"]), 0)
            
            audio_size = os.path.getsize(result["outputs"]["audio"])
            self.assertGreater(audio_size, 1024)  

if __name__ == "__main__":
    unittest.main()