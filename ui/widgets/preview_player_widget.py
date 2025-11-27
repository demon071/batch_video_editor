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
        
        # Update time label
        fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        if fps > 0:
            timestamp = frame_number / fps
            self.time_current_label.setText(self._format_time(timestamp))
    
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
        
        # Timeline scrubber
        timeline_layout = QHBoxLayout()
        
        self.time_current_label = QLabel("0:00")
        self.time_current_label.setMinimumWidth(50)
        timeline_layout.addWidget(self.time_current_label)
        
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(1000)
        self.timeline_slider.setValue(0)
        self.timeline_slider.sliderReleased.connect(self._on_seek)
        timeline_layout.addWidget(self.timeline_slider)
        
        self.time_total_label = QLabel("0:00")
        self.time_total_label.setMinimumWidth(50)
        timeline_layout.addWidget(self.time_total_label)
        
        layout.addLayout(timeline_layout)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.addStretch()
        
        self.prev_frame_btn = QPushButton("◀◀")
        self.prev_frame_btn.setToolTip("Previous Frame")
        self.prev_frame_btn.setMaximumWidth(50)
        self.prev_frame_btn.clicked.connect(self._prev_frame)
        self.prev_frame_btn.setEnabled(False)
        controls_layout.addWidget(self.prev_frame_btn)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setToolTip("Play/Pause")
        self.play_btn.setMaximumWidth(50)
        self.play_btn.setEnabled(False)
        controls_layout.addWidget(self.play_btn)
        
        self.next_frame_btn = QPushButton("▶▶")
        self.next_frame_btn.setToolTip("Next Frame")
        self.next_frame_btn.setMaximumWidth(50)
        self.next_frame_btn.clicked.connect(self._next_frame)
        self.next_frame_btn.setEnabled(False)
        controls_layout.addWidget(self.next_frame_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
    
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
        
        # Update timeline
        if task.duration > 0:
            self.time_total_label.setText(self._format_time(task.duration))
            self.timeline_slider.setEnabled(True)
        else:
            self.time_total_label.setText("0:00")
            self.timeline_slider.setEnabled(False)
        
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
        
        # Update timeline
        self.time_current_label.setText(self._format_time(timestamp))
        if self.current_task and self.current_task.duration > 0:
            progress = int((timestamp / self.current_task.duration) * 1000)
            self.timeline_slider.setValue(progress)
    
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
            
            # Enable controls
            self.prev_frame_btn.setEnabled(True)
            self.next_frame_btn.setEnabled(True)
            
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
        
        # Update time label
        fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        if fps > 0:
            timestamp = frame_number / fps
            self.time_current_label.setText(self._format_time(timestamp))
    
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
    
    def _on_seek(self):
        """Handle timeline seek."""
        if not self.is_rendering:
            position = self.timeline_slider.value()
            self._show_frame_at_position(position)
    
    def _prev_frame(self):
        """Go to previous frame."""
        current = self.timeline_slider.value()
        self.timeline_slider.setValue(max(0, current - 10))
        self._on_seek()
    
    def _next_frame(self):
        """Go to next frame."""
        current = self.timeline_slider.value()
        self.timeline_slider.setValue(min(1000, current + 10))
        self._on_seek()
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def resizeEvent(self, event):
        """Handle resize event."""
        super().resizeEvent(event)
        # Redisplay current pixmap at new size
        if self.current_pixmap:
            self._display_pixmap(self.current_pixmap)
