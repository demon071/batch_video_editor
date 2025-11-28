"""
Project Browser Widget - Left panel showing task list with details.

Displays all video tasks in an organized table with:
- Filename
- Status
- Progress
- Duration
- Resolution
- Size
- Ratio
- Error details
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from typing import Optional, List

from models.video_task import VideoTask
from models.enums import TaskStatus
from ui.widgets.task_table import TaskTableWidget


class ProjectBrowserWidget(QWidget):
    """
    Project browser panel showing all video tasks.
    
    Features:
    - Task table with full details
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
        
        # Task table
        self.task_table = TaskTableWidget()
        self.task_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Connect table signals
        self.task_table.task_retry_requested.connect(self.task_retry_requested)
        self.task_table.task_remove_requested.connect(self.task_remove_requested)
        self.task_table.task_open_output_requested.connect(self.task_open_output_requested)
        self.task_table.task_view_settings_requested.connect(self.task_view_settings_requested)
        
        layout.addWidget(self.task_table)
        
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
        self.task_table.add_task(task)
        self._update_count()
    
    def update_task(self, task: VideoTask):
        """Update task display."""
        self.task_table.update_task(task)
    
    def remove_task(self, task: VideoTask):
        """Remove a task from the browser."""
        if task not in self.tasks:
            return
        
        self.tasks.remove(task)
        self.task_table.remove_task(task)
        self._update_count()
    
    def clear_tasks(self):
        """Clear all tasks."""
        self.tasks.clear()
        self.task_table.clear_tasks()
        self._update_count()
    
    def get_selected_task(self) -> Optional[VideoTask]:
        """Get currently selected task."""
        return self.task_table.get_selected_task()
    
    def _filter_tasks(self, text: str):
        """Filter tasks based on search text."""
        text = text.lower()
        
        for i in range(self.task_table.rowCount()):
            # Filename is in column 0
            item = self.task_table.item(i, 0)
            if item:
                visible = text in item.text().lower()
                self.task_table.setRowHidden(i, not visible)
    
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
