"""Enumerations for video processing tasks."""
from enum import Enum, auto


class TaskStatus(Enum):
    """Status of a video processing task."""
    PENDING = auto()
    PROCESSING = auto()
    DONE = auto()
    ERROR = auto()
    CANCELLED = auto()

    def __str__(self):
        return self.name.capitalize()


class VideoCodec(Enum):
    """Supported video codecs."""
    H264 = "libx264"
    HEVC = "libx265"
    H264_NVENC = "h264_nvenc"
    HEVC_NVENC = "hevc_nvenc"

    def __str__(self):
        return self.name

    @property
    def is_gpu(self):
        """Check if codec uses GPU acceleration."""
        return "nvenc" in self.value


class Preset(Enum):
    """Encoding speed presets."""
    ULTRAFAST = "ultrafast"
    SUPERFAST = "superfast"
    VERYFAST = "veryfast"
    FASTER = "faster"
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    SLOWER = "slower"
    VERYSLOW = "veryslow"

    def __str__(self):
        return self.value.capitalize()


class QualityMode(Enum):
    """Quality control mode."""
    CRF = "crf"
    BITRATE = "bitrate"

    def __str__(self):
        return self.name




class TextPosition(str, Enum):
    """Text overlay position presets."""
    TOP_LEFT = "Top-Left"
    TOP_RIGHT = "Top-Right"
    BOTTOM_LEFT = "Bottom-Left"
    BOTTOM_RIGHT = "Bottom-Right"
    CENTER = "Center"
    CUSTOM = "Custom"
    
    def __str__(self):
        return self.value


class OverlayType(str, Enum):
    """Media overlay types."""
    IMAGE = "Image Overlay"
    VIDEO = "Video Overlay"
    INTRO = "Intro Video"
    OUTRO = "Outro Video"
    
    def __str__(self):
        return self.value


class OverlayPosition(str, Enum):
    """Media overlay position presets."""
    TOP_LEFT = "Top-Left"
    TOP_RIGHT = "Top-Right"
    BOTTOM_LEFT = "Bottom-Left"
    BOTTOM_RIGHT = "Bottom-Right"
    CENTER = "Center"
    CUSTOM = "Custom"
    
    def __str__(self):
        return self.value


class SplitMode(str, Enum):
    """Video split modes."""
    DISABLED = "Disabled"
    BY_COUNT = "By Count"
    BY_DURATION = "By Duration"
    
    def __str__(self):
        return self.value
