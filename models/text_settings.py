"""Text overlay settings model."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from .enums import TextPosition


@dataclass
class TextSettings:
    """
    Settings for advanced text overlay on videos.
    
    Attributes:
        enabled: Whether text overlay is active
        text: Multi-line text content
        font_family: Font family name
        font_path: Path to font file (.ttf)
        font_size: Font size in pixels
        font_color: Font color in hex format (#RRGGBB)
        outline_color: Outline color in hex format
        outline_thickness: Outline thickness in pixels
        bold: Apply bold style
        italic: Apply italic style
        underline: Apply underline style
        position_preset: Position preset (TOP_LEFT, CENTER, etc.)
        position_x: Custom X position (used when preset is CUSTOM)
        position_y: Custom Y position (used when preset is CUSTOM)
        box_enabled: Enable background box
        box_color: Background box color in hex format
        box_opacity: Background box opacity (0.0-1.0)
    """
    
    enabled: bool = False
    text: str = ""
    font_family: str = ""
    font_path: Optional[Path] = None
    font_size: int = 48
    font_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    outline_thickness: int = 2
    bold: bool = False
    italic: bool = False
    underline: bool = False
    position_preset: TextPosition = TextPosition.TOP_LEFT
    position_x: int = 10
    position_y: int = 10
    box_enabled: bool = False
    box_color: str = "#000000"
    box_opacity: float = 0.5
    
    def __post_init__(self):
        """Convert string paths to Path objects."""
        if self.font_path and isinstance(self.font_path, str):
            self.font_path = Path(self.font_path)
    
    def is_active(self) -> bool:
        """Check if text overlay should be applied."""
        return self.enabled and bool(self.text.strip())
    
    def get_position_coords(self, video_width: int, video_height: int) -> Tuple[int, int]:
        """
        Calculate position coordinates based on preset or custom values.
        
        Args:
            video_width: Video width in pixels
            video_height: Video height in pixels
            
        Returns:
            Tuple of (x, y) coordinates
        """
        if self.position_preset == TextPosition.CUSTOM:
            return (self.position_x, self.position_y)
        
        # Estimate text dimensions (rough approximation)
        # Actual rendering will be done by FFmpeg
        text_width = len(self.text.split('\n')[0]) * self.font_size * 0.6
        text_height = self.font_size * len(self.text.split('\n'))
        
        margin = 10
        
        if self.position_preset == TextPosition.TOP_LEFT:
            return (margin, margin)
        elif self.position_preset == TextPosition.TOP_RIGHT:
            return (int(video_width - text_width - margin), margin)
        elif self.position_preset == TextPosition.BOTTOM_LEFT:
            return (margin, int(video_height - text_height - margin))
        elif self.position_preset == TextPosition.BOTTOM_RIGHT:
            return (int(video_width - text_width - margin), 
                   int(video_height - text_height - margin))
        elif self.position_preset == TextPosition.CENTER:
            return (int((video_width - text_width) / 2), 
                   int((video_height - text_height) / 2))
        else:
            return (self.position_x, self.position_y)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'enabled': self.enabled,
            'text': self.text,
            'font_family': self.font_family,
            'font_path': str(self.font_path) if self.font_path else '',
            'font_size': self.font_size,
            'font_color': self.font_color,
            'outline_color': self.outline_color,
            'outline_thickness': self.outline_thickness,
            'bold': self.bold,
            'italic': self.italic,
            'underline': self.underline,
            'position_preset': self.position_preset.name,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'box_enabled': self.box_enabled,
            'box_color': self.box_color,
            'box_opacity': self.box_opacity,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextSettings':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary with settings
            
        Returns:
            TextSettings instance
        """
        # Convert position preset string to enum
        preset_name = data.get('position_preset', 'TOP_LEFT')
        try:
            position_preset = TextPosition[preset_name]
        except KeyError:
            position_preset = TextPosition.TOP_LEFT
        
        return cls(
            enabled=data.get('enabled', False),
            text=data.get('text', ''),
            font_family=data.get('font_family', ''),
            font_path=Path(data['font_path']) if data.get('font_path') else None,
            font_size=data.get('font_size', 48),
            font_color=data.get('font_color', '#FFFFFF'),
            outline_color=data.get('outline_color', '#000000'),
            outline_thickness=data.get('outline_thickness', 2),
            bold=data.get('bold', False),
            italic=data.get('italic', False),
            underline=data.get('underline', False),
            position_preset=position_preset,
            position_x=data.get('position_x', 10),
            position_y=data.get('position_y', 10),
            box_enabled=data.get('box_enabled', False),
            box_color=data.get('box_color', '#000000'),
            box_opacity=data.get('box_opacity', 0.5),
        )
