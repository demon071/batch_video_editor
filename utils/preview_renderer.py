"""
Preview Renderer for Multi-Layer Overlay System.

Extracts frames from video and composites layers using QPainter for preview.
"""
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QImage
from PyQt5.QtCore import Qt, QRect
from models.layer import Layer, LayerType, TextLayerProperties, ImageLayerProperties, VideoLayerProperties


class PreviewRenderer:
    """
    Renders preview frames with layers composited.
    
    Uses FFmpeg to extract frames and QPainter to composite layers.
    """
    
    def __init__(self):
        """Initialize preview renderer."""
        self.frame_cache = {}  # Cache extracted frames
        
    def extract_frame(self, video_path: Path, timestamp: float) -> Optional[QPixmap]:
        """
        Extract a single frame from video at specified timestamp.
        
        Args:
            video_path: Path to video file
            timestamp: Time in seconds
            
        Returns:
            QPixmap of the frame or None if extraction failed
        """
        # Check cache first
        cache_key = f"{video_path}_{timestamp}"
        if cache_key in self.frame_cache:
            return self.frame_cache[cache_key]
        
        # Create temporary file for frame
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # FFmpeg command to extract frame
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', str(video_path),
                '-frames:v', '1',
                '-y',
                tmp_path
            ]
            
            # Run FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                return None
            
            # Load frame as QPixmap
            pixmap = QPixmap(tmp_path)
            
            # Cache the frame
            self.frame_cache[cache_key] = pixmap
            
            return pixmap
            
        except Exception as e:
            print(f"Error extracting frame: {e}")
            return None
            
        finally:
            # Clean up temp file
            try:
                Path(tmp_path).unlink()
            except:
                pass
    
    def render_preview(
        self, 
        video_path: Path, 
        layers: List[Layer], 
        timestamp: float,
        max_width: int = 640,
        max_height: int = 480
    ) -> Optional[QPixmap]:
        """
        Render preview frame with all layers composited.
        
        Args:
            video_path: Path to main video
            layers: List of Layer objects to composite
            timestamp: Time in seconds for preview
            max_width: Maximum width for preview (for scaling)
            max_height: Maximum height for preview (for scaling)
            
        Returns:
            QPixmap with composited layers or None if failed
        """
        # Extract base frame
        base_frame = self.extract_frame(video_path, timestamp)
        if base_frame is None:
            return None
        
        # Scale frame to fit preview area while maintaining aspect ratio
        scaled_frame = base_frame.scaled(
            max_width, 
            max_height, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # Create a copy for painting
        result = QPixmap(scaled_frame)
        
        # Calculate scale factor for layer positions
        scale_x = scaled_frame.width() / base_frame.width()
        scale_y = scaled_frame.height() / base_frame.height()
        
        # Create painter
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Sort layers by z_index
        sorted_layers = sorted(layers, key=lambda l: l.z_index)
        
        # Render each layer
        for layer in sorted_layers:
            if not layer.enabled:
                continue
            
            # Check if layer is active at this timestamp
            if not self._is_layer_active(layer, timestamp):
                continue
            
            # Render based on layer type
            if layer.type == LayerType.TEXT:
                self._render_text_layer(painter, layer, scale_x, scale_y)
            elif layer.type == LayerType.IMAGE:
                self._render_image_layer(painter, layer, scale_x, scale_y)
            elif layer.type == LayerType.VIDEO:
                self._render_video_layer(painter, layer, timestamp, scale_x, scale_y)
        
        painter.end()
        
        return result
    
    def _is_layer_active(self, layer: Layer, timestamp: float) -> bool:
        """Check if layer should be visible at given timestamp."""
        if layer.start_time is not None and timestamp < layer.start_time:
            return False
        if layer.end_time is not None and timestamp > layer.end_time:
            return False
        return True
    
    def _render_text_layer(self, painter: QPainter, layer: Layer, scale_x: float, scale_y: float):
        """Render text layer on painter."""
        props = layer.properties
        
        # Get text properties
        text = props.get(TextLayerProperties.TEXT, "")
        font_size = props.get(TextLayerProperties.FONT_SIZE, 48)
        font_color = props.get(TextLayerProperties.FONT_COLOR, "#FFFFFF")
        border_width = props.get(TextLayerProperties.BORDER_WIDTH, 0)
        border_color = props.get(TextLayerProperties.BORDER_COLOR, "#000000")
        
        # Scale position
        x = int(layer.position[0] * scale_x)
        y = int(layer.position[1] * scale_y)
        
        # Scale font size
        scaled_font_size = int(font_size * min(scale_x, scale_y))
        
        # Set up font
        font = QFont()
        font.setPixelSize(scaled_font_size)
        painter.setFont(font)
        
        # Draw border/outline if specified
        if border_width > 0:
            pen = QPen(QColor(border_color))
            pen.setWidth(int(border_width * min(scale_x, scale_y)))
            painter.setPen(pen)
            painter.drawText(x, y, text)
        
        # Draw text
        painter.setPen(QColor(font_color))
        painter.drawText(x, y, text)
    
    def _render_image_layer(self, painter: QPainter, layer: Layer, scale_x: float, scale_y: float):
        """Render image layer on painter."""
        props = layer.properties
        
        # Get image path
        img_path = props.get(ImageLayerProperties.FILE_PATH)
        if not img_path or not Path(img_path).exists():
            return
        
        # Load image
        image = QPixmap(str(img_path))
        if image.isNull():
            return
        
        # Get scale properties
        scale_width = props.get(ImageLayerProperties.SCALE_WIDTH)
        scale_height = props.get(ImageLayerProperties.SCALE_HEIGHT)
        opacity = props.get(ImageLayerProperties.OPACITY, 1.0)
        
        # Scale image if specified
        if scale_width or scale_height:
            w = int(scale_width * scale_x) if scale_width else image.width()
            h = int(scale_height * scale_y) if scale_height else image.height()
            image = image.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Scale position
        x = int(layer.position[0] * scale_x)
        y = int(layer.position[1] * scale_y)
        
        # Set opacity
        painter.setOpacity(opacity)
        
        # Draw image
        painter.drawPixmap(x, y, image)
        
        # Reset opacity
        painter.setOpacity(1.0)
    
    def _render_video_layer(
        self, 
        painter: QPainter, 
        layer: Layer, 
        timestamp: float,
        scale_x: float, 
        scale_y: float
    ):
        """Render video layer on painter."""
        props = layer.properties
        
        # Get video path
        vid_path = props.get(VideoLayerProperties.FILE_PATH)
        if not vid_path or not Path(vid_path).exists():
            return
        
        # Calculate video timestamp (relative to layer start)
        vid_timestamp = timestamp
        if layer.start_time is not None:
            vid_timestamp = timestamp - layer.start_time
        
        # Extract frame from video overlay
        frame = self.extract_frame(Path(vid_path), vid_timestamp)
        if frame is None:
            return
        
        # Get scale properties
        scale_width = props.get(VideoLayerProperties.SCALE_WIDTH)
        scale_height = props.get(VideoLayerProperties.SCALE_HEIGHT)
        opacity = props.get(VideoLayerProperties.OPACITY, 1.0)
        
        # Scale frame if specified
        if scale_width or scale_height:
            w = int(scale_width * scale_x) if scale_width else frame.width()
            h = int(scale_height * scale_y) if scale_height else frame.height()
            frame = frame.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Scale position
        x = int(layer.position[0] * scale_x)
        y = int(layer.position[1] * scale_y)
        
        # Set opacity
        painter.setOpacity(opacity)
        
        # Draw frame
        painter.drawPixmap(x, y, frame)
        
        # Reset opacity
        painter.setOpacity(1.0)
    
    def render_task_preview(
        self,
        task,
        timestamp: float,
        max_width: int = 640,
        max_height: int = 480,
        base_image: Optional[QPixmap] = None
    ) -> Optional[QPixmap]:
        """
        Render preview for a specific video task.
        
        Args:
            task: VideoTask object
            timestamp: Time in seconds
            max_width: Maximum width
            max_height: Maximum height
            base_image: Optional base frame (if already extracted)
            
        Returns:
            QPixmap or None
        """
        if not task or not task.input_path.exists():
            return None
            
        # Use provided base image or extract one
        base_frame = base_image
        if base_frame is None:
            base_frame = self.extract_frame(task.input_path, timestamp)
            
        if base_frame is None:
            return None
            
        # Create painter for composition
        # Scale base frame first if needed (e.g. for performance)
        # For now, we'll work with the base frame resolution and scale at the end if needed
        # But to match render_preview signature, let's scale first to fit preview area
        
        scaled_frame = base_frame.scaled(
            max_width, 
            max_height, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        result = QPixmap(scaled_frame)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate scale factors relative to original video
        scale_x = scaled_frame.width() / base_frame.width()
        scale_y = scaled_frame.height() / base_frame.height()
        
        # Apply Crop (Simulated by drawing a rectangle or actually cropping?)
        # For true preview, we should probably crop the source image before scaling
        # But for simplicity in this overlay preview, we might just show the crop box
        # OR, actually crop. Let's try to actually crop if crop settings exist.
        
        crop = task.crop
        if crop:
            # If cropping is enabled, we should have cropped the base_frame BEFORE scaling
            # Let's redo the base frame handling
            painter.end() # End previous painter
            
            x, y, w, h = crop
            cropped_frame = base_frame.copy(x, y, w, h)
            
            scaled_frame = cropped_frame.scaled(
                max_width, 
                max_height, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            result = QPixmap(scaled_frame)
            painter = QPainter(result)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Recalculate scale factors based on cropped size
            scale_x = scaled_frame.width() / w
            scale_y = scaled_frame.height() / h
            
        # Apply Watermark
        from models.enums import WatermarkType
        
        # Check if watermark is enabled (handle both Enum and string "None")
        is_watermark_enabled = False
        if isinstance(task.watermark_type, WatermarkType):
            is_watermark_enabled = task.watermark_type != WatermarkType.NONE
        else:
            is_watermark_enabled = str(task.watermark_type) != "None"
            
        if is_watermark_enabled:
            
            # Text Watermark
            # Handle string comparison if needed
            is_text_type = task.watermark_type == WatermarkType.TEXT or str(task.watermark_type) == "WatermarkType.TEXT" or str(task.watermark_type) == "Text"
            
            if is_text_type and task.watermark_text:
                font = QFont()
                # Rough font size estimation
                font_size = 36 * min(scale_x, scale_y) 
                font.setPixelSize(int(font_size))
                painter.setFont(font)
                painter.setPen(QColor("white"))
                
                wx, wy = task.watermark_position
                painter.drawText(int(wx * scale_x), int(wy * scale_y), task.watermark_text)
                
            # Image Watermark
            elif task.watermark_type == WatermarkType.IMAGE and task.watermark_image:
                if task.watermark_image.exists():
                    wm_pixmap = QPixmap(str(task.watermark_image))
                    if not wm_pixmap.isNull():
                        # Scale watermark (e.g. 10% of width)
                        target_w = int(scaled_frame.width() * 0.15)
                        wm_scaled = wm_pixmap.scaledToWidth(target_w, Qt.SmoothTransformation)
                        
                        wx, wy = task.watermark_position
                        painter.drawPixmap(int(wx * scale_x), int(wy * scale_y), wm_scaled)

        # Apply Text Overlays
        # Convert task text settings to temporary layers or render directly
        if task.text_settings:
            # This would require parsing the text settings dict/object
            # For now, let's assume simple rendering if possible, or skip complex overlays
            pass
            
        painter.end()
        return result

    def clear_cache(self):
        """Clear frame cache to free memory."""
        self.frame_cache.clear()
