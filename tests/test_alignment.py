import os
import sys
import unittest
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from narrative_generator import NarrativeSegment
from scene_analyzer import VideoScene

class TestAlignment(unittest.TestCase):

    
    def test_narrative_timing(self):

        scenes = [
            VideoScene(
                start_time=0.0,
                end_time=10.0,
                duration=10.0,
                keyframe_path="",
                scene_type="wide-shot"
            ),
            VideoScene(
                start_time=10.0,
                end_time=20.0,
                duration=10.0,
                keyframe_path="",
                scene_type="close-up"
            ),
            VideoScene(
                start_time=20.0,
                end_time=30.0,
                duration=10.0,
                keyframe_path="",
                scene_type="medium-shot"
            )
        ]
        
        narrative = [
            NarrativeSegment(
                start_time=0.0,
                end_time=10.0,
                duration=10.0,
                text="This is the first scene.",
                scene_idx=0
            ),
            NarrativeSegment(
                start_time=10.0,
                end_time=20.0,
                duration=10.0,
                text="This is the second scene.",
                scene_idx=1
            ),
            NarrativeSegment(
                start_time=20.0,
                end_time=30.0,
                duration=10.0,
                text="This is the third scene.",
                scene_idx=2
            )
        ]
        
        for i, (scene, segment) in enumerate(zip(scenes, narrative)):
            self.assertEqual(segment.start_time, scene.start_time, f"Segment {i} start time mismatch")
            self.assertEqual(segment.end_time, scene.end_time, f"Segment {i} end time mismatch")
            self.assertEqual(segment.duration, scene.duration, f"Segment {i} duration mismatch")
            self.assertEqual(segment.scene_idx, i, f"Segment {i} scene index mismatch")
    
    def test_segment_coverage(self):

        narrative = [
            NarrativeSegment(
                start_time=0.0,
                end_time=10.0,
                duration=10.0,
                text="This is the first segment.",
                scene_idx=0
            ),
            NarrativeSegment(
                start_time=10.0,
                end_time=20.0,
                duration=10.0,
                text="This is the second segment.",
                scene_idx=1
            ),
            NarrativeSegment(
                start_time=20.0,
                end_time=30.0,
                duration=10.0,
                text="This is the third segment.",
                scene_idx=2
            )
        ]
        
        video_duration = 30.0
        covered_duration = sum(segment.duration for segment in narrative)
        coverage_percentage = (covered_duration / video_duration) * 100
        
        self.assertGreaterEqual(
            coverage_percentage, 
            95.0, 
            f"Narration coverage ({coverage_percentage:.2f}%) is less than required 95%"
        )

if __name__ == "__main__":
    unittest.main()