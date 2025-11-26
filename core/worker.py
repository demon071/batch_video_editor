"""FFmpeg worker process using QProcess."""
import re
import subprocess
from pathlib import Path
from PyQt5.QtCore import QObject, QProcess, pyqtSignal
from models.video_task import VideoTask
from models.enums import SplitMode
from core.ffmpeg_builder_python import FFmpegPythonBuilder as FFmpegCommandBuilder
from core.ffmpeg_splitter import FFmpegSplitter


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
    split_parts_created = pyqtSignal(list)  # List[VideoTask] - split part tasks
    
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
        # Check if this is a split task
        if self.task.split_settings and self.task.split_settings.enabled:
            self._process_split_task()
            return
        
        # Normal processing
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
    
    def _process_split_task(self):
        """Process video splitting task."""
        try:
            # Validate split task
            is_valid, error_msg = FFmpegSplitter.validate_task(self.task)
            if not is_valid:
                self.task_failed.emit(error_msg)
                return
            
            # Set running flag
            self.is_running = True
            
            # Split video using FFmpegSplitter
            # This is synchronous but fast (stream copy)
            output_files = FFmpegSplitter.split_video(self.task)
            
            # Update progress
            self.progress_updated.emit(100.0)
            
            # Log success
            self.log_message.emit(
                f"Split complete: {len(output_files)} parts created\n" +
                "\n".join([f"  - {f.name}" for f in output_files])
            )
            
            # Check if we should process split parts
            if self.task.split_settings.process_split_parts:
                # Create processing tasks for each split part
                split_tasks = self._create_split_part_tasks(output_files)
                
                # Emit signal with new tasks
                if split_tasks:
                    self.split_parts_created.emit(split_tasks)
                    self.log_message.emit(
                        f"\nCreated {len(split_tasks)} processing tasks for split parts"
                    )
            
            # Mark as complete
            self.is_running = False
            self.task_completed.emit()
            
        except Exception as e:
            self.is_running = False
            error_msg = f"Split failed: {str(e)}"
            print(f"\nERROR: {error_msg}")
            self.task_failed.emit(error_msg)
    
    def _create_split_part_tasks(self, split_files: list) -> list:
        """
        Create processing tasks for split parts.
        
        Args:
            split_files: List of split file paths
            
        Returns:
            List of VideoTask objects for processing split parts
        """
        tasks = []
        
        for split_file in split_files:
            # Clone task settings for this split part
            part_task = self._clone_task_for_split_part(split_file)
            if part_task:
                tasks.append(part_task)
        
        return tasks
    
    def _clone_task_for_split_part(self, input_file: Path):
        """
        Clone task settings for a split part.
        
        Args:
            input_file: Path to split part file
            
        Returns:
            VideoTask with cloned settings
        """
        try:
            # Create output path
            output_dir = self.task.output_path.parent
            output_file = output_dir / f"{input_file.stem}_processed{input_file.suffix}"
            
            # Create new task with same settings (except split settings)
            from utils.system_check import get_video_info
            info = get_video_info(input_file)
            
            task = VideoTask(
                input_path=input_file,
                output_path=output_file,
                # Copy processing parameters
                speed=self.task.speed,
                volume=self.task.volume,
                trim_start=self.task.trim_start,
                cut_from_end=self.task.cut_from_end,
                scale=self.task.scale,
                crop=self.task.crop,
                # Copy watermark settings
                watermark_type=self.task.watermark_type,
                watermark_text=self.task.watermark_text,
                watermark_image=self.task.watermark_image,
                watermark_position=self.task.watermark_position,
                # Copy subtitle settings
                subtitle_file=self.task.subtitle_file,
                # Copy text overlay settings
                text_settings=self.task.text_settings,
                # Copy media overlay settings
                image_overlay=self.task.image_overlay,
                video_overlay=self.task.video_overlay,
                intro_video=self.task.intro_video,
                outro_video=self.task.outro_video,
                # Copy stacking settings
                stack_settings=self.task.stack_settings,
                # Copy background frame settings
                background_frame=self.task.background_frame,
                # Copy codec settings
                codec=self.task.codec,
                quality_mode=self.task.quality_mode,
                crf=self.task.crf,
                bitrate=self.task.bitrate,
                preset=self.task.preset,
                # Set video info
                duration=info['duration'] if info else 0.0,
                original_resolution=(info['width'], info['height']) if info else None,
                # IMPORTANT: Don't split again!
                split_settings=None
            )
            
            # Store reference to intermediate file for cleanup
            task.intermediate_file = input_file
            
            return task
            
        except Exception as e:
            self.log_message.emit(f"Warning: Failed to create task for {input_file.name}: {str(e)}")
            return None
    
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
