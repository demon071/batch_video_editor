"""Input validation utilities."""
import re
from pathlib import Path
from typing import Optional, Tuple


def validate_time_format(time_str: str) -> bool:
    """
    Validate time format (HH:MM:SS, MM:SS, or SS).
    
    Args:
        time_str: Time string to validate
        
    Returns:
        True if valid format
    """
    if not time_str or not time_str.strip():
        return True  # Empty is valid (means not set)
    
    # Match HH:MM:SS, MM:SS, or SS
    pattern = r'^(\d{1,2}:)?\d{1,2}(:\d{1,2})?$'
    return bool(re.match(pattern, time_str.strip()))


def validate_resolution(width: int, height: int) -> bool:
    """
    Validate video resolution.
    
    Args:
        width: Video width in pixels
        height: Video height in pixels
        
    Returns:
        True if valid resolution
    """
    # Check reasonable bounds
    if width < 1 or height < 1:
        return False
    if width > 7680 or height > 4320:  # Max 8K
        return False
    
    # Check if divisible by 2 (required by most codecs)
    if width % 2 != 0 or height % 2 != 0:
        return False
    
    return True


def validate_file_path(file_path: Path, must_exist: bool = True) -> bool:
    """
    Validate file path.
    
    Args:
        file_path: Path to validate
        must_exist: If True, file must exist
        
    Returns:
        True if valid
    """
    if not file_path:
        return False
    
    try:
        path = Path(file_path)
        
        if must_exist:
            return path.exists() and path.is_file()
        else:
            # Check if parent directory exists
            return path.parent.exists()
            
    except Exception:
        return False


def validate_bitrate(bitrate_str: str) -> Optional[str]:
    """
    Validate and normalize bitrate string.
    
    Args:
        bitrate_str: Bitrate string (e.g., "5M", "1000k", "500000")
        
    Returns:
        Normalized bitrate string or None if invalid
    """
    if not bitrate_str or not bitrate_str.strip():
        return None
    
    bitrate_str = bitrate_str.strip().upper()
    
    # Match patterns like "5M", "1000K", "500000"
    pattern = r'^(\d+\.?\d*)([KM])?$'
    match = re.match(pattern, bitrate_str)
    
    if not match:
        return None
    
    value = match.group(1)
    unit = match.group(2)
    
    # Normalize to include unit
    if unit:
        return f"{value}{unit}"
    else:
        # No unit means bits per second, convert to K
        try:
            bits = int(float(value))
            return f"{bits // 1000}K"
        except ValueError:
            return None


def validate_crop_region(x: int, y: int, width: int, height: int, 
                        video_width: int, video_height: int) -> bool:
    """
    Validate crop region is within video bounds.
    
    Args:
        x: Crop X position
        y: Crop Y position
        width: Crop width
        height: Crop height
        video_width: Original video width
        video_height: Original video height
        
    Returns:
        True if valid crop region
    """
    # Check bounds
    if x < 0 or y < 0:
        return False
    if width <= 0 or height <= 0:
        return False
    if x + width > video_width:
        return False
    if y + height > video_height:
        return False
    
    # Check divisible by 2
    if width % 2 != 0 or height % 2 != 0:
        return False
    
    return True


def validate_speed(speed: float) -> bool:
    """
    Validate playback speed.
    
    Args:
        speed: Speed multiplier
        
    Returns:
        True if valid (0.5 - 2.0)
    """
    return 0.5 <= speed <= 2.0


def validate_volume(volume: float) -> bool:
    """
    Validate volume level.
    
    Args:
        volume: Volume multiplier
        
    Returns:
        True if valid (0.0 - 2.0)
    """
    return 0.0 <= volume <= 2.0


def validate_crf(crf: int) -> bool:
    """
    Validate CRF value.
    
    Args:
        crf: CRF value
        
    Returns:
        True if valid (0 - 51)
    """
    return 0 <= crf <= 51


def validate_hex_color(color_str: str) -> bool:
    """
    Validate hex color format.
    
    Args:
        color_str: Color string to validate
        
    Returns:
        True if valid hex color (#RRGGBB or #RGB)
    """
    if not color_str:
        return False
    
    # Remove # if present
    color = color_str.strip()
    if color.startswith('#'):
        color = color[1:]
    
    # Check length (3 or 6 hex digits)
    if len(color) not in (3, 6):
        return False
    
    # Check all characters are hex digits
    try:
        int(color, 16)
        return True
    except ValueError:
        return False


def validate_opacity(opacity: float) -> bool:
    """
    Validate opacity value.
    
    Args:
        opacity: Opacity value
        
    Returns:
        True if valid (0.0 - 1.0)
    """
    return 0.0 <= opacity <= 1.0


def validate_font_size(size: int) -> bool:
    """
    Validate font size.
    
    Args:
        size: Font size in pixels
        
    Returns:
        True if valid (6 - 200)
    """
    return 6 <= size <= 200


def normalize_hex_color(color_str: str) -> str:
    """
    Normalize hex color to #RRGGBB format.
    
    Args:
        color_str: Color string (#RGB or #RRGGBB)
        
    Returns:
        Normalized color string or original if invalid
    """
    if not validate_hex_color(color_str):
        return color_str
    
    color = color_str.strip()
    if not color.startswith('#'):
        color = '#' + color
    
    # Expand #RGB to #RRGGBB
    if len(color) == 4:  # #RGB
        r, g, b = color[1], color[2], color[3]
        color = f'#{r}{r}{g}{g}{b}{b}'
    
    return color.upper()

