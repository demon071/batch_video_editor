"""System check utilities for FFmpeg and GPU support."""
import subprocess
import re
import json
from pathlib import Path
from typing import Optional, Dict, Tuple


def check_ffmpeg() -> Tuple[bool, str]:
    """
    Check if FFmpeg is installed and accessible.
    
    Returns:
        Tuple of (is_available, version_string)
    """
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        if result.returncode == 0:
            # Extract version from first line
            first_line = result.stdout.split('\n')[0]
            version_match = re.search(r'ffmpeg version ([\d.]+)', first_line)
            version = version_match.group(1) if version_match else "unknown"
            return True, f"FFmpeg {version}"
        else:
            return False, "FFmpeg not found"
            
    except FileNotFoundError:
        return False, "FFmpeg not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "FFmpeg check timeout"
    except Exception as e:
        return False, f"Error checking FFmpeg: {str(e)}"


def check_nvenc_support() -> Tuple[bool, str]:
    """
    Check if NVIDIA NVENC encoders are available.
    
    Returns:
        Tuple of (is_available, message)
    """
    try:
        # Try to get list of encoders
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        if result.returncode == 0:
            output = result.stdout
            
            # Check for NVENC encoders
            has_h264_nvenc = 'h264_nvenc' in output
            has_hevc_nvenc = 'hevc_nvenc' in output
            
            if has_h264_nvenc or has_hevc_nvenc:
                encoders = []
                if has_h264_nvenc:
                    encoders.append("H.264 NVENC")
                if has_hevc_nvenc:
                    encoders.append("HEVC NVENC")
                return True, f"GPU encoding available: {', '.join(encoders)}"
            else:
                return False, "NVENC not available (no NVIDIA GPU or driver issue)"
        else:
            return False, "Could not check encoder support"
            
    except FileNotFoundError:
        return False, "FFmpeg not found"
    except subprocess.TimeoutExpired:
        return False, "Encoder check timeout"
    except Exception as e:
        return False, f"Error checking NVENC: {str(e)}"


def get_video_info(video_path: Path) -> Optional[Dict]:
    """
    Extract video metadata using ffprobe.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dictionary with video info (duration, width, height, codec) or None if error
    """
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        if result.returncode != 0 or not result.stdout:
            return None
        
        # Check if stdout is valid before parsing
        if not result.stdout.strip():
            return None
        
        data = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            return None
        
        # Extract info with safe defaults
        duration = data.get('format', {}).get('duration', '0')
        bitrate = data.get('format', {}).get('bit_rate', '0')
        
        # Safely parse FPS
        fps_str = video_stream.get('r_frame_rate', '0/1')
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                fps = float(num) / float(den) if float(den) != 0 else 0.0
            else:
                fps = float(fps_str)
        except:
            fps = 0.0
        
        info = {
            'duration': float(duration) if duration else 0.0,
            'width': int(video_stream.get('width', 0)),
            'height': int(video_stream.get('height', 0)),
            'codec': video_stream.get('codec_name', 'unknown'),
            'bitrate': int(bitrate) if bitrate else 0,
            'fps': fps
        }
        
        return info
        
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from ffprobe: {e}")
        return None
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to HH:MM:SS.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_duration(time_str: str) -> Optional[float]:
    """
    Parse time string (HH:MM:SS or MM:SS or SS) to seconds.
    
    Args:
        time_str: Time string
        
    Returns:
        Duration in seconds or None if invalid
    """
    try:
        parts = time_str.strip().split(':')
        parts = [int(p) for p in parts]
        
        if len(parts) == 1:  # SS
            return float(parts[0])
        elif len(parts) == 2:  # MM:SS
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:  # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        else:
            return None
    except (ValueError, IndexError):
        return None
