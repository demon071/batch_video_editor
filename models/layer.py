"""
Layer model for multi-layer overlay system.

Represents a single overlay layer (text, image, or video) with positioning,
timing, and z-index for rendering order.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class LayerType(Enum):
    """Type of overlay layer."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    MAIN_VIDEO = "main_video"
    BACKGROUND = "background"


@dataclass
class Layer:
    """
    Represents a single overlay layer.
    
    Attributes:
        id: Unique identifier for the layer
        type: Type of layer (TEXT, IMAGE, VIDEO)
        z_index: Rendering order (0 = bottom, higher = on top)
        enabled: Whether the layer is active
        name: Display name for the layer
        
        # Positioning
        position: (x, y) coordinates in pixels or expressions
        
        # Timing
        start_time: When to show the layer (seconds, None = from start)
        end_time: When to hide the layer (seconds, None = until end)
        
        # Type-specific properties
        properties: Flexible dict for layer-specific settings
    """
    
    # Core attributes
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: LayerType = LayerType.TEXT
    z_index: int = 0
    enabled: bool = True
    name: str = ""
    
    # Positioning
    position: tuple = (10, 10)  # (x, y)
    
    # Timing
    start_time: Optional[float] = None  # None = from start
    end_time: Optional[float] = None    # None = until end
    
    # Type-specific properties
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default name if not provided."""
        if not self.name:
            self.name = f"{self.type.value.capitalize()} {self.z_index + 1}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert layer to dictionary for serialization."""
        return {
            'id': self.id,
            'type': self.type.value,
            'z_index': self.z_index,
            'enabled': self.enabled,
            'name': self.name,
            'position': self.position,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'properties': self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Layer':
        """Create layer from dictionary."""
        layer_type = LayerType(data.get('type', 'text'))
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            type=layer_type,
            z_index=data.get('z_index', 0),
            enabled=data.get('enabled', True),
            name=data.get('name', ''),
            position=tuple(data.get('position', (10, 10))),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            properties=data.get('properties', {})
        )
    
    def get_timing_expression(self) -> Optional[str]:
        """
        Get FFmpeg enable expression for timing.
        
        Returns:
            FFmpeg enable expression or None if always visible
        """
        if self.start_time is None and self.end_time is None:
            return None
        
        if self.start_time is not None and self.end_time is not None:
            return f"between(t,{self.start_time},{self.end_time})"
        elif self.start_time is not None:
            return f"gte(t,{self.start_time})"
        elif self.end_time is not None:
            return f"lte(t,{self.end_time})"
        
        return None


# Property keys for each layer type
class TextLayerProperties:
    """Property keys for text layers."""
    TEXT = 'text'
    FONT_FILE = 'font_file'
    FONT_SIZE = 'font_size'
    FONT_COLOR = 'font_color'
    BORDER_WIDTH = 'border_width'
    BORDER_COLOR = 'border_color'
    SHADOW_OFFSET = 'shadow_offset'
    SHADOW_COLOR = 'shadow_color'


class ImageLayerProperties:
    """Property keys for image layers."""
    FILE_PATH = 'file_path'
    SCALE_WIDTH = 'scale_width'
    SCALE_HEIGHT = 'scale_height'
    OPACITY = 'opacity'


class VideoLayerProperties:
    """Property keys for video layers."""
    FILE_PATH = 'file_path'
    SCALE_WIDTH = 'scale_width'
    SCALE_HEIGHT = 'scale_height'
    OPACITY = 'opacity'
    LOOP = 'loop'
