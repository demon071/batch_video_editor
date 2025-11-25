"""Font detection and management utilities."""
import os
from pathlib import Path
from typing import List, Tuple, Optional


def get_system_fonts() -> List[Tuple[str, str]]:
    """
    Detect system fonts from Windows font directories.
    
    Returns:
        List of (font_name, font_path) tuples
    """
    fonts = []
    font_extensions = {'.ttf', '.otf', '.ttc'}
    
    # Windows font directories
    font_dirs = [
        Path(r'C:\Windows\Fonts'),
        Path(os.path.expanduser(r'~\AppData\Local\Microsoft\Windows\Fonts')),
    ]
    
    for font_dir in font_dirs:
        if not font_dir.exists():
            continue
        
        try:
            for font_file in font_dir.iterdir():
                if font_file.suffix.lower() in font_extensions:
                    font_name = get_font_name_from_path(font_file)
                    fonts.append((font_name, str(font_file)))
        except (PermissionError, OSError):
            continue
    
    # Sort by font name
    fonts.sort(key=lambda x: x[0].lower())
    
    # Remove duplicates (keep first occurrence)
    seen = set()
    unique_fonts = []
    for name, path in fonts:
        if name.lower() not in seen:
            seen.add(name.lower())
            unique_fonts.append((name, path))
    
    return unique_fonts


def get_default_font() -> Optional[str]:
    """
    Get path to a reliable default font.
    
    Returns:
        Path to default font or None if not found
    """
    # Try common default fonts in order of preference
    default_fonts = [
        r'C:\Windows\Fonts\arial.ttf',
        r'C:\Windows\Fonts\verdana.ttf',
        r'C:\Windows\Fonts\calibri.ttf',
        r'C:\Windows\Fonts\tahoma.ttf',
        r'C:\Windows\Fonts\segoeui.ttf',
    ]
    
    for font_path in default_fonts:
        if Path(font_path).exists():
            return font_path
    
    # If no default found, try to get any .ttf font
    fonts_dir = Path(r'C:\Windows\Fonts')
    if fonts_dir.exists():
        try:
            for font_file in fonts_dir.iterdir():
                if font_file.suffix.lower() == '.ttf':
                    return str(font_file)
        except (PermissionError, OSError):
            pass
    
    return None


def validate_font_path(font_path: Path) -> bool:
    """
    Validate that font file exists and is readable.
    
    Args:
        font_path: Path to font file
        
    Returns:
        True if valid font file
    """
    if not font_path:
        return False
    
    try:
        path = Path(font_path)
        if not path.exists():
            return False
        if not path.is_file():
            return False
        if path.suffix.lower() not in {'.ttf', '.otf', '.ttc'}:
            return False
        return True
    except Exception:
        return False


def get_font_name_from_path(font_path: Path) -> str:
    """
    Extract font family name from file path.
    
    Args:
        font_path: Path to font file
        
    Returns:
        Font family name (cleaned filename without extension)
    """
    # Get filename without extension
    name = font_path.stem
    
    # Clean up common suffixes
    suffixes_to_remove = [
        'Regular', 'Bold', 'Italic', 'BoldItalic',
        'Light', 'Medium', 'Semibold', 'Black',
        '-Regular', '-Bold', '-Italic', '-BoldItalic',
        '_Regular', '_Bold', '_Italic', '_BoldItalic',
    ]
    
    for suffix in suffixes_to_remove:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    
    # Replace underscores and hyphens with spaces
    name = name.replace('_', ' ').replace('-', ' ')
    
    # Clean up multiple spaces
    name = ' '.join(name.split())
    
    return name.strip()


def escape_font_path_for_ffmpeg(font_path: str) -> str:
    """
    Escape font path for FFmpeg drawtext filter.
    
    Args:
        font_path: Windows font path
        
    Returns:
        Escaped path suitable for FFmpeg
    """
    # Convert backslashes to forward slashes
    path = font_path.replace('\\', '/')
    
    # Escape colons (for Windows drive letters)
    path = path.replace(':', '\\:')
    
    return path
