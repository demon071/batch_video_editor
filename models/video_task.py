"""Video task data model."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, TYPE_CHECKING
from .enums import TaskStatus, VideoCodec, Preset, QualityMode, WatermarkType

if TYPE_CHECKING:
    from .text_settings import TextSettings



@dataclass(eq=False)
class VideoTask:
    """
    Represents a single video processing task.
    
    Attributes:
        input_path: Path to input video file
        output_path: Path to output video file
        status: Current processing status
        progress: Progress percentage (0-100)
        error_message: Error description if status is ERROR
        
        # Processing parameters
        speed: Playback speed multiplier (0.5 - 2.0)
        volume: Volume multiplier (0.0 - 2.0)
        trim_start: Start time in seconds (None = from beginning)
        trim_end: End time in seconds (None = to end)
        scale: Target resolution as (width, height) tuple (None = original)
        crop: Crop region as (x, y, width, height) tuple (None = no crop)
        
        # Watermark settings
        watermark_type: Type of watermark (NONE, TEXT, IMAGE)
        watermark_text: Text to display (if watermark_type is TEXT)
        watermark_image: Path to watermark image (if watermark_type is IMAGE)
        watermark_position: Position as (x, y) tuple
        
        # Subtitle settings
        subtitle_file: Path to SRT subtitle file (None = no subtitles)
        
        # Codec settings
        codec: Video codec to use
        quality_mode: Quality control mode (CRF or BITRATE)
        crf: CRF value (0-51, lower = better quality)
        bitrate: Target bitrate (e.g., "5M", "1000k")
        preset: Encoding speed preset
        
        # Metadata
        duration: Video duration in seconds (populated after analysis)
        original_resolution: Original video resolution as (width, height)
    """
    
    input_path: Path
    output_path: Path
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    error_message: str = ""
    
    # Processing parameters
    speed: float = 1.0
    volume: float = 1.0
    trim_start: Optional[float] = None
    trim_end: Optional[float] = None  # Absolute end time (deprecated in UI, kept for compatibility)
    cut_from_end: Optional[float] = None  # Seconds to cut from end
    scale: Optional[Tuple[int, int]] = None
    crop: Optional[Tuple[int, int, int, int]] = None
    
    # Watermark settings
    watermark_type: WatermarkType = WatermarkType.NONE
    watermark_text: str = ""
    watermark_image: Optional[Path] = None
    watermark_position: Tuple[int, int] = (10, 10)
    
    # Subtitle settings
    subtitle_file: Optional[Path] = None
    
    # Text overlay settings
    text_settings: Optional['TextSettings'] = None
    
    # Media overlay settings (Phase 3)
    image_overlay: Optional[dict] = None
    video_overlay: Optional[dict] = None
    intro_video: Optional[dict] = None
    outro_video: Optional[dict] = None
    
    # Codec settings
    codec: VideoCodec = VideoCodec.H264
    quality_mode: QualityMode = QualityMode.CRF
    crf: int = 23
    bitrate: str = "5M"
    preset: Preset = Preset.MEDIUM
    
    # Metadata
    duration: float = 0.0
    original_resolution: Optional[Tuple[int, int]] = None
    
    def __post_init__(self):
        """Convert string paths to Path objects."""
        if isinstance(self.input_path, str):
            self.input_path = Path(self.input_path)
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)
        if self.watermark_image and isinstance(self.watermark_image, str):
            self.watermark_image = Path(self.watermark_image)
        if self.subtitle_file and isinstance(self.subtitle_file, str):
            self.subtitle_file = Path(self.subtitle_file)
    
    @property
    def filename(self) -> str:
        """Get input filename."""
        return self.input_path.name
    
    @property
    def is_complete(self) -> bool:
        """Check if task is complete (done or error)."""
        return self.status in (TaskStatus.DONE, TaskStatus.ERROR, TaskStatus.CANCELLED)
    
    @property
    def is_processing(self) -> bool:
        """Check if task is currently processing."""
        return self.status == TaskStatus.PROCESSING
    
    def reset(self):
        """Reset task to pending state."""
        self.status = TaskStatus.PENDING
        self.progress = 0.0
        self.error_message = ""
    
    def set_error(self, message: str):
        """Set task to error state with message."""
        self.status = TaskStatus.ERROR
        self.error_message = message
        self.progress = 0.0
    
    def set_processing(self):
        """Set task to processing state."""
        self.status = TaskStatus.PROCESSING
        self.progress = 0.0
        self.error_message = ""
    
    def set_done(self):
        """Set task to done state."""
        self.status = TaskStatus.DONE
        self.progress = 100.0
        self.error_message = ""
    
    def set_cancelled(self):
        """Set task to cancelled state."""
        self.status = TaskStatus.CANCELLED
        self.error_message = "Cancelled by user"
    
    def __hash__(self):
        """Make task hashable based on object identity."""
        return id(self)
    
    def __eq__(self, other):
        """Check equality based on object identity."""
        return self is other
