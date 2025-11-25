"""
FFmpeg command builder using ffmpeg-python library.
This replaces the manual command builder with a more robust, fluent API implementation.
"""
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import ffmpeg
from models.video_task import VideoTask
from models.text_settings import TextSettings
from models.enums import VideoCodec, QualityMode, WatermarkType, OverlayPosition
from utils.font_utils import get_default_font


class FFmpegPythonBuilder:
    """
    Builds FFmpeg command using ffmpeg-python library.
    This handles proper escaping, stream mapping, and filter graph construction automatically.
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
        # Check if we need complex filter graph (overlays)
        needs_overlay = FFmpegPythonBuilder._needs_overlay(task)
        
        if needs_overlay:
            return FFmpegPythonBuilder._build_with_overlay(task)
        else:
            return FFmpegPythonBuilder._build_standard(task)
    
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
        Build standard FFmpeg command using ffmpeg-python.
        Used when no overlays are needed.
        """
        # Input options
        input_kwargs = {}
        if task.codec.is_gpu:
            input_kwargs['hwaccel'] = 'cuda'
        
        if task.trim_start is not None:
            input_kwargs['ss'] = task.trim_start
            
        # Handle trim end (absolute) or cut from end (relative)
        if task.cut_from_end is not None and task.duration > 0:
            # Calculate absolute end time
            input_kwargs['to'] = max(0, task.duration - task.cut_from_end)
        elif task.trim_end is not None:
            input_kwargs['to'] = task.trim_end
            
        # Create input stream
        stream = ffmpeg.input(str(task.input_path), **input_kwargs)
        
        # Split into video and audio streams
        video = stream.video
        audio = stream.audio
        
        # Apply video filters
        video = FFmpegPythonBuilder._apply_video_filters(video, task)
        
        # Apply audio filters
        audio = FFmpegPythonBuilder._apply_audio_filters(audio, task)
        
        # Output options
        output_kwargs = FFmpegPythonBuilder._get_output_kwargs(task)
        
        # Create output
        out = ffmpeg.output(video, audio, str(task.output_path), **output_kwargs)
        
        # Overwrite output
        out = ffmpeg.overwrite_output(out)
        
        # Compile command
        cmd = ffmpeg.compile(out)
        
        # DEBUG
        print("\n" + "="*80)
        print("FFmpeg Command (ffmpeg-python standard):")
        print("="*80)
        print(' '.join(cmd))
        print("="*80 + "\n")
        
        return cmd
    
    @staticmethod
    def _build_with_overlay(task: VideoTask) -> List[str]:
        """
        Build complex FFmpeg command handling Overlays and Intro/Outro.
        Pipeline:
        1. Process Main Video (Scale, Crop, Speed, Overlays, Text)
        2. Process Intro (Scale, Fade)
        3. Process Outro (Scale, Fade)
        4. Concat All
        """
        # --- 1. Main Video Processing ---
        input_kwargs = {}
        if task.codec.is_gpu:
            input_kwargs['hwaccel'] = 'cuda'
        
        if task.trim_start is not None:
            input_kwargs['ss'] = task.trim_start
            
        # Handle trim end (absolute) or cut from end (relative)
        if task.cut_from_end is not None and task.duration > 0:
            # Calculate absolute end time
            input_kwargs['to'] = max(0, task.duration - task.cut_from_end)
        elif task.trim_end is not None:
            input_kwargs['to'] = task.trim_end
            
        main_input = ffmpeg.input(str(task.input_path), **input_kwargs)
        video_stream = main_input.video
        audio_stream = main_input.audio
        
        # Apply basic video processing to main stream first
        # Note: We skip text overlay here to apply it BEFORE concat if possible, 
        # but usually text is on main video only. 
        # If we want text on intro/outro, we'd apply after concat.
        # Assuming text is for main video content only.
        video_stream = FFmpegPythonBuilder._apply_video_filters(video_stream, task, skip_text=False)
        audio_stream = FFmpegPythonBuilder._apply_audio_filters(audio_stream, task)
        
        # Apply Overlays (Image/Video) to Main Video
        if task.image_overlay and task.image_overlay.get('enabled'):
            img_path = task.image_overlay.get('file_path')
            if img_path and Path(img_path).exists():
                img_input = ffmpeg.input(str(img_path))
                img_stream = img_input.video
                img_stream = FFmpegPythonBuilder._process_overlay_stream(img_stream, task.image_overlay)
                x, y = FFmpegPythonBuilder._get_overlay_position(task.image_overlay)
                video_stream = ffmpeg.overlay(video_stream, img_stream, x=x, y=y)
        
        if task.video_overlay and task.video_overlay.get('enabled'):
            vid_path = task.video_overlay.get('file_path')
            if vid_path and Path(vid_path).exists():
                vid_kwargs = {}
                if task.video_overlay.get('loop'):
                    vid_kwargs['stream_loop'] = -1
                vid_input = ffmpeg.input(str(vid_path), **vid_kwargs)
                vid_stream = vid_input.video
                vid_stream = FFmpegPythonBuilder._process_overlay_stream(vid_stream, task.video_overlay)
                x, y = FFmpegPythonBuilder._get_overlay_position(task.video_overlay)
                enable_expr = FFmpegPythonBuilder._get_enable_expression(task.video_overlay)
                
                # If loop is enabled, the overlay stream is infinite.
                # We must set shortest=1 to ensure output ends when Main Video ends.
                overlay_kwargs = {'x': x, 'y': y}
                if enable_expr:
                    overlay_kwargs['enable'] = enable_expr
                if task.video_overlay.get('loop'):
                    overlay_kwargs['shortest'] = 1
                    
                video_stream = ffmpeg.overlay(video_stream, vid_stream, **overlay_kwargs)

        # --- 2. Intro Processing ---
        intro_streams = None
        if task.intro_video and task.intro_video.get('enabled'):
            intro_path = task.intro_video.get('file_path')
            if intro_path and Path(intro_path).exists():
                intro_input = ffmpeg.input(str(intro_path))
                intro_v = intro_input.video
                intro_a = intro_input.audio
                
                # Scale Intro to match Main Video
                # Determine target resolution
                # If task.scale is set, use it.
                # If not, use original_resolution (from Main Video).
                # Fallback to 1920x1080 if unknown.
                target_w, target_h = task.scale if task.scale else (task.original_resolution if task.original_resolution else (1920, 1080))
                
                # Force scale Intro to target resolution
                intro_v = intro_v.filter('scale', target_w, target_h)
                # Force SAR to 1:1 to avoid mismatch
                intro_v = intro_v.filter('setsar', 1)
                
                # Fade Out
                fade_dur = task.intro_video.get('fade_duration', 0)
                if fade_dur > 0:
                    intro_v = intro_v.filter('fade', type='in', start_time=0, duration=fade_dur)
                    intro_a = intro_a.filter('afade', type='in', start_time=0, duration=fade_dur)
                
                intro_streams = (intro_v, intro_a)

        # --- 3. Outro Processing ---
        outro_streams = None
        if task.outro_video and task.outro_video.get('enabled'):
            outro_path = task.outro_video.get('file_path')
            if outro_path and Path(outro_path).exists():
                outro_input = ffmpeg.input(str(outro_path))
                outro_v = outro_input.video
                outro_a = outro_input.audio
                
                # Determine target resolution
                target_w, target_h = task.scale if task.scale else (task.original_resolution if task.original_resolution else (1920, 1080))
                
                # Force scale Outro to target resolution
                outro_v = outro_v.filter('scale', target_w, target_h)
                # Force SAR to 1:1
                outro_v = outro_v.filter('setsar', 1)
                
                # Fade Out (requires duration)
                # For now, let's just do Fade IN for Outro (transition from Main)
                fade_dur = task.outro_video.get('fade_duration', 0)
                if fade_dur > 0:
                     outro_v = outro_v.filter('fade', type='in', start_time=0, duration=fade_dur)
                     outro_a = outro_a.filter('afade', type='in', start_time=0, duration=fade_dur)
                
                outro_streams = (outro_v, outro_a)

        # --- 4. Concatenation ---
        # Prepare list of streams [v, a, v, a, ...]
        concat_inputs = []
        
        if intro_streams:
            concat_inputs.extend(intro_streams)
            
        concat_inputs.extend([video_stream, audio_stream])
        
        if outro_streams:
            concat_inputs.extend(outro_streams)
            
        # If we have intro or outro, we concat
        if intro_streams or outro_streams:
            # Number of segments
            n = 1 + (1 if intro_streams else 0) + (1 if outro_streams else 0)
            joined = ffmpeg.concat(*concat_inputs, v=1, a=1)
            video_stream = joined.node[0]
            audio_stream = joined.node[1]

        # --- 5. Output ---
        output_kwargs = FFmpegPythonBuilder._get_output_kwargs(task)
        
        # Force audio encoding for complex filtergraph
        # Streamcopy cannot be used with complex filters (concat, overlay)
        output_kwargs['acodec'] = 'aac'
        output_kwargs['audio_bitrate'] = '192k'
        
        out = ffmpeg.output(video_stream, audio_stream, str(task.output_path), **output_kwargs)
        out = ffmpeg.overwrite_output(out)
        
        cmd = ffmpeg.compile(out)
        
        # DEBUG
        print("\n" + "="*80)
        print("FFmpeg Command (ffmpeg-python complex):")
        print("="*80)
        print(' '.join(cmd))
        print("="*80 + "\n")
        
        return cmd

    @staticmethod
    def _apply_video_filters(stream, task: VideoTask, skip_text: bool = False):
        """Apply standard video filters (scale, crop, speed, etc)."""
        # Scale
        if task.scale:
            width, height = task.scale
            if task.codec.is_gpu:
                stream = stream.filter('scale_cuda', width, height)
            else:
                stream = stream.filter('scale', width, height)
        
        # Crop
        if task.crop:
            x, y, width, height = task.crop
            stream = stream.filter('crop', width, height, x, y)
        
        # Speed
        if task.speed != 1.0:
            pts_multiplier = 1.0 / task.speed
            stream = stream.filter('setpts', f'{pts_multiplier}*PTS')
            
        # Watermark (simple text)
        if task.watermark_type == WatermarkType.TEXT and task.watermark_text:
            x, y = task.watermark_position
            txt = task.watermark_text
            # Simple drawtext for watermark
            # Note: We use basic settings for watermark as per original implementation
            stream = stream.filter('drawtext', text=txt, x=x, y=y, fontsize=24, fontcolor='white', borderw=2, bordercolor='black')
            
        # Text Overlay (if not skipped)
        if not skip_text and task.text_settings and task.text_settings.is_active():
            drawtext_args = FFmpegPythonBuilder._get_drawtext_args(task.text_settings, task)
            if drawtext_args:
                stream = stream.filter('drawtext', **drawtext_args)
                
        # Subtitles
        if task.subtitle_file:
            # Escape path for filter
            sub_path = str(task.subtitle_file).replace('\\', '/').replace(':', '\\:')
            stream = stream.filter('subtitles', sub_path)
            
        return stream

    @staticmethod
    def _apply_audio_filters(stream, task: VideoTask):
        """Apply audio filters (volume, speed)."""
        # Volume
        if task.volume != 1.0:
            stream = stream.filter('volume', task.volume)
            
        # Speed
        if task.speed != 1.0:
            speed = task.speed
            while speed > 2.0:
                stream = stream.filter('atempo', 2.0)
                speed /= 2.0
            while speed < 0.5:
                stream = stream.filter('atempo', 0.5)
                speed /= 0.5
            if speed != 1.0:
                stream = stream.filter('atempo', speed)
                
        return stream

    @staticmethod
    def _process_overlay_stream(stream, settings: dict):
        """Apply scaling and opacity to overlay stream."""
        # Scale
        scale_w = settings.get('scale_width')
        scale_h = settings.get('scale_height')
        if scale_w or scale_h:
            w = scale_w if scale_w else -1
            h = scale_h if scale_h else -1
            stream = stream.filter('scale', w, h)
            
        # Opacity
        opacity = settings.get('opacity', 1.0)
        if opacity < 1.0:
            stream = stream.filter('format', 'yuva420p')
            stream = stream.filter('colorchannelmixer', aa=opacity)
            
        return stream

    @staticmethod
    def _get_overlay_position(settings: dict) -> Tuple[str, str]:
        """Calculate overlay position expression."""
        position = settings.get('position', OverlayPosition.TOP_RIGHT)
        
        if position == OverlayPosition.CUSTOM:
            x = str(settings.get('custom_x', 10))
            y = str(settings.get('custom_y', 10))
        elif position == OverlayPosition.TOP_LEFT:
            x, y = '10', '10'
        elif position == OverlayPosition.TOP_RIGHT:
            x, y = 'W-w-10', '10'
        elif position == OverlayPosition.BOTTOM_LEFT:
            x, y = '10', 'H-h-10'
        elif position == OverlayPosition.BOTTOM_RIGHT:
            x, y = 'W-w-10', 'H-h-10'
        elif position == OverlayPosition.CENTER:
            x, y = '(W-w)/2', '(H-h)/2'
        else:
            x, y = '10', '10'
            
        return x, y

    @staticmethod
    def _get_enable_expression(settings: dict) -> Optional[str]:
        """Get enable expression for timing."""
        start_time = settings.get('start_time', 0)
        duration = settings.get('duration')
        
        if start_time > 0 or duration:
            if duration:
                end_time = start_time + duration
                return f"between(t,{start_time},{end_time})"
            else:
                return f"gte(t,{start_time})"
        return None

    @staticmethod
    def _get_drawtext_args(text_settings: TextSettings, task: VideoTask) -> Optional[Dict[str, Any]]:
        """Get arguments for drawtext filter."""
        if not text_settings.text.strip():
            return None
            
        args = {}
        args['text'] = text_settings.text
        
        # Font
        font_path = text_settings.font_path
        if not font_path or not font_path.exists():
            default_font = get_default_font()
            if default_font:
                font_path = Path(default_font)
        
        if font_path and font_path.exists():
            # ffmpeg-python handles escaping, we just pass the path string
            # BUT we still need to handle the Windows drive letter colon issue if ffmpeg-python doesn't
            # Let's try passing it clean first, usually libraries handle this
            # Actually, for filter args, manual escaping might still be needed for special chars
            # Let's use the safe escaping we found works: forward slashes + escaped colon
            font_str = str(font_path).replace('\\', '/')
            if len(font_str) >= 2 and font_str[1] == ':':
                font_str = font_str[0] + '\\:' + font_str[2:]
            args['fontfile'] = font_str
            
        args['fontsize'] = text_settings.font_size
        args['fontcolor'] = f"0x{text_settings.font_color.lstrip('#')}"
        
        # Position
        if task.original_resolution:
            vw, vh = task.original_resolution
        else:
            vw, vh = 1920, 1080
        x, y = text_settings.get_position_coords(vw, vh)
        args['x'] = x
        args['y'] = y
        
        # Outline
        if text_settings.outline_thickness > 0:
            args['bordercolor'] = f"0x{text_settings.outline_color.lstrip('#')}"
            args['borderw'] = text_settings.outline_thickness
            
        # Box
        if text_settings.box_enabled:
            args['box'] = 1
            args['boxcolor'] = f"0x{text_settings.box_color.lstrip('#')}@{text_settings.box_opacity}"
            
        return args

    @staticmethod
    def _get_output_kwargs(task: VideoTask) -> Dict[str, Any]:
        """Get output arguments."""
        kwargs = {}
        
        # Video codec
        kwargs['vcodec'] = task.codec.value
        
        # Quality
        if task.quality_mode == QualityMode.CRF:
            if task.codec.is_gpu:
                kwargs['cq'] = task.crf
            else:
                kwargs['crf'] = task.crf
        else:
            kwargs['video_bitrate'] = task.bitrate
            
        # Preset
        kwargs['preset'] = task.preset.value
        
        # Audio codec
        if task.volume != 1.0 or task.speed != 1.0:
            kwargs['acodec'] = 'aac'
            kwargs['audio_bitrate'] = '192k'
        else:
            kwargs['acodec'] = 'copy'
            
        # Progress
        kwargs['progress'] = 'pipe:1'
        
        return kwargs
    
    @staticmethod
    def validate_task(task: VideoTask) -> Tuple[bool, str]:
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
                
        if task.video_overlay and task.video_overlay.get('enabled'):
            vid_path = task.video_overlay.get('file_path')
            if vid_path and not Path(vid_path).exists():
                return False, f"Video overlay file not found: {vid_path}"
        
        if task.intro_video and task.intro_video.get('enabled'):
            intro_path = task.intro_video.get('file_path')
            if intro_path and not Path(intro_path).exists():
                return False, f"Intro video file not found: {intro_path}"
                
        if task.outro_video and task.outro_video.get('enabled'):
            outro_path = task.outro_video.get('file_path')
            if outro_path and not Path(outro_path).exists():
                return False, f"Outro video file not found: {outro_path}"
        
        return True, ""
