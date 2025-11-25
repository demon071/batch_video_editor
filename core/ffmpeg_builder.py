"""FFmpeg command builder using ffmpeg-python library."""
from pathlib import Path
from typing import List, Optional
import ffmpeg
from models.video_task import VideoTask
from models.text_settings import TextSettings
from models.enums import VideoCodec, QualityMode, WatermarkType, OverlayPosition
from utils.font_utils import get_default_font


class FFmpegCommandBuilder:
    """
    Builds FFmpeg command using ffmpeg-python library.
    This handles proper escaping and quoting automatically.
    """
    
    @staticmethod
    def build_command(task: VideoTask) -> List[str]:
        """
        Build FFmpeg command from task parameters using ffmpeg-python.
        
        Args:
            task: VideoTask with processing parameters
            
        Returns:
            List of command arguments
        """
        # Check if overlays are needed (requires filter_complex)
        needs_overlay = FFmpegCommandBuilder._needs_overlay(task)
        
        if needs_overlay:
            return FFmpegCommandBuilder._build_with_overlay(task)
        else:
            return FFmpegCommandBuilder._build_standard(task)
    
    @staticmethod
    def _needs_overlay(task: VideoTask) -> bool:
        """Check if task requires overlay processing."""
        return (
            (task.image_overlay and task.image_overlay.get('enabled', False)) or
            (task.video_overlay and task.video_overlay.get('enabled', False)) or
            (task.intro_video and task.intro_video.get('enabled', False)) or
            (task.outro_video and task.outro_video.get('enabled', False))
        )
    
    @staticmethod
    def _build_standard(task: VideoTask) -> List[str]:
        """
        Build standard FFmpeg command (existing implementation).
        Used when no overlays are needed.
        
        Args:
            task: VideoTask with processing parameters
            
        Returns:
            List of command arguments
        """
        # Start with input
        input_kwargs = {}
        
        # GPU acceleration
        if task.codec.is_gpu:
            input_kwargs['hwaccel'] = 'cuda'
        
        # Trim
        if task.trim_start is not None:
            input_kwargs['ss'] = task.trim_start
        if task.trim_end is not None:
            input_kwargs['to'] = task.trim_end
        
        stream = ffmpeg.input(str(task.input_path), **input_kwargs)
        
        # Build output options
        output_kwargs = {}
        
        # Video filter
        video_filter_string = FFmpegCommandBuilder._build_video_filter_string(task)
        if video_filter_string:
            output_kwargs['vf'] = video_filter_string
        
        # Audio filter
        audio_filter_string = FFmpegCommandBuilder._build_audio_filter_string(task)
        if audio_filter_string:
            output_kwargs['af'] = audio_filter_string
        
        # Video codec
        output_kwargs['vcodec'] = task.codec.value
        
        # Quality settings
        if task.quality_mode == QualityMode.CRF:
            if task.codec.is_gpu:
                output_kwargs['cq'] = task.crf
            else:
                output_kwargs['crf'] = task.crf
        else:
            output_kwargs['video_bitrate'] = task.bitrate
        
        # Preset
        output_kwargs['preset'] = task.preset.value
        
        # Audio codec
        if task.volume != 1.0:
            output_kwargs['acodec'] = 'aac'
            output_kwargs['audio_bitrate'] = '192k'
        else:
            output_kwargs['acodec'] = 'copy'
        
        # Progress reporting
        output_kwargs['progress'] = 'pipe:1'
        
        # Build output
        stream = ffmpeg.output(stream, str(task.output_path), **output_kwargs)
        
        # Overwrite output
        stream = ffmpeg.overwrite_output(stream)
        
        # Compile to command list
        cmd = ffmpeg.compile(stream)
        
        # DEBUG: Print command
        print("\n" + "="*80)
        print("FFmpeg Command (via ffmpeg-python):")
        print("="*80)
        print(' '.join(cmd))
        print("="*80 + "\n")
        
        return cmd
    
    @staticmethod
    def _build_video_filter_string(task: VideoTask) -> str:
        """
        Build video filter string.
        
        Args:
            task: VideoTask with parameters
            
        Returns:
            Filter string (comma-separated)
        """
        filters = []
        
        # Scale
        if task.scale:
            width, height = task.scale
            if task.codec.is_gpu:
                filters.append(f'scale_cuda={width}:{height}')
            else:
                filters.append(f'scale={width}:{height}')
        
        # Crop
        if task.crop:
            x, y, width, height = task.crop
            filters.append(f'crop={width}:{height}:{x}:{y}')
        
        # Speed (setpts)
        if task.speed != 1.0:
            pts_multiplier = 1.0 / task.speed
            filters.append(f'setpts={pts_multiplier}*PTS')
        
        # Watermark (simple text)
        if task.watermark_type == WatermarkType.TEXT and task.watermark_text:
            x, y = task.watermark_position
            text = task.watermark_text.replace("'", "\\'").replace(":", "\\:")
            filters.append(f"drawtext=text='{text}':x={x}:y={y}:fontsize=24:fontcolor=white:borderw=2:bordercolor=black")
        
        # Advanced text overlay
        if task.text_settings and task.text_settings.is_active():
            drawtext_filter = FFmpegCommandBuilder._build_drawtext_filter(task.text_settings, task)
            if drawtext_filter:
                filters.append(drawtext_filter)
        
        # Subtitle burn-in
        if task.subtitle_file:
            subtitle_path = str(task.subtitle_file).replace('\\', '/').replace(':', '\\:')
            filters.append(f'subtitles={subtitle_path}')
        
        return ','.join(filters) if filters else ''
    
    @staticmethod
    def _build_audio_filter_string(task: VideoTask) -> str:
        """
        Build audio filter string.
        
        Args:
            task: VideoTask with parameters
            
        Returns:
            Filter string (comma-separated)
        """
        filters = []
        
        # Volume
        if task.volume != 1.0:
            filters.append(f'volume={task.volume}')
        
        # Speed (atempo)
        if task.speed != 1.0:
            speed = task.speed
            while speed > 2.0:
                filters.append('atempo=2.0')
                speed /= 2.0
            while speed < 0.5:
                filters.append('atempo=0.5')
                speed /= 0.5
            if speed != 1.0:
                filters.append(f'atempo={speed}')
        
        return ','.join(filters) if filters else ''
    
    @staticmethod
    def _build_drawtext_filter(text_settings: TextSettings, task: VideoTask) -> Optional[str]:
        """
        Build drawtext filter string.
        
        Args:
            text_settings: TextSettings with overlay parameters
            task: VideoTask for video dimensions
            
        Returns:
            Drawtext filter string or None
        """
        if not text_settings.text.strip():
            return None
        
        # Escape text
        text = text_settings.text.replace('\\', '\\\\').replace("'", "\\'").replace(':', '\\:').replace('%', '\\%')
        
        parts = [f"text='{text}'"]
        
        # Font file (optional)
        font_path = text_settings.font_path
        if not font_path or not font_path.exists():
            default_font = get_default_font()
            if default_font:
                font_path = Path(default_font)
        
        if font_path and font_path.exists():
            # Escape font path for FFmpeg drawtext filter
            # Windows: C:\path\to\font.ttf -> C\:/path/to/font.ttf
            font_str = str(font_path)
            # First replace all backslashes with forward slashes
            font_str = font_str.replace('\\', '/')
            # Then escape the colon after drive letter: C: -> C\:
            if len(font_str) >= 2 and font_str[1] == ':':
                font_str = font_str[0] + '\\:' + font_str[2:]
            parts.append(f'fontfile={font_str}')
        
        # Font size
        parts.append(f'fontsize={text_settings.font_size}')
        
        # Font color
        font_color = text_settings.font_color.lstrip('#')
        parts.append(f'fontcolor=0x{font_color}')
        
        # Position
        if task.original_resolution:
            video_width, video_height = task.original_resolution
        else:
            video_width, video_height = 1920, 1080
        
        x, y = text_settings.get_position_coords(video_width, video_height)
        parts.append(f'x={x}')
        parts.append(f'y={y}')
        
        # Outline
        if text_settings.outline_thickness > 0:
            border_color = text_settings.outline_color.lstrip('#')
            parts.append(f'bordercolor=0x{border_color}')
            parts.append(f'borderw={text_settings.outline_thickness}')
        
        # Background box
        if text_settings.box_enabled:
            parts.append('box=1')
            bg_color = text_settings.box_color.lstrip('#')
            parts.append(f'boxcolor=0x{bg_color}@{text_settings.box_opacity}')
        
        return 'drawtext=' + ':'.join(parts)
    
    @staticmethod
    def _build_with_overlay(task: VideoTask) -> List[str]:
        """
        Build FFmpeg command with overlay support (image or video).
        
        Supports:
        - Image overlay: static image with position, scale, opacity
        - Video overlay: video clip with timing, loop, position, scale, opacity
        
        Args:
            task: VideoTask with overlay parameters
            
        Returns:
            List of command arguments
        """
        # Check what overlays are enabled
        has_image = task.image_overlay and task.image_overlay.get('enabled')
        has_video = task.video_overlay and task.video_overlay.get('enabled')
        
        if not has_image and not has_video:
            return FFmpegCommandBuilder._build_standard(task)
        
        # Validate overlay files
        if has_image:
            image_path = task.image_overlay.get('file_path')
            if not image_path or not Path(image_path).exists():
                print(f"Warning: Image overlay file not found: {image_path}")
                has_image = False
        
        if has_video:
            video_path = task.video_overlay.get('file_path')
            if not video_path or not Path(video_path).exists():
                print(f"Warning: Video overlay file not found: {video_path}")
                has_video = False
        
        if not has_image and not has_video:
            return FFmpegCommandBuilder._build_standard(task)
        
        
        # Build command manually (not using ffmpeg-python for filter_complex)
        cmd = ['ffmpeg']
        
        # Input 0: Main video with trim
        if task.trim_start is not None:
            cmd.extend(['-ss', str(task.trim_start)])
        if task.trim_end is not None:
            cmd.extend(['-to', str(task.trim_end)])
        
        if task.codec.is_gpu:
            cmd.extend(['-hwaccel', 'cuda'])
        
        cmd.extend(['-i', str(task.input_path)])
        
        # Track input indices
        input_idx = 1
        image_input_idx = None
        video_input_idx = None
        
        # Input 1 (optional): Image overlay
        if has_image:
            image_input_idx = input_idx
            cmd.extend(['-i', str(task.image_overlay.get('file_path'))])
            input_idx += 1
        
        # Input 2 (optional): Video overlay
        if has_video:
            video_input_idx = input_idx
            video_settings = task.video_overlay
            
            # Add loop option if enabled
            if video_settings.get('loop', False):
                cmd.extend(['-stream_loop', '-1'])
            
            cmd.extend(['-i', str(task.video_overlay.get('file_path'))])
            input_idx += 1
        
        # Build filter_complex
        filters = []
        video_stream = '[0:v]'
        
        # Apply video processing to main stream
        if task.scale:
            width, height = task.scale
            if task.codec.is_gpu:
                filters.append(f'{video_stream}scale_cuda={width}:{height}[scaled]')
            else:
                filters.append(f'{video_stream}scale={width}:{height}[scaled]')
            video_stream = '[scaled]'
        
        if task.crop:
            x, y, width, height = task.crop
            filters.append(f'{video_stream}crop={width}:{height}:{x}:{y}[cropped]')
            video_stream = '[cropped]'
        
        if task.speed != 1.0:
            pts_multiplier = 1.0 / task.speed
            filters.append(f'{video_stream}setpts={pts_multiplier}*PTS[sped]')
            video_stream = '[sped]'
        
        
        # Process overlay(s)
        # We'll apply overlays sequentially: first image, then video
        
        # Process image overlay if enabled
        if has_image:
            overlay_stream = f'[{image_input_idx}:v]'
            settings = task.image_overlay
            
            # Scale overlay if specified
            scale_w = settings.get('scale_width')
            scale_h = settings.get('scale_height')
            if scale_w or scale_h:
                w = scale_w if scale_w else -1
                h = scale_h if scale_h else -1
                filters.append(f'{overlay_stream}scale={w}:{h}[img_scaled]')
                overlay_stream = '[img_scaled]'
            
            # Apply opacity
            opacity = settings.get('opacity', 1.0)
            if opacity < 1.0:
                filters.append(f'{overlay_stream}format=yuva420p,colorchannelmixer=aa={opacity}[img_alpha]')
                overlay_stream = '[img_alpha]'
            
            # Calculate position
            position = settings.get('position', OverlayPosition.TOP_RIGHT)
            if position == OverlayPosition.CUSTOM:
                x = settings.get('custom_x', 10)
                y = settings.get('custom_y', 10)
            elif position == OverlayPosition.TOP_LEFT:
                x, y = 10, 10
            elif position == OverlayPosition.TOP_RIGHT:
                x, y = 'W-w-10', 10
            elif position == OverlayPosition.BOTTOM_LEFT:
                x, y = 10, 'H-h-10'
            elif position == OverlayPosition.BOTTOM_RIGHT:
                x, y = 'W-w-10', 'H-h-10'
            elif position == OverlayPosition.CENTER:
                x, y = '(W-w)/2', '(H-h)/2'
            else:
                x, y = 10, 10
            
            # Apply image overlay
            filters.append(f'{video_stream}{overlay_stream}overlay={x}:{y}[img_out]')
            video_stream = '[img_out]'
        
        # Process video overlay if enabled
        if has_video:
            overlay_stream = f'[{video_input_idx}:v]'
            settings = task.video_overlay
            
            # Scale overlay if specified
            scale_w = settings.get('scale_width')
            scale_h = settings.get('scale_height')
            if scale_w or scale_h:
                w = scale_w if scale_w else -1
                h = scale_h if scale_h else -1
                filters.append(f'{overlay_stream}scale={w}:{h}[vid_scaled]')
                overlay_stream = '[vid_scaled]'
            
            # Apply opacity
            opacity = settings.get('opacity', 1.0)
            if opacity < 1.0:
                filters.append(f'{overlay_stream}format=yuva420p,colorchannelmixer=aa={opacity}[vid_alpha]')
                overlay_stream = '[vid_alpha]'
            
            # Calculate position
            position = settings.get('position', OverlayPosition.TOP_RIGHT)
            if position == OverlayPosition.CUSTOM:
                x = settings.get('custom_x', 10)
                y = settings.get('custom_y', 10)
            elif position == OverlayPosition.TOP_LEFT:
                x, y = 10, 10
            elif position == OverlayPosition.TOP_RIGHT:
                x, y = 'W-w-10', 10
            elif position == OverlayPosition.BOTTOM_LEFT:
                x, y = 10, 'H-h-10'
            elif position == OverlayPosition.BOTTOM_RIGHT:
                x, y = 'W-w-10', 'H-h-10'
            elif position == OverlayPosition.CENTER:
                x, y = '(W-w)/2', '(H-h)/2'
            else:
                x, y = 10, 10
            
            # Build overlay filter with timing if specified
            start_time = settings.get('start_time', 0)
            duration = settings.get('duration')
            
            if start_time > 0 or duration:
                # Use enable filter for timing control
                if duration:
                    end_time = start_time + duration
                    enable_expr = f"'between(t,{start_time},{end_time})'"
                else:
                    enable_expr = f"'gte(t,{start_time})'"
                
                filters.append(f'{video_stream}{overlay_stream}overlay={x}:{y}:enable={enable_expr}[vid_out]')
            else:
                # No timing, overlay for entire duration
                filters.append(f'{video_stream}{overlay_stream}overlay={x}:{y}[vid_out]')
            
            video_stream = '[vid_out]'
        
        # Add text overlay if needed
        if task.text_settings and task.text_settings.is_active():
            drawtext = FFmpegCommandBuilder._build_drawtext_filter(task.text_settings, task)
            if drawtext:
                # Extract just the filter part (remove 'drawtext=')
                drawtext_params = drawtext.replace('drawtext=', '')
                filters.append(f'{video_stream}drawtext={drawtext_params}[final]')
                video_stream = '[final]'
        
        # Combine filters
        filter_complex = ';'.join(filters)
        cmd.extend(['-filter_complex', filter_complex])
        
        # Map video stream
        cmd.extend(['-map', video_stream])
        
        # Audio processing
        audio_filters = FFmpegCommandBuilder._build_audio_filter_string(task)
        if audio_filters:
            cmd.extend(['-af', audio_filters])
            cmd.extend(['-map', '0:a', '-acodec', 'aac', '-b:a', '192k'])
        else:
            cmd.extend(['-map', '0:a', '-acodec', 'copy'])
        
        # Video codec and quality
        cmd.extend(['-vcodec', task.codec.value])
        
        if task.quality_mode == QualityMode.CRF:
            if task.codec.is_gpu:
                cmd.extend(['-cq', str(task.crf)])
            else:
                cmd.extend(['-crf', str(task.crf)])
        else:
            cmd.extend(['-b:v', task.bitrate])
        
        cmd.extend(['-preset', task.preset.value])
        
        # Progress and output
        cmd.extend(['-progress', 'pipe:1', '-y', str(task.output_path)])
        
        # DEBUG
        print("\n" + "="*80)
        print("FFmpeg Command (with image overlay):")
        print("="*80)
        print(' '.join(cmd))
        print("="*80 + "\n")
        
        return cmd
    
    @staticmethod
    def validate_task(task: VideoTask) -> tuple[bool, str]:
        """
        Validate task parameters before building command.
        
        Args:
            task: VideoTask to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not task.input_path.exists():
            return False, f"Input file not found: {task.input_path}"
        
        if not task.output_path.parent.exists():
            return False, f"Output directory not found: {task.output_path.parent}"
        
        if task.watermark_type == WatermarkType.IMAGE:
            if not task.watermark_image or not task.watermark_image.exists():
                return False, "Watermark image not found"
        
        if task.subtitle_file and not task.subtitle_file.exists():
            return False, f"Subtitle file not found: {task.subtitle_file}"
        
        if not (0.5 <= task.speed <= 2.0):
            return False, f"Speed must be between 0.5 and 2.0, got {task.speed}"
        
        if not (0.0 <= task.volume <= 2.0):
            return False, f"Volume must be between 0.0 and 2.0, got {task.volume}"
        
        if task.quality_mode == QualityMode.CRF:
            if not (0 <= task.crf <= 51):
                return False, f"CRF must be between 0 and 51, got {task.crf}"
        
        if task.text_settings and task.text_settings.is_active():
            if task.text_settings.font_path and not task.text_settings.font_path.exists():
                return False, f"Font file not found: {task.text_settings.font_path}"
        
        # Validate overlay files
        if task.image_overlay and task.image_overlay.get('enabled'):
            img_path = task.image_overlay.get('file_path')
            if img_path and not Path(img_path).exists():
                return False, f"Image overlay file not found: {img_path}"
        
        return True, ""
