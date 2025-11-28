"""
Preview Player Widget - Center panel for video preview and playback.

Displays:
- Video preview (input or output)
- Live render preview during processing
- Playback controls
- Timeline scrubber
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSlider, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from pathlib import Path
from typing import Optional
import cv2

from models.video_task import VideoTask


class PreviewPlayerWidget(QWidget):
    """
    Preview player for video display and playback.
    
    Features:
    - Display input video preview
    - Display live render preview during processing
    - Timeline scrubber
    - Playback controls
    - Resolution/FPS display
    
    Signals:
        seek_requested: User wants to seek to a specific time
    """
    
    # Signals
    seek_requested = pyqtSignal(float)  # timestamp in seconds
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_task: Optional[VideoTask] = None
        self.current_pixmap: Optional[QPixmap] = None
        self.video_capture: Optional[cv2.VideoCapture] = None
        self.is_rendering = False
        
        # Initialize renderer
        from utils.preview_renderer import PreviewRenderer
        self.renderer = PreviewRenderer()
        
        self._init_ui()
        
    def refresh_preview(self):
        """Refresh current preview frame with latest settings."""
        if not self.current_task:
            return
            
        # Get current timestamp and frame
        timestamp = 0.0
        base_pixmap = None
        
        if self.video_capture:
            # Save current position
            current_pos = self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)
            timestamp = self.video_capture.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            
            # Read current frame
            ret, frame = self.video_capture.read()
            if ret:
                # Convert to QPixmap
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                
                from PyQt5.QtGui import QImage
                q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                base_pixmap = QPixmap.fromImage(q_image)
                
                # Restore position (so we don't advance when just tweaking settings)
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
            else:
                # If read failed, try to seek back just in case
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
            
        # Render frame with effects
        pixmap = self.renderer.render_task_preview(
            self.current_task,
            timestamp,
            self.preview_label.width(),
            self.preview_label.height(),
            base_image=base_pixmap
        )
        
        if pixmap:
            self.current_pixmap = pixmap
            self._display_pixmap(pixmap)

    def _show_frame_at_position(self, position: int):
        """Show frame at specific position (0-1000)."""
        if not self.video_capture or not self.current_task:
            print("DEBUG: _show_frame_at_position - Missing capture or task")
            return
        
        # Calculate frame number
        total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_number = int((position / 1000.0) * total_frames)
        
        print(f"DEBUG: _show_frame_at_position - Position: {position}, Frame: {frame_number}/{total_frames}")
        
        # Seek to frame
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Instead of reading raw frame, use renderer
        self.refresh_preview()
        

    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Info label (overlay or top corner)
        header_layout = QHBoxLayout()
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #888; font-size: 10px;")
        header_layout.addWidget(self.info_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Preview area
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(640, 360)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #444;
                border-radius: 4px;
            }
        """)
        self._show_placeholder()
        layout.addWidget(self.preview_label, 1)
        

    
    def set_task(self, task: Optional[VideoTask]):
        """Set the current task to preview."""
        self.current_task = task
        
        if task is None:
            self._show_placeholder()
            self._close_video()
            return
        
        # Update info
        if task.original_resolution:
            w, h = task.original_resolution
            self.info_label.setText(f"{w}x{h}")
        else:
            self.info_label.setText("")
        

        
        # Load video for preview
        self._load_video(task.input_path)
    
    def set_render_preview(self, pixmap: QPixmap, timestamp: float):
        """
        Set preview frame during rendering.
        
        Args:
            pixmap: Frame to display
            timestamp: Current timestamp in seconds
        """
        self.is_rendering = True
        self.current_pixmap = pixmap
        self._display_pixmap(pixmap)
        

    
    def clear_render_preview(self):
        """Clear render preview and return to input preview."""
        self.is_rendering = False
        if self.current_task:
            self._load_video(self.current_task.input_path)
        else:
            self._show_placeholder()
    
    def _load_video(self, video_path: Path):
        """Load video file for preview."""
        self._close_video()
        
        if not video_path.exists():
            self._show_placeholder("Video file not found")
            return
        
        try:
            self.video_capture = cv2.VideoCapture(str(video_path))
            
            if not self.video_capture.isOpened():
                self._show_placeholder("Failed to open video")
                self._close_video()
                return
            
            # Check if video has frames
            total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                self._show_placeholder("Video has no frames")
                self._close_video()
                return
            
            # Extract and show first frame
            self._show_frame_at_position(0)
            
        except Exception as e:
            print(f"Error loading video: {e}")
            self._show_placeholder(f"Error: {str(e)}")
            self._close_video()
    
    def _show_frame_at_position(self, position: int):
        """Show frame at specific position (0-1000)."""
        if not self.video_capture or not self.current_task:
            return
        
        # Calculate frame number
        total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_number = int((position / 1000.0) * total_frames)
        
        # Seek to frame
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Instead of reading raw frame, use renderer
        self.refresh_preview()
        

    
    def _display_pixmap(self, pixmap: QPixmap):
        """Display pixmap scaled to fit preview area."""
        if pixmap.isNull():
            return
        
        # Scale to fit while maintaining aspect ratio
        scaled = pixmap.scaled(
            self.preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled)
    
    def _show_placeholder(self, message: str = "No preview available"):
        """Show placeholder text."""
        self.preview_label.clear()
        self.preview_label.setText(message)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #444;
                border-radius: 4px;
                color: #666;
                font-size: 14px;
            }
        """)
    
    def _close_video(self):
        """Close video capture."""
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
    

    
    def resizeEvent(self, event):
        """Handle resize event."""
        super().resizeEvent(event)
        # Redisplay current pixmap at new size
        if self.current_pixmap:
            self._display_pixmap(self.current_pixmap)
