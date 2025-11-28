"""
Project Browser Widget - Left panel showing task list with thumbnails.

Displays all video tasks in an organized list with:
- Thumbnail previews
- Status indicators
- Progress bars
- Quick actions
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QPushButton, QLabel, QProgressBar,
                             QMenu, QAction, QLineEdit, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter
from pathlib import Path
from typing import Optional, List
import cv2

from models.video_task import VideoTask
from models.enums import TaskStatus


class TaskListItem(QListWidgetItem):
    """Custom list item for video tasks with thumbnail."""
    
    def __init__(self, task: VideoTask):
        super().__init__()
        self.task = task
        self.thumbnail: Optional[QPixmap] = None
        self._update_display()
    
    def _update_display(self):
        """Update item display text and icon."""
        # Status icon
        status_icons = {
            TaskStatus.PENDING: "⏸",
            TaskStatus.PROCESSING: "●",
            TaskStatus.DONE: "✓",
            TaskStatus.ERROR: "✗",
            TaskStatus.CANCELLED: "⊘"
        }
        
        icon = status_icons.get(self.task.status, "○")
        
        # Display text
        duration = f"{int(self.task.duration)}s" if self.task.duration > 0 else "?"
        progress = f"{int(self.task.progress)}%" if self.task.progress > 0 else ""
        
        text = f"{icon} {self.task.filename}\n{duration} {progress}"
        self.setText(text)
        
        # Set size hint for thumbnail
        self.setSizeHint(QSize(200, 80))
    
    def set_thumbnail(self, pixmap: QPixmap):
        """Set thumbnail image."""
        self.thumbnail = pixmap
        if pixmap:
            self.setIcon(QIcon(pixmap))


class ProjectBrowserWidget(QWidget):
    """
    Project browser panel showing all video tasks.
    
    Features:
    - Task list with thumbnails
    - Status indicators
    - Search/filter
    - Quick actions (add, remove, clear)
    
    Signals:
        task_selected: Emitted when a task is selected
        task_add_requested: User wants to add files
        task_remove_requested: User wants to remove a task
        task_view_settings_requested: User wants to view task settings
    """
    
    # Signals
    task_selected = pyqtSignal(VideoTask)
    task_add_requested = pyqtSignal()
    task_remove_requested = pyqtSignal(VideoTask)
    task_view_settings_requested = pyqtSignal(VideoTask)
    task_retry_requested = pyqtSignal(VideoTask)
    task_open_output_requested = pyqtSignal(VideoTask)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks: List[VideoTask] = []
        self.task_items = {}  # task -> TaskListItem mapping
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Search bar
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search tasks...")
        self.search_edit.textChanged.connect(self._filter_tasks)
        layout.addWidget(self.search_edit)
        
        # Task list
        self.task_list = QListWidget()
        self.task_list.setIconSize(QSize(120, 68))  # 16:9 thumbnail
        self.task_list.setSpacing(2)
        self.task_list.setAlternatingRowColors(True)
        self.task_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.task_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self._show_context_menu)
        
        # Apply dark theme
        self.task_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                alternate-background-color: #333333;
                color: #e0e0e0;
                border: 1px solid #555555;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #444444;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
        """)
        layout.addWidget(self.task_list)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Files")
        self.add_btn.clicked.connect(self.task_add_requested.emit)
        button_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self._remove_selected)
        self.remove_btn.setEnabled(False)
        button_layout.addWidget(self.remove_btn)
        
        layout.addLayout(button_layout)
        
        # Task count label
        self.count_label = QLabel("0 tasks")
        self.count_label.setStyleSheet("color: #888;")
        layout.addWidget(self.count_label)
    
    def add_task(self, task: VideoTask):
        """Add a task to the browser."""
        if task in self.tasks:
            return
        
        self.tasks.append(task)
        
        # Create list item
        item = TaskListItem(task)
        self.task_items[task] = item
        self.task_list.addItem(item)
        
        # Extract thumbnail asynchronously
        self._extract_thumbnail(task, item)
        
        self._update_count()
    
    def update_task(self, task: VideoTask):
        """Update task display."""
        if task not in self.task_items:
            return
        
        item = self.task_items[task]
        item._update_display()
    
    def remove_task(self, task: VideoTask):
        """Remove a task from the browser."""
        if task not in self.tasks:
            return
        
        self.tasks.remove(task)
        item = self.task_items.pop(task)
        row = self.task_list.row(item)
        self.task_list.takeItem(row)
        
        self._update_count()
    
    def clear_tasks(self):
        """Clear all tasks."""
        self.tasks.clear()
        self.task_items.clear()
        self.task_list.clear()
        self._update_count()
    
    def get_selected_task(self) -> Optional[VideoTask]:
        """Get currently selected task."""
        items = self.task_list.selectedItems()
        if not items:
            return None
        
        item = items[0]
        if isinstance(item, TaskListItem):
            return item.task
        return None
    
    def _extract_thumbnail(self, task: VideoTask, item: TaskListItem):
        """Extract thumbnail from video file."""
        try:
            if not task.input_path.exists():
                return
            
            # Use OpenCV to extract first frame
            cap = cv2.VideoCapture(str(task.input_path))
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Convert to QPixmap
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                
                from PyQt5.QtGui import QImage
                q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                
                # Scale to thumbnail size (120x68)
                pixmap = QPixmap.fromImage(q_image)
                pixmap = pixmap.scaled(120, 68, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                item.set_thumbnail(pixmap)
        except Exception as e:
            print(f"Failed to extract thumbnail: {e}")
    
    def _filter_tasks(self, text: str):
        """Filter tasks based on search text."""
        text = text.lower()
        
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if isinstance(item, TaskListItem):
                visible = text in item.task.filename.lower()
                item.setHidden(not visible)
    
    def _on_selection_changed(self):
        """Handle selection change."""
        task = self.get_selected_task()
        self.remove_btn.setEnabled(task is not None)
        
        if task:
            self.task_selected.emit(task)
    
    def _remove_selected(self):
        """Remove selected task."""
        task = self.get_selected_task()
        if task:
            self.task_remove_requested.emit(task)
    
    def _update_count(self):
        """Update task count label."""
        count = len(self.tasks)
        self.count_label.setText(f"{count} task{'s' if count != 1 else ''}")
    
    def _show_context_menu(self, position):
        """Show context menu for task."""
        task = self.get_selected_task()
        if not task:
            return
        
        menu = QMenu(self)
        
        # View Settings
        view_settings_action = QAction("View Settings", self)
        view_settings_action.triggered.connect(lambda: self.task_view_settings_requested.emit(task))
        menu.addAction(view_settings_action)
        
        menu.addSeparator()
        
        # Retry (for failed tasks)
        if task.status == TaskStatus.ERROR:
            retry_action = QAction("Retry", self)
            retry_action.triggered.connect(lambda: self.task_retry_requested.emit(task))
            menu.addAction(retry_action)
        
        # Remove (for non-processing tasks)
        if not task.is_processing:
            remove_action = QAction("Remove", self)
            remove_action.triggered.connect(lambda: self.task_remove_requested.emit(task))
            menu.addAction(remove_action)
        
        # Open Output Folder (for completed tasks)
        if task.status == TaskStatus.DONE:
            open_action = QAction("Open Output Folder", self)
            open_action.triggered.connect(lambda: self.task_open_output_requested.emit(task))
            menu.addAction(open_action)
        
        if not menu.isEmpty():
            menu.exec_(self.task_list.mapToGlobal(position))
