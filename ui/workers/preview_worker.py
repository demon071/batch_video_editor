"""
Worker thread for asynchronous preview generation.
"""
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from typing import Optional, List
import subprocess
import sys
from pathlib import Path

from models.video_task import VideoTask
from core.preview_builder import PreviewBuilder


class PreviewWorker(QThread):
    """
    Worker thread to run FFmpeg preview generation asynchronously.
    """
    preview_ready = pyqtSignal(QPixmap)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, task: VideoTask, timestamp: float):
        super().__init__()
        self.task = task
        self.timestamp = timestamp
        self._is_cancelled = False
        
    def run(self):
        """Run FFmpeg command."""
        if self._is_cancelled:
            return
            
        try:
            # Build command
            cmd = PreviewBuilder.build_preview_command(self.task, self.timestamp)
            
            if self._is_cancelled:
                return

            # Run FFmpeg
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            
            # Read output
            stdout, stderr = process.communicate()
            
            if self._is_cancelled:
                return
                
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                self.error_occurred.emit(f"FFmpeg error: {error_msg}")
                return
                
            if not stdout:
                self.error_occurred.emit("No output from FFmpeg")
                return
                
            # Create QImage from data
            image = QImage.fromData(stdout)
            if image.isNull():
                self.error_occurred.emit("Failed to create image from data")
                return
                
            pixmap = QPixmap.fromImage(image)
            self.preview_ready.emit(pixmap)
            
        except Exception as e:
            if not self._is_cancelled:
                self.error_occurred.emit(str(e))
    
    def cancel(self):
        """Cancel the worker."""
        self._is_cancelled = True
        self.quit()
        self.wait()
