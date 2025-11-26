"""FFmpeg video splitter with stream copy support."""
import subprocess
import re
from pathlib import Path
from typing import List, Tuple, Optional
from models.video_task import VideoTask
from models.split_settings import SplitSettings
from models.enums import SplitMode


class FFmpegSplitter:
    """
    Handles video splitting using FFmpeg with stream copy for fast, lossless splitting.
    
    Supports:
    - Split by count: Split video into N equal parts
    - Split by duration: Split video into segments of X seconds
    - Keyframe-accurate cutting to prevent corruption
    - Stream copy (no re-encoding) for speed
    """
    
    @staticmethod
    def split_video(task: VideoTask) -> List[Path]:
        """
        Split video based on task settings.
        
        Args:
            task: VideoTask with split settings
            
        Returns:
            List of output file paths
            
        Raises:
            ValueError: If settings are invalid
            RuntimeError: If FFmpeg command fails
        """
        if not task.split_settings or not task.split_settings.enabled:
            raise ValueError("Split settings not enabled")
        
        settings = task.split_settings
        
        # Validate settings
        is_valid, error_msg = settings.validate()
        if not is_valid:
            raise ValueError(f"Invalid split settings: {error_msg}")
        
        # Get video duration if not already set
        if task.duration <= 0:
            task.duration = FFmpegSplitter._get_video_duration(task.input_path)
        
        # Prepare output directory
        output_dir = task.output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Split based on mode
        if settings.mode == SplitMode.BY_COUNT:
            return FFmpegSplitter._split_by_count(
                task.input_path,
                output_dir,
                settings.num_parts,
                task.duration,
                settings.output_pattern,
                settings.use_stream_copy
            )
        elif settings.mode == SplitMode.BY_DURATION:
            return FFmpegSplitter._split_by_duration(
                task.input_path,
                output_dir,
                settings.duration_seconds,
                settings.output_pattern,
                settings.use_stream_copy
            )
        else:
            raise ValueError(f"Unknown split mode: {settings.mode}")
    
    @staticmethod
    def _split_by_count(
        input_path: Path,
        output_dir: Path,
        num_parts: int,
        duration: float,
        output_pattern: str,
        use_stream_copy: bool = True
    ) -> List[Path]:
        """
        Split video into N equal parts.
        
        Args:
            input_path: Input video file
            output_dir: Output directory
            num_parts: Number of parts to split into
            duration: Video duration in seconds
            output_pattern: Output filename pattern
            use_stream_copy: Use stream copy (no re-encoding)
            
        Returns:
            List of output file paths
        """
        # Calculate segment duration
        segment_duration = duration / num_parts
        
        # Calculate split points (start times for each segment)
        split_points = []
        for i in range(num_parts):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration if i < num_parts - 1 else duration
            split_points.append((start_time, end_time - start_time))
        
        # Generate output files
        output_files = []
        name = input_path.stem
        ext = input_path.suffix
        
        for i, (start_time, segment_len) in enumerate(split_points, start=1):
            # Format output filename
            output_name = output_pattern.format(
                name=name,
                num=i,
                ext=ext
            )
            output_path = output_dir / output_name
            
            # Build FFmpeg command
            cmd = FFmpegSplitter._build_split_command(
                input_path,
                output_path,
                start_time,
                segment_len,
                use_stream_copy
            )
            
            # Execute command
            FFmpegSplitter._execute_command(cmd, output_path)
            output_files.append(output_path)
        
        return output_files
    
    @staticmethod
    def _split_by_duration(
        input_path: Path,
        output_dir: Path,
        segment_duration: float,
        output_pattern: str,
        use_stream_copy: bool = True
    ) -> List[Path]:
        """
        Split video into segments of specified duration.
        
        Args:
            input_path: Input video file
            output_dir: Output directory
            segment_duration: Duration of each segment in seconds
            output_pattern: Output filename pattern
            use_stream_copy: Use stream copy (no re-encoding)
            
        Returns:
            List of output file paths
        """
        name = input_path.stem
        ext = input_path.suffix
        
        # Use FFmpeg segment muxer for efficient splitting
        # Output pattern for segment muxer
        segment_pattern = output_pattern.replace('{name}', name).replace('{ext}', ext)
        segment_pattern = segment_pattern.replace('{num:03d}', '%03d')
        segment_pattern = segment_pattern.replace('{num}', '%d')
        
        output_path = output_dir / segment_pattern
        
        # Build FFmpeg command with segment muxer
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-f', 'segment',
            '-segment_time', str(segment_duration),
            '-reset_timestamps', '1',
            '-break_non_keyframes', '0',  # Only break at keyframes
        ]
        
        if use_stream_copy:
            cmd.extend(['-c', 'copy'])
        else:
            cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
        
        cmd.extend([
            '-avoid_negative_ts', '1',
            str(output_path)
        ])
        
        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        
        # Find all generated files
        output_files = sorted(output_dir.glob(f"{name}_part*{ext}"))
        
        return output_files
    
    @staticmethod
    def _build_split_command(
        input_path: Path,
        output_path: Path,
        start_time: float,
        duration: float,
        use_stream_copy: bool = True
    ) -> List[str]:
        """
        Build FFmpeg command for splitting a segment.
        
        Args:
            input_path: Input video file
            output_path: Output file path
            start_time: Start time in seconds
            duration: Segment duration in seconds
            use_stream_copy: Use stream copy (no re-encoding)
            
        Returns:
            FFmpeg command as list of arguments
        """
        # Use -ss before -i for fast seeking (input seeking)
        # Then use -t for duration
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', str(input_path),
            '-t', str(duration),
        ]
        
        if use_stream_copy:
            cmd.extend(['-c', 'copy'])
        else:
            cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
        
        cmd.extend([
            '-avoid_negative_ts', '1',
            '-y',  # Overwrite output file
            str(output_path)
        ])
        
        return cmd
    
    @staticmethod
    def _execute_command(cmd: List[str], output_path: Path) -> None:
        """
        Execute FFmpeg command.
        
        Args:
            cmd: FFmpeg command arguments
            output_path: Expected output file path
            
        Raises:
            RuntimeError: If command fails
        """
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg failed for {output_path.name}:\n{result.stderr}"
            )
        
        if not output_path.exists():
            raise RuntimeError(f"Output file not created: {output_path}")
    
    @staticmethod
    def _get_video_duration(video_path: Path) -> float:
        """
        Get video duration using ffprobe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds
            
        Raises:
            RuntimeError: If ffprobe fails
        """
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr}")
        
        try:
            duration = float(result.stdout.strip())
            return duration
        except ValueError:
            raise RuntimeError(f"Invalid duration output: {result.stdout}")
    
    @staticmethod
    def get_keyframes(video_path: Path) -> List[float]:
        """
        Get keyframe timestamps from video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of keyframe timestamps in seconds
            
        Note:
            This is useful for advanced keyframe-accurate splitting,
            but current implementation uses FFmpeg's built-in keyframe detection.
        """
        cmd = [
            'ffprobe',
            '-select_streams', 'v:0',
            '-show_entries', 'frame=pkt_pts_time,pict_type',
            '-of', 'csv=p=0',
            str(video_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode != 0:
            return []
        
        keyframes = []
        for line in result.stdout.strip().split('\n'):
            parts = line.split(',')
            if len(parts) >= 2 and parts[1] == 'I':
                try:
                    timestamp = float(parts[0])
                    keyframes.append(timestamp)
                except ValueError:
                    continue
        
        return keyframes
    
    @staticmethod
    def validate_task(task: VideoTask) -> Tuple[bool, str]:
        """
        Validate task for splitting.
        
        Args:
            task: VideoTask to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not task.split_settings:
            return False, "Split settings not configured"
        
        if not task.split_settings.enabled:
            return False, "Split not enabled"
        
        if not task.input_path.exists():
            return False, f"Input file not found: {task.input_path}"
        
        # Validate split settings
        is_valid, error_msg = task.split_settings.validate()
        if not is_valid:
            return False, error_msg
        
        return True, ""
