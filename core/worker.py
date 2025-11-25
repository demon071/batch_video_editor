"""FFmpeg worker process using QProcess."""
import re
import subprocess
from pathlib import Path
from PyQt5.QtCore import QObject, QProcess, pyqtSignal
from models.video_task import VideoTask
from core.ffmpeg_builder_python import FFmpegPythonBuilder as FFmpegCommandBuilder


class FFmpegWorker(QObject):
    """
    Worker class for executing FFmpeg commands in background.
    
    Uses QProcess to run FFmpeg with progress monitoring.
    Emits signals for progress updates and completion.
    """
    
    # Signals
    progress_updated = pyqtSignal(float)  # Progress percentage (0-100)
    task_completed = pyqtSignal()
    task_failed = pyqtSignal(str)  # Error message
    log_message = pyqtSignal(str)  # Log output
    
    def __init__(self, task: VideoTask, parent=None):
        """
        Initialize worker.
        
        Args:
            task: VideoTask to process
            parent: Parent QObject
        """
        super().__init__(parent)
        self.task = task
        self.process = None
        self.duration = task.duration or 0.0
        self.is_running = False
        self.stderr_buffer = []  # Store stderr for error reporting
    
    def start(self):
        """Start FFmpeg processing."""
        # Validate task
        is_valid, error_msg = FFmpegCommandBuilder.validate_task(self.task)
        if not is_valid:
            self.task_failed.emit(error_msg)
            return
        
        # Build command
        cmd = FFmpegCommandBuilder.build_command(self.task)
        
        # Create process
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_process_error)
        
        # Merge stdout and stderr
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        
        # Start process
        self.is_running = True
        self.stderr_buffer = []
        
        try:
            self.process.start(cmd[0], cmd[1:])
        except Exception as e:
            self.is_running = False
            self.task_failed.emit(f"Failed to start FFmpeg: {str(e)}")
    
    def stop(self):
        """Stop FFmpeg processing."""
        if self.process and self.is_running:
            self.is_running = False
            # Try graceful termination first
            self.process.terminate()
            # Wait up to 2 seconds for termination
            if not self.process.waitForFinished(2000):
                # Force kill if still running
                self.process.kill()
                self.process.waitForFinished(1000)
    
    def _on_stdout(self):
        """Handle stdout data."""
        if not self.process:
            return
        
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self._parse_progress(data)
        self.log_message.emit(data)
        # Also store in buffer for error reporting
        self.stderr_buffer.append(data)
        # Keep only last 50 lines
        if len(self.stderr_buffer) > 50:
            self.stderr_buffer = self.stderr_buffer[-50:]
    
    def _on_stderr(self):
        """Handle stderr data."""
        if not self.process:
            return
        
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self._parse_progress(data)
        self.log_message.emit(data)
        # Store in buffer for error reporting
        self.stderr_buffer.append(data)
        # Keep only last 50 lines
        if len(self.stderr_buffer) > 50:
            self.stderr_buffer = self.stderr_buffer[-50:]
    
    def _parse_progress(self, output: str):
        """
        Parse FFmpeg output for progress information.
        
        Args:
            output: FFmpeg output text
        """
        # Look for time=HH:MM:SS.MS pattern
        time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', output)
        if time_match and self.duration > 0:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = float(time_match.group(3))
            
            current_time = hours * 3600 + minutes * 60 + seconds
            progress = min(100.0, (current_time / self.duration) * 100.0)
            
            self.progress_updated.emit(progress)
        
        # Also look for progress=end
        if 'progress=end' in output:
            self.progress_updated.emit(100.0)
    
    def _on_finished(self, exit_code, exit_status):
        """
        Handle process completion.
        
        Args:
            exit_code: Process exit code
            exit_status: QProcess exit status
        """
        self.is_running = False
        
        if exit_code == 0:
            self.task_completed.emit()
        else:
            # Get last lines from buffer for error context
            error_context = '\n'.join(self.stderr_buffer[-20:]) if self.stderr_buffer else "No output captured"
            error_msg = f"FFmpeg exited with code {exit_code}\n\nLast output:\n{error_context}"
            print(f"\nERROR: {error_msg}")
            self.task_failed.emit(error_msg)
    
    def _on_process_error(self, error):
        """
        Handle process error.
        
        Args:
            error: QProcess error code
        """
        if not self.is_running:
            return
        
        error_messages = {
            QProcess.FailedToStart: "FFmpeg failed to start. Check if FFmpeg is installed and in PATH.",
            QProcess.Crashed: "FFmpeg crashed during processing.",
            QProcess.Timedout: "FFmpeg process timed out.",
            QProcess.WriteError: "Error writing to FFmpeg process.",
            QProcess.ReadError: "Error reading from FFmpeg process.",
            QProcess.UnknownError: "Unknown FFmpeg error occurred."
        }
        
        error_msg = error_messages.get(error, f"FFmpeg error: {error}")
        
        # Add stderr context if available
        if self.stderr_buffer:
            error_context = '\n'.join(self.stderr_buffer[-20:])
            error_msg = f"{error_msg}\n\nFFmpeg output:\n{error_context}"
        
        print(f"\nERROR: {error_msg}")
        self.is_running = False
        self.task_failed.emit(error_msg)
