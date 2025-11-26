"""Task queue manager for batch processing."""
import queue
from typing import List, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from models.video_task import VideoTask
from models.enums import TaskStatus
from core.worker import FFmpegWorker


class QueueManager(QObject):
    """
    Manages queue of video processing tasks.
    
    Processes tasks sequentially to avoid resource conflicts.
    Coordinates with FFmpegWorker for actual processing.
    """
    
    # Signals
    queue_started = pyqtSignal()
    queue_paused = pyqtSignal()
    queue_completed = pyqtSignal()
    task_started = pyqtSignal(VideoTask)
    task_progress = pyqtSignal(VideoTask, float)  # task, progress
    task_completed = pyqtSignal(VideoTask)
    task_failed = pyqtSignal(VideoTask, str)  # task, error_message
    task_added = pyqtSignal(VideoTask)  # New task added dynamically
    
    def __init__(self, parent=None):
        """
        Initialize queue manager.
        
        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self.tasks: List[VideoTask] = []
        self.current_worker: Optional[FFmpegWorker] = None
        self.current_task_index: int = -1
        self.is_running = False
        self.is_paused = False
    
    def add_task(self, task: VideoTask):
        """
        Add task to queue.
        
        Args:
            task: VideoTask to add
        """
        self.tasks.append(task)
    
    def add_tasks(self, tasks: List[VideoTask]):
        """
        Add multiple tasks to queue.
        
        Args:
            tasks: List of VideoTask objects
        """
        self.tasks.extend(tasks)
    
    def clear_tasks(self):
        """Clear all tasks from queue."""
        if not self.is_running:
            self.tasks.clear()
            self.current_task_index = -1
    
    def remove_task(self, task: VideoTask):
        """
        Remove task from queue.
        
        Args:
            task: VideoTask to remove
        """
        if task in self.tasks and not task.is_processing:
            self.tasks.remove(task)
    
    def get_tasks(self) -> List[VideoTask]:
        """
        Get all tasks in queue.
        
        Returns:
            List of VideoTask objects
        """
        return self.tasks
    
    def get_all_tasks(self) -> List[VideoTask]:
        """
        Get all tasks in queue (alias for get_tasks).
        
        Returns:
            List of VideoTask objects
        """
        return self.tasks
    
    def start(self):
        """Start processing queue."""
        if self.is_running:
            return
        
        if not self.tasks:
            return
        
        self.is_running = True
        self.is_paused = False
        self.queue_started.emit()
        
        # Start from first pending task
        self.current_task_index = -1
        self._process_next_task()
    
    def pause(self):
        """Pause queue processing."""
        self.is_paused = True
        self.queue_paused.emit()
        
        # Stop current worker
        if self.current_worker:
            self.current_worker.stop()
    
    def resume(self):
        """Resume queue processing."""
        if not self.is_paused:
            return
        
        self.is_paused = False
        self.queue_started.emit()
        self._process_next_task()
    
    def stop(self):
        """Stop queue processing."""
        self.is_running = False
        self.is_paused = False
        
        # Stop current worker
        if self.current_worker:
            self.current_worker.stop()
            self.current_worker = None
        
        # Reset all processing tasks to pending
        for task in self.tasks:
            if task.is_processing:
                task.reset()
    
    def _process_next_task(self):
        """Process next pending task in queue."""
        if self.is_paused or not self.is_running:
            return
        
        # Find next pending task
        next_task = None
        for i, task in enumerate(self.tasks):
            if task.status == TaskStatus.PENDING:
                next_task = task
                self.current_task_index = i
                break
        
        if next_task is None:
            # No more pending tasks
            self.is_running = False
            self.queue_completed.emit()
            return
        
        # Start processing task
        self._start_task(next_task)
    
    def _start_task(self, task: VideoTask):
        """
        Start processing a task.
        
        Args:
            task: VideoTask to process
        """
        task.set_processing()
        self.task_started.emit(task)
        
        # Create worker
        self.current_worker = FFmpegWorker(task)
        self.current_worker.progress_updated.connect(
            lambda progress: self._on_task_progress(task, progress)
        )
        self.current_worker.task_completed.connect(
            lambda: self._on_task_completed(task)
        )
        self.current_worker.task_failed.connect(
            lambda error: self._on_task_failed(task, error)
        )
        self.current_worker.split_parts_created.connect(self._on_split_parts_created)
        
        # Start worker
        self.current_worker.start()
    
    def _on_split_parts_created(self, split_tasks: List[VideoTask]):
        """
        Handle split parts created by worker.
        
        Args:
            split_tasks: List of new VideoTask objects
        """
        for task in split_tasks:
            self.add_task(task)
            self.task_added.emit(task)
    
    def _on_task_progress(self, task: VideoTask, progress: float):
        """
        Handle task progress update.
        
        Args:
            task: VideoTask being processed
            progress: Progress percentage
        """
        task.progress = progress
        self.task_progress.emit(task, progress)
    
    def _on_task_completed(self, task: VideoTask):
        """
        Handle task completion.
        
        Args:
            task: Completed VideoTask
        """
        task.set_done()
        self.task_completed.emit(task)
        
        # Clean up worker
        if self.current_worker:
            self.current_worker.deleteLater()
            self.current_worker = None
        
        # Auto-cleanup intermediate file if exists
        if task.intermediate_file and task.intermediate_file.exists():
            try:
                task.intermediate_file.unlink()
                print(f"Deleted intermediate file: {task.intermediate_file}")
            except Exception as e:
                print(f"Failed to delete intermediate file: {e}")
        
        # Process next task
        self._process_next_task()
    
    def _on_task_failed(self, task: VideoTask, error_message: str):
        """
        Handle task failure.
        
        Args:
            task: Failed VideoTask
            error_message: Error description
        """
        task.set_error(error_message)
        self.task_failed.emit(task, error_message)
        
        # Clean up worker
        if self.current_worker:
            self.current_worker.deleteLater()
            self.current_worker = None
        
        # Continue with next task
        self._process_next_task()
    
    def retry_task(self, task: VideoTask):
        """
        Retry a failed task.
        
        Args:
            task: VideoTask to retry
        """
        if task in self.tasks and task.status == TaskStatus.ERROR:
            task.reset()
            
            # If not currently running, start queue
            if not self.is_running:
                self.start()
    
    @property
    def pending_count(self) -> int:
        """Get number of pending tasks."""
        return sum(1 for task in self.tasks if task.status == TaskStatus.PENDING)
    
    @property
    def processing_count(self) -> int:
        """Get number of processing tasks."""
        return sum(1 for task in self.tasks if task.status == TaskStatus.PROCESSING)
    
    @property
    def completed_count(self) -> int:
        """Get number of completed tasks."""
        return sum(1 for task in self.tasks if task.status == TaskStatus.DONE)
    
    @property
    def failed_count(self) -> int:
        """Get number of failed tasks."""
        return sum(1 for task in self.tasks if task.status == TaskStatus.ERROR)
    
    @property
    def total_progress(self) -> float:
        """
        Calculate overall progress percentage.
        
        Returns:
            Progress percentage (0-100)
        """
        if not self.tasks:
            return 0.0
        
        total = 0.0
        for task in self.tasks:
            if task.status == TaskStatus.DONE:
                total += 100.0
            elif task.status == TaskStatus.PROCESSING:
                total += task.progress
        
        return total / len(self.tasks)
