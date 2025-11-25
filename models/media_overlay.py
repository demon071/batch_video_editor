"""Media overlay settings model."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple
from models.enums import OverlayType, OverlayPosition


@dataclass
class MediaOverlay:
    """
    Settings for media overlay (image/video overlay, intro/outro).
    
    Supports:
    - Image overlay: Static image on top of video
    - Video overlay: Video playing on top of main video
    - Intro video: Video played before main video
    - Outro video: Video played after main video
    """
    
    # Enable/disable
    enabled: bool = False
    
    # Overlay type
    overlay_type: OverlayType = OverlayType.IMAGE
    
    # Media source
    media_path: Optional[Path] = None
    
    # Position & Size (for IMAGE and VIDEO overlays)
    position_preset: OverlayPosition = OverlayPosition.TOP_RIGHT
    custom_x: int = 10
    custom_y: int = 10
    scale_width: Optional[int] = None  # None = original size
    scale_height: Optional[int] = None  # None = original size
    
    # Appearance
    opacity: float = 1.0  # 0.0 (transparent) - 1.0 (opaque)
    
    # Timing (for VIDEO overlay)
    start_time: float = 0.0  # seconds from start of main video
    duration: Optional[float] = None  # None = until end of main video
    loop: bool = False  # Loop overlay video if shorter than duration
    
    # Intro/Outro specific
    fade_duration: float = 0.5  # seconds for fade in/out
    mix_audio: bool = True  # Mix audio from intro/outro with main video
    
    def is_active(self) -> bool:
        """Check if overlay is enabled and has valid media."""
        return self.enabled and self.media_path is not None and self.media_path.exists()
    
    def get_position_coords(self, video_width: int, video_height: int, 
                           overlay_width: int, overlay_height: int) -> Tuple[int, int]:
        """
        Calculate overlay position coordinates based on preset.
        
        Args:
            video_width: Main video width
            video_height: Main video height
            overlay_width: Overlay media width
            overlay_height: Overlay media height
            
        Returns:
            Tuple of (x, y) coordinates
        """
        if self.position_preset == OverlayPosition.CUSTOM:
            return (self.custom_x, self.custom_y)
        
        margin = 10  # pixels from edge
        
        positions = {
            OverlayPosition.TOP_LEFT: (margin, margin),
            OverlayPosition.TOP_RIGHT: (video_width - overlay_width - margin, margin),
            OverlayPosition.BOTTOM_LEFT: (margin, video_height - overlay_height - margin),
            OverlayPosition.BOTTOM_RIGHT: (
                video_width - overlay_width - margin,
                video_height - overlay_height - margin
            ),
            OverlayPosition.CENTER: (
                (video_width - overlay_width) // 2,
                (video_height - overlay_height) // 2
            ),
        }
        
        return positions.get(self.position_preset, (margin, margin))
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'enabled': self.enabled,
            'overlay_type': self.overlay_type.value,
            'media_path': str(self.media_path) if self.media_path else None,
            'position_preset': self.position_preset.value,
            'custom_x': self.custom_x,
            'custom_y': self.custom_y,
            'scale_width': self.scale_width,
            'scale_height': self.scale_height,
            'opacity': self.opacity,
            'start_time': self.start_time,
            'duration': self.duration,
            'loop': self.loop,
            'fade_duration': self.fade_duration,
            'mix_audio': self.mix_audio,
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'MediaOverlay':
        """Create from dictionary."""
        return MediaOverlay(
            enabled=data.get('enabled', False),
            overlay_type=OverlayType(data.get('overlay_type', OverlayType.IMAGE.value)),
            media_path=Path(data['media_path']) if data.get('media_path') else None,
            position_preset=OverlayPosition(data.get('position_preset', OverlayPosition.TOP_RIGHT.value)),
            custom_x=data.get('custom_x', 10),
            custom_y=data.get('custom_y', 10),
            scale_width=data.get('scale_width'),
            scale_height=data.get('scale_height'),
            opacity=data.get('opacity', 1.0),
            start_time=data.get('start_time', 0.0),
            duration=data.get('duration'),
            loop=data.get('loop', False),
            fade_duration=data.get('fade_duration', 0.5),
            mix_audio=data.get('mix_audio', True),
        )
