"""
Preview Player Widget - Center panel for video preview and playback.

Displays:
- Video preview (input or output)
- Live render preview during processing
- Playback controls
- Timeline scrubber
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSlider, QSizePolicy, QStyle)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QImage, QIcon
from pathlib import Path
from typing import Optional
import subprocess
import sys

from models.video_task import VideoTask
from utils.system_check import format_duration


class PreviewPlayerWidget(QWidget):
    """
    Preview player for video display and playback.
    
    Features:
    - Display input video preview using FFmpeg
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
        self.is_rendering = False
        self.current_timestamp = 0.0
        self.is_scrubbing = False
        
        self._init_ui()
        
    def refresh_preview(self):
        """Refresh current preview frame with latest settings."""
        if not self.current_task:
            return
            
        # Cancel existing worker if running
        if hasattr(self, 'preview_worker') and self.preview_worker and self.preview_worker.isRunning():
            self.preview_worker.cancel()
            
        # Start new worker
        from ui.workers.preview_worker import PreviewWorker
        self.preview_worker = PreviewWorker(self.current_task, self.current_timestamp)
        self.preview_worker.preview_ready.connect(self._on_preview_ready)
        self.preview_worker.error_occurred.connect(self._on_preview_error)
        self.preview_worker.start()
        
    def _on_preview_ready(self, pixmap: QPixmap):
        """Handle ready preview."""
        self.current_pixmap = pixmap
        self._display_pixmap(pixmap)
        
    def _on_preview_error(self, error: str):
        """Handle preview error."""
        # print(f"Preview error: {error}")
        pass
        
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
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
        
        # Controls Layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Time Label (Current)
        self.time_current_label = QLabel("00:00")
        self.time_current_label.setFixedWidth(40)
        self.time_current_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        controls_layout.addWidget(self.time_current_label)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setEnabled(False)
        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderMoved.connect(self._on_slider_moved)
        self.slider.sliderReleased.connect(self._on_slider_released)
        controls_layout.addWidget(self.slider)
        
        # Time Label (Total)
        self.time_total_label = QLabel("00:00")
        self.time_total_label.setFixedWidth(40)
        controls_layout.addWidget(self.time_total_label)
        
        layout.addLayout(controls_layout)
        
    def set_task(self, task: Optional[VideoTask]):
        """Set the current task to preview."""
        self.current_task = task
        self.current_timestamp = 0.0
        
        if task is None:
            self._show_placeholder()
            self.slider.setEnabled(False)
            self.time_current_label.setText("00:00")
            self.time_total_label.setText("00:00")
            return
        
        # Update info
        if task.original_resolution:
            w, h = task.original_resolution
            self.info_label.setText(f"{w}x{h}")
        else:
            self.info_label.setText("")
            
        # Enable controls
        self.slider.setEnabled(True)
        self.slider.setValue(0)
        
        # Update duration label
        duration = task.duration if task.duration else 0
        self.time_total_label.setText(format_duration(duration))
        self._update_time_label()
        
        # Load video for preview (just show first frame)
        self._load_video(task.input_path)
    
    def set_render_preview(self, pixmap: QPixmap, timestamp: float):
        """
        Set preview frame during rendering.
        """
        self.is_rendering = True
        self.current_pixmap = pixmap
        self.current_timestamp = timestamp
        self._display_pixmap(pixmap)
        
        # Update slider/time if rendering
        if self.current_task and self.current_task.duration > 0:
            pos = int((timestamp / self.current_task.duration) * 1000)
            self.slider.blockSignals(True)
            self.slider.setValue(pos)
            self.slider.blockSignals(False)
            self._update_time_label()
    
    def clear_render_preview(self):
        """Clear render preview and return to input preview."""
        self.is_rendering = False
        if self.current_task:
            self._load_video(self.current_task.input_path)
        else:
            self._show_placeholder()
    
    def _load_video(self, video_path: Path):
        """Load video file for preview."""
        if not video_path.exists():
            self._show_placeholder("Video file not found")
            return
        
        # Show first frame
        self.current_timestamp = 0.0
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
    
    def resizeEvent(self, event):
        """Handle resize event."""
        super().resizeEvent(event)
        # Redisplay current pixmap at new size
        if self.current_pixmap:
            self._display_pixmap(self.current_pixmap)

    # --- Timeline Controls ---
        
    def _on_slider_pressed(self):
        """Slider interaction started."""
        self.is_scrubbing = True
            
    def _on_slider_moved(self, position):
        """Slider moved by user."""
        if not self.current_task or self.current_task.duration <= 0:
            return
            
        self.current_timestamp = (position / 1000.0) * self.current_task.duration
        self._update_time_label()
        
        # Throttle preview updates during scrubbing if needed
        # For now, we rely on the worker cancellation logic to handle rapid updates
        self.refresh_preview()
        
    def _on_slider_released(self):
        """Slider interaction ended."""
        self.is_scrubbing = False
            
    def _update_time_label(self):
        """Update current time label."""
        self.time_current_label.setText(format_duration(self.current_timestamp))

