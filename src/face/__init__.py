"""Layer 3: Face — Avatar Rendering."""

from src.face.pipeline import (
    AvatarPipeline,
    GFPGANEnhancer,
    IdentityController,
    MuseTalkEngine,
    TemporalSmoother,
    VideoFrame,
)
from src.face.livetalking_adapter import LiveTalkingEngine, LiveTalkingPipeline
from src.face.livetalking_manager import LiveTalkingManager, get_livetalking_manager

__all__ = [
    "AvatarPipeline", "GFPGANEnhancer", "IdentityController",
    "MuseTalkEngine", "TemporalSmoother", "VideoFrame",
    "LiveTalkingEngine", "LiveTalkingPipeline",
    "LiveTalkingManager", "get_livetalking_manager",
]
