"""
FFmpeg preview builder using ffmpeg-python library.
Cloned from FFmpegPythonBuilder to generate preview images instead of video files.
"""
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import ffmpeg
from models.video_task import VideoTask
from models.text_settings import TextSettings
from models.enums import VideoCodec, QualityMode, OverlayPosition
from utils.font_utils import get_default_font


class PreviewBuilder:
    """
    Builds FFmpeg command for generating a preview frame.
    """
    
    @staticmethod
    def build_preview_command(task: VideoTask, timestamp: float) -> List[str]:
        """
        Build FFmpeg command to extract a preview frame at the given timestamp.
        
        Args:
            task: VideoTask with processing parameters
            timestamp: Time in seconds to extract frame from
            
        Returns:
            List of command arguments
        """
        # Check if we need complex filter graph (overlays)
        needs_overlay = PreviewBuilder._needs_overlay(task)
        
        if needs_overlay:
            return PreviewBuilder._build_with_overlay(task, timestamp)
        else:
            return PreviewBuilder._build_standard(task, timestamp)
    
    @staticmethod
    def _build_standard(task: VideoTask, timestamp: float) -> List[str]:
        """
        Build standard FFmpeg command for basic processing.
        """
        # Input options
        input_kwargs = {}
        
        # Optimization: For standard processing (no concat/overlays that shift time),
        # we can seek the input directly for faster performance.
        # However, we must account for trim_start.
        # If task has trim_start=10, and we want preview at T=5 (relative to trimmed video),
        # we need to seek to 10+5 = 15s in original video.
        
        seek_time = timestamp
        if task.trim_start is not None:
            seek_time += task.trim_start
            
        input_kwargs['ss'] = seek_time
            
        # Use GPU for input decoding if requested
        if task.use_gpu_decoding and task.codec.is_gpu:
            input_kwargs['hwaccel'] = 'cuda'
            
        # Input stream
        stream = ffmpeg.input(str(task.input_path), **input_kwargs)
        video_stream = stream.video
        # We don't need audio for image preview
        
        # Apply video filters
        video_stream = PreviewBuilder._apply_video_filters(video_stream, task)
        
        # Output options
        # Output to pipe as PNG
        out = ffmpeg.output(
            video_stream, 
            'pipe:', 
            format='image2pipe', 
            vcodec='png', 
            vframes=1
        )
        
        # Compile command
        cmd = ffmpeg.compile(out)
        
        return cmd

    @staticmethod
    def _needs_overlay(task: VideoTask) -> bool:
        """Check if task requires overlay processing."""
        return (
            (task.image_overlay and task.image_overlay.get('enabled', False)) or
            (task.video_overlay and task.video_overlay.get('enabled', False)) or
            (task.intro_video and task.intro_video.get('enabled', False)) or
            (task.outro_video and task.outro_video.get('enabled', False)) or
            (task.stack_settings and task.stack_settings.get('mode')) or
            (task.background_frame and task.background_frame.get('enabled', False))
        )

    @staticmethod
    def _build_with_overlay(task: VideoTask, timestamp: float) -> List[str]:
        """
        Build complex FFmpeg command handling Overlays, Intro/Outro, and Stacking.
        """
        # --- 1. Main Video Processing ---
        input_kwargs = {}
        if task.use_gpu_decoding and task.codec.is_gpu:
            input_kwargs['hwaccel'] = 'cuda'
        
        if task.trim_start is not None:
            input_kwargs['ss'] = task.trim_start
            
        # Handle trim end
        if task.cut_from_end is not None and task.duration > 0:
            input_kwargs['to'] = max(0, task.duration - task.cut_from_end)
        elif task.trim_end is not None:
            input_kwargs['to'] = task.trim_end
            
        main_input = ffmpeg.input(str(task.input_path), **input_kwargs)
        video_stream = main_input.video
        
        # --- Background Frame Processing ---
        background_layer = None
        if task.background_frame and task.background_frame.get('enabled'):
            bg_settings = task.background_frame
            target_width, target_height = bg_settings['resolution']
            bg_type = bg_settings['background_type']
            
            # For preview, we don't strictly need exact duration, but it helps
            bg_duration = 10000 # Arbitrary long duration for preview
            
            if bg_type == 'color':
                bg_color = bg_settings.get('background_color', '#000000')
                if bg_color.startswith('#'):
                    bg_color = '0x' + bg_color.lstrip('#')
                background_layer = ffmpeg.input(
                    f'color=c={bg_color}:s={target_width}x{target_height}:d={bg_duration}',
                    f='lavfi'
                ).video
            elif bg_type == 'image':
                bg_path = bg_settings.get('background_path')
                if bg_path and Path(bg_path).exists():
                    bg_img = ffmpeg.input(str(bg_path), loop=1, t=bg_duration)
                    bg_scaled = bg_img.video.filter('scale', target_width, target_height, force_original_aspect_ratio='increase')
                    background_layer = bg_scaled.filter('crop', target_width, target_height, '(iw-ow)/2', '(ih-oh)/2')
            elif bg_type == 'video':
                bg_path = bg_settings.get('background_path')
                if bg_path and Path(bg_path).exists():
                    bg_vid = ffmpeg.input(str(bg_path), stream_loop=-1)
                    bg_scaled = bg_vid.video.filter('scale', target_width, target_height, force_original_aspect_ratio='increase')
                    background_layer = bg_scaled.filter('crop', target_width, target_height, '(iw-ow)/2', '(ih-oh)/2')
            
            if background_layer:
                if task.original_resolution:
                    video_w, video_h = task.original_resolution
                else:
                    video_w, video_h = 1920, 1080
                
                video_aspect = video_w / video_h if video_h > 0 else 1.0
                bg_aspect = target_width / target_height if target_height > 0 else 1.0
                
                if video_aspect < 1.0 and bg_aspect > 1.0:
                    video_stream = video_stream.filter('scale', -1, target_height)
                elif video_aspect > 1.0 and bg_aspect < 1.0:
                    video_stream = video_stream.filter('scale', target_width, -1)
                else:
                    video_stream = video_stream.filter('scale', target_width, target_height, force_original_aspect_ratio='decrease')
                
                video_stream = ffmpeg.overlay(background_layer, video_stream, x='(W-w)/2', y='(H-h)/2', shortest=1)
        
        # Apply filters
        if not (task.background_frame and task.background_frame.get('enabled')):
            video_stream = PreviewBuilder._apply_video_filters(video_stream, task, skip_text=False)
        else:
            if task.text_settings and task.text_settings.is_active():
                drawtext_args = PreviewBuilder._get_drawtext_args(task.text_settings, task)
                if drawtext_args:
                    video_stream = video_stream.filter('drawtext', **drawtext_args)
            if task.subtitle_file:
                sub_path = str(task.subtitle_file).replace('\\', '/').replace(':', '\\:')
                video_stream = video_stream.filter('subtitles', sub_path)
        
        # Apply Overlays
        if task.image_overlay and task.image_overlay.get('enabled'):
            img_path = task.image_overlay.get('file_path')
            if img_path and Path(img_path).exists():
                img_input = ffmpeg.input(str(img_path))
                img_stream = img_input.video
                img_stream = PreviewBuilder._process_overlay_stream(img_stream, task.image_overlay)
                x, y = PreviewBuilder._get_overlay_position(task.image_overlay)
                video_stream = ffmpeg.overlay(video_stream, img_stream, x=x, y=y)
        
        if task.video_overlay and task.video_overlay.get('enabled'):
            vid_path = task.video_overlay.get('file_path')
            if vid_path and Path(vid_path).exists():
                vid_kwargs = {}
                if task.video_overlay.get('loop'):
                    vid_kwargs['stream_loop'] = -1
                vid_input = ffmpeg.input(str(vid_path), **vid_kwargs)
                vid_stream = vid_input.video
                vid_stream = PreviewBuilder._process_overlay_stream(vid_stream, task.video_overlay)
                x, y = PreviewBuilder._get_overlay_position(task.video_overlay)
                enable_expr = PreviewBuilder._get_enable_expression(task.video_overlay)
                
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
                
                target_w, target_h = task.scale if task.scale else (task.original_resolution if task.original_resolution else (1920, 1080))
                intro_v = intro_v.filter('scale', target_w, target_h)
                intro_v = intro_v.filter('setsar', 1)
                
                fade_dur = task.intro_video.get('fade_duration', 0)
                if fade_dur > 0:
                    intro_v = intro_v.filter('fade', type='in', start_time=0, duration=fade_dur)
                
                intro_streams = (intro_v, None) # No audio for preview

        # --- 3. Outro Processing ---
        outro_streams = None
        if task.outro_video and task.outro_video.get('enabled'):
            outro_path = task.outro_video.get('file_path')
            if outro_path and Path(outro_path).exists():
                outro_input = ffmpeg.input(str(outro_path))
                outro_v = outro_input.video
                
                target_w, target_h = task.scale if task.scale else (task.original_resolution if task.original_resolution else (1920, 1080))
                outro_v = outro_v.filter('scale', target_w, target_h)
                outro_v = outro_v.filter('setsar', 1)
                
                fade_dur = task.outro_video.get('fade_duration', 0)
                if fade_dur > 0:
                     outro_v = outro_v.filter('fade', type='in', start_time=0, duration=fade_dur)
                
                outro_streams = (outro_v, None)

        # --- 4. Concatenation ---
        concat_inputs = []
        if intro_streams:
            concat_inputs.append(intro_streams[0])
        concat_inputs.append(video_stream)
        if outro_streams:
            concat_inputs.append(outro_streams[0])
            
        if intro_streams or outro_streams:
            # Concat video only (v=1, a=0)
            joined = ffmpeg.concat(*concat_inputs, v=1, a=0)
            video_stream = joined.node[0]

        # --- 5. Stacking ---
        if task.stack_settings and task.stack_settings.get('mode'):
            stack_mode = task.stack_settings.get('mode')
            stack_type = task.stack_settings.get('type')
            stack_path = task.stack_settings.get('path')
            
            stack_stream = None
            if stack_type == 'file' and stack_path and Path(stack_path).exists():
                stack_input = ffmpeg.input(str(stack_path), stream_loop=-1)
                stack_stream = stack_input.video
            elif stack_type == 'folder' and stack_path and Path(stack_path).exists():
                 # Simplified for preview: just pick one random file or first file
                 # to avoid complex concat logic in preview
                 video_exts = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
                 files = [f for f in Path(stack_path).iterdir() if f.suffix.lower() in video_exts]
                 if files:
                     stack_input = ffmpeg.input(str(files[0]), stream_loop=-1)
                     stack_stream = stack_input.video
            
            if stack_stream:
                current_w, current_h = 1920, 1080
                if task.scale:
                    current_w, current_h = task.scale
                elif task.original_resolution:
                    current_w, current_h = task.original_resolution
                if task.crop:
                    _, _, cw, ch = task.crop
                    current_w, current_h = cw, ch
                
                if stack_mode == 'hstack':
                    stack_stream = stack_stream.filter('scale', -1, current_h)
                    video_stream = ffmpeg.hstack(video_stream, stack_stream)
                elif stack_mode == 'vstack':
                    stack_stream = stack_stream.filter('scale', current_w, -1)
                    video_stream = ffmpeg.vstack(video_stream, stack_stream)

        # --- 6. Output ---
        # Seek on output for accurate preview of complex filter graph
        out = ffmpeg.output(
            video_stream, 
            'pipe:', 
            format='image2pipe', 
            vcodec='png', 
            vframes=1,
            ss=timestamp
        )
        
        cmd = ffmpeg.compile(out)
        return cmd

    @staticmethod
    def _apply_video_filters(stream, task: VideoTask, skip_text: bool = False):
        """Apply standard video filters."""
        if task.scale:
            width, height = task.scale
            if task.codec.is_gpu:
                stream = stream.filter('scale_cuda', width, height)
            else:
                stream = stream.filter('scale', width, height)
        
        if task.crop:
            x, y, width, height = task.crop
            stream = stream.filter('crop', width, height, x, y)
        
        if task.speed != 1.0:
            pts_multiplier = 1.0 / task.speed
            stream = stream.filter('setpts', f'{pts_multiplier}*PTS')
            

            
        if not skip_text and task.text_settings and task.text_settings.is_active():
            drawtext_args = PreviewBuilder._get_drawtext_args(task.text_settings, task)
            if drawtext_args:
                stream = stream.filter('drawtext', **drawtext_args)
                
        if task.subtitle_file:
            sub_path = str(task.subtitle_file).replace('\\', '/').replace(':', '\\:')
            stream = stream.filter('subtitles', sub_path)
            
        return stream

    @staticmethod
    def _process_overlay_stream(stream, settings: dict):
        """Apply scaling and opacity to overlay stream."""
        scale_w = settings.get('scale_width')
        scale_h = settings.get('scale_height')
        if scale_w or scale_h:
            w = scale_w if scale_w else -1
            h = scale_h if scale_h else -1
            stream = stream.filter('scale', w, h)
            
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
        
        font_path = text_settings.font_path
        if not font_path or not font_path.exists():
            default_font = get_default_font()
            if default_font:
                font_path = Path(default_font)
        
        if font_path and font_path.exists():
            font_str = str(font_path).replace('\\', '/')
            if len(font_str) >= 2 and font_str[1] == ':':
                font_str = font_str[0] + '\\:' + font_str[2:]
            args['fontfile'] = font_str
            
        args['fontsize'] = text_settings.font_size
        args['fontcolor'] = f"0x{text_settings.font_color.lstrip('#')}"
        
        if task.original_resolution:
            vw, vh = task.original_resolution
        else:
            vw, vh = 1920, 1080
        x, y = text_settings.get_position_coords(vw, vh)
        args['x'] = x
        args['y'] = y
        
        if text_settings.outline_thickness > 0:
            args['bordercolor'] = f"0x{text_settings.outline_color.lstrip('#')}"
            args['borderw'] = text_settings.outline_thickness
            
        if text_settings.box_enabled:
            args['box'] = 1
            args['boxcolor'] = f"0x{text_settings.box_color.lstrip('#')}@{text_settings.box_opacity}"
            
        return args
