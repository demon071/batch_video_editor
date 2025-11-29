"""
Whisper Worker - Background thread for running Whisper CLI.
"""
import re
import json
import subprocess
from pathlib import Path
from PyQt5.QtCore import QObject, QProcess, pyqtSignal


class WhisperWorker(QObject):
    """
    Worker class for executing Whisper CLI commands in background.
    """
    
    # Signals
    progress_updated = pyqtSignal(float)  # Progress percentage (0-100)
    task_completed = pyqtSignal(str)  # Output SRT path
    task_failed = pyqtSignal(str)  # Error message
    log_message = pyqtSignal(str)  # Log output
    
    def __init__(self, cli_path: str, model: str, device: str, language: str, threads: int, word_count: int, parent=None):
        """
        Initialize worker.
        
        Args:
            cli_path: Path to Whisper executable
            model: Model name or path
            device: Device to use (cpu/cuda) - Note: whisper.cpp auto-detects or uses build flags, usually doesn't have --device flag like python.
            language: Language code
            threads: Number of threads
            word_count: Max words per segment (mapped to -ml)
            parent: Parent QObject
        """
        super().__init__(parent)
        self.cli_path = cli_path
        self.model = model
        self.device = device
        self.language = language
        self.threads = threads
        self.word_count = word_count
        self.process = None
        self.is_running = False
        self.stderr_buffer = []
        self.input_file = None
        self.temp_audio_file = None
        
    def start_processing(self, input_file: Path, output_dir: Path):
        """
        Start Whisper processing.
        
        Args:
            input_file: Path to input media file
            output_dir: Directory to save output SRT
        """
        self.input_file = input_file
        
        if not Path(self.cli_path).exists():
            self.task_failed.emit(f"Whisper CLI not found at: {self.cli_path}")
            return
            
        # 1. Extract Audio (if needed)
        # whisper.cpp typically needs 16kHz WAV
        self.log_message.emit("Extracting audio...")
        self.temp_audio_file = output_dir / f"{input_file.stem}_temp_audio.wav"
        
        if not self._extract_audio(input_file, self.temp_audio_file):
            self.task_failed.emit("Failed to extract audio from video.")
            return

        # 2. Build Command
        # User provided structure:
        # COMMAND = [
        #     cli_path,
        #     '-m', config.model,
        #     '-l', config.language,
        #     '-f', audio_path,
        #     # '-osrt',
        #     '-oj',
        #     '-ml', '1',
        #     '-of', json_path,
        #     '-t', str(config.threads)
        # ]
        
        # We will use '-osrt' to get SRT output directly as needed by the app.
        # Output filename will be derived from input filename.
        
        output_base = output_dir / input_file.stem
        
        cmd = [
            self.cli_path,
            '-m', self.model,
            '-l', self.language,
            '-f', str(self.temp_audio_file),
            '-osrt', # Output SRT
            '-ml', str(self.word_count), # Max segment length?
            '-of', str(output_base), # Output filename base (whisper adds .srt)
            '-t', str(self.threads)
        ]
        
        self.log_message.emit(f"Running command: {' '.join(cmd)}")
        
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_process_error)
        
        # Merge channels
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        
        self.is_running = True
        self.stderr_buffer = []
        
        try:
            self.process.start(cmd[0], cmd[1:])
        except Exception as e:
            self.is_running = False
            self.task_failed.emit(f"Failed to start Whisper: {str(e)}")
            
    def _extract_audio(self, input_path: Path, output_path: Path) -> bool:
        """Extract audio to 16kHz WAV using FFmpeg."""
        try:
            # ffmpeg -i input -ar 16000 -ac 1 -c:a pcm_s16le output.wav
            cmd = [
                'ffmpeg', '-y',
                '-i', str(input_path),
                '-ar', '16000',
                '-ac', '1',
                '-c:a', 'pcm_s16le',
                str(output_path)
            ]
            
            # Run synchronously
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode != 0:
                self.log_message.emit(f"FFmpeg error: {process.stderr}")
                return False
            return True
        except Exception as e:
            self.log_message.emit(f"Audio extraction exception: {e}")
            return False

    def stop(self):
        """Stop processing."""
        if self.process and self.is_running:
            self.is_running = False
            self.process.terminate()
            if not self.process.waitForFinished(2000):
                self.process.kill()
        
        # Cleanup temp file
        if self.temp_audio_file and self.temp_audio_file.exists():
            try:
                self.temp_audio_file.unlink()
            except:
                pass
                
    def _on_stdout(self):
        """Handle stdout."""
        if not self.process:
            return
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.log_message.emit(data)
        
    def _on_stderr(self):
        """Handle stderr."""
        if not self.process:
            return
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.log_message.emit(data)
        self.stderr_buffer.append(data)
        
    def _on_finished(self, exit_code, exit_status):
        """Handle completion."""
        self.is_running = False
        
        # Cleanup temp file
        if self.temp_audio_file and self.temp_audio_file.exists():
            try:
                self.temp_audio_file.unlink()
            except:
                pass
                
        if exit_code == 0:
            # Check for output file
            # whisper.cpp with -osrt and -of base produces base.srt
            if self.input_file:
                # We used output_base = output_dir / input_file.stem
                # So expected file is output_dir / input_file.stem + ".srt"
                expected_srt = self.input_file.with_suffix('.srt')
                
                # If the user provided output_dir is different, we need to check there.
                # In start_processing we used output_dir / input_file.stem
                # But wait, self.input_file.with_suffix('.srt') assumes same dir as input.
                # If output_dir is different, we need to construct it correctly.
                # Let's assume output_dir is passed correctly.
                
                # Re-construct expected path based on command logic
                output_dir = self.input_file.parent # We passed this in dialog
                expected_srt = output_dir / (self.input_file.stem + ".srt")
                
                if expected_srt.exists():
                    self.task_completed.emit("Success")
                else:
                    self.task_failed.emit(f"Whisper finished but SRT not found at {expected_srt}")
            else:
                 self.task_completed.emit("Success")
        else:
            error_msg = f"Whisper exited with code {exit_code}"
            if self.stderr_buffer:
                error_msg += f"\nLast output:\n{''.join(self.stderr_buffer[-10:])}"
            self.task_failed.emit(error_msg)
            
    def _on_process_error(self, error):
        """Handle process error."""
        if not self.is_running:
            return
        self.is_running = False
        self.task_failed.emit(f"Process error: {error}")
