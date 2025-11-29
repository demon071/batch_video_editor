"""
Worker thread for asynchronous task loading.
"""
from PyQt5.QtCore import QThread, pyqtSignal
from pathlib import Path
from typing import List, Dict, Any

from models.video_task import VideoTask
from utils.system_check import get_video_info


class TaskLoaderWorker(QThread):
    """
    Worker thread to load video tasks asynchronously.
    """
    task_loaded = pyqtSignal(object)  # Emits VideoTask
    finished = pyqtSignal()
    
    def __init__(self, video_files: List[Path], output_folder: Path, settings: Dict[str, Any]):
        super().__init__()
        self.video_files = video_files
        self.output_folder = output_folder
        self.settings = settings
        self._is_cancelled = False
        
    def run(self):
        """Process files."""
        for video_file in self.video_files:
            if self._is_cancelled:
                break
                
            try:
                # Get video info (blocking I/O)
                info = get_video_info(video_file)
                
                # Create output path
                output_file = self.output_folder / f"{video_file.stem}_processed{video_file.suffix}"
                
                # Create task
                task = VideoTask(
                    input_path=video_file,
                    output_path=output_file,
                    speed=self.settings.get('speed', 1.0),
                    volume=self.settings.get('volume', 1.0),
                    scale=self.settings.get('scale'),
                    crop=self.settings.get('crop'),

                    subtitle_file=self.settings.get('subtitle_file'),
                    codec=self.settings.get('codec'),
                    quality_mode=self.settings.get('quality_mode'),
                    crf=self.settings.get('crf'),
                    bitrate=self.settings.get('bitrate'),
                    preset=self.settings.get('preset'),
                    use_gpu_decoding=self.settings.get('use_gpu_decoding', False)
                )
                
                # Optional settings
                task.trim_start = self.settings.get('trim_start')
                task.cut_from_end = self.settings.get('cut_from_end')
                task.trim_end = self.settings.get('trim_end')
                
                # Set video info
                if info:
                    task.duration = info['duration']
                    task.original_resolution = (info['width'], info['height'])
                
                # Complex settings
                task.text_settings = self.settings.get('text_settings')
                task.image_overlay = self.settings.get('image_overlay')
                task.video_overlay = self.settings.get('video_overlay')
                task.intro_video = self.settings.get('intro_video')
                task.outro_video = self.settings.get('outro_video')
                task.stack_settings = self.settings.get('stack_settings')
                task.background_frame = self.settings.get('background_frame')
                task.split_settings = self.settings.get('split_settings')
                
                self.task_loaded.emit(task)
                
            except Exception as e:
                print(f"Error loading task for {video_file}: {e}")
                
        self.finished.emit()
    
    def cancel(self):
        """Cancel the worker."""
        self._is_cancelled = True
        self.quit()
        self.wait()
