"""Task table widget for displaying video processing tasks."""
from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView,
                             QProgressBar, QWidget, QHBoxLayout, QLabel, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon
from models.video_task import VideoTask
from models.enums import TaskStatus
from utils.system_check import format_duration


class TaskTableWidget(QTableWidget):
    """
    Table widget for displaying video processing tasks.
    
    Shows filename, status, progress, duration, resolution, and error details.
    """
    
    # Signals
    task_retry_requested = pyqtSignal(VideoTask)
    task_remove_requested = pyqtSignal(VideoTask)
    task_open_output_requested = pyqtSignal(VideoTask)
    
    # Column indices
    COL_FILENAME = 0
    COL_STATUS = 1
    COL_PROGRESS = 2
    COL_DURATION = 3
    COL_RESOLUTION = 4
    COL_ERROR = 5
    
    def __init__(self, parent=None):
        """Initialize task table."""
        super().__init__(parent)
        self._init_ui()
        
        # Store task references
        self.task_rows = {}  # task -> row_index
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Filename", "Status", "Progress", "Duration", "Resolution", "Error"
        ])
        
        # Set column widths
        header = self.horizontalHeader()
        header.resizeSection(0, 300)  # Filename
        header.resizeSection(1, 100)  # Status
        header.resizeSection(2, 150)  # Progress
        header.resizeSection(3, 80)   # Duration
        header.resizeSection(4, 100)  # Resolution
        header.setStretchLastSection(True)  # Error column stretches
        
        # Configure table
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Apply dark theme
        self.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                alternate-background-color: #333333;
                color: #e0e0e0;
                gridline-color: #444444;
                border: 1px solid #555555;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #3a3a3a;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #e0e0e0;
                padding: 5px;
                border: 1px solid #555555;
                font-weight: bold;
            }
        """)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def add_task(self, task: VideoTask):
        """
        Add task to table.
        
        Args:
            task: VideoTask to add
        """
        row = self.rowCount()
        self.insertRow(row)
        
        # Filename
        filename_item = QTableWidgetItem(task.filename)
        self.setItem(row, self.COL_FILENAME, filename_item)
        
        # Status
        status_item = QTableWidgetItem(str(task.status))
        self._update_status_color(status_item, task.status)
        self.setItem(row, self.COL_STATUS, status_item)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setValue(int(task.progress))
        self.setCellWidget(row, self.COL_PROGRESS, progress_bar)
        
        # Duration
        duration_text = format_duration(task.duration) if task.duration > 0 else "Unknown"
        duration_item = QTableWidgetItem(duration_text)
        self.setItem(row, self.COL_DURATION, duration_item)
        
        # Resolution
        if task.original_resolution:
            resolution_text = f"{task.original_resolution[0]}x{task.original_resolution[1]}"
        else:
            resolution_text = "Unknown"
        resolution_item = QTableWidgetItem(resolution_text)
        self.setItem(row, self.COL_RESOLUTION, resolution_item)
        
        # Error (empty initially)
        error_item = QTableWidgetItem("")
        error_item.setForeground(QColor(200, 0, 0))
        self.setItem(row, self.COL_ERROR, error_item)
        
        # Store reference
        self.task_rows[task] = row
    
    def update_task(self, task: VideoTask):
        """
        Update task display.
        
        Args:
            task: VideoTask to update
        """
        if task not in self.task_rows:
            return
        
        row = self.task_rows[task]
        
        # Update status
        status_item = self.item(row, self.COL_STATUS)
        status_item.setText(str(task.status))
        self._update_status_color(status_item, task.status)
        
        # Update progress
        progress_bar = self.cellWidget(row, self.COL_PROGRESS)
        if progress_bar:
            progress_bar.setValue(int(task.progress))
        
        # Update error message if task failed
        error_item = self.item(row, self.COL_ERROR)
        if task.status == TaskStatus.ERROR and task.error_message:
            error_item.setText(task.error_message)
            error_item.setToolTip(task.error_message)  # Show full error on hover
        else:
            error_item.setText("")
            error_item.setToolTip("")
        
        # Scroll to current task if processing
        if task.is_processing:
            self.scrollToItem(status_item)
    
    def remove_task(self, task: VideoTask):
        """
        Remove task from table.
        
        Args:
            task: VideoTask to remove
        """
        if task not in self.task_rows:
            return
        
        row = self.task_rows[task]
        self.removeRow(row)
        
        # Update row indices
        del self.task_rows[task]
        for t, r in list(self.task_rows.items()):
            if r > row:
                self.task_rows[t] = r - 1
    
    def clear_tasks(self):
        """Clear all tasks from table."""
        self.setRowCount(0)
        self.task_rows.clear()
    
    def get_selected_task(self) -> VideoTask:
        """
        Get currently selected task.
        
        Returns:
            Selected VideoTask or None
        """
        selected_rows = self.selectionModel().selectedRows()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        
        # Find task by row
        for task, task_row in self.task_rows.items():
            if task_row == row:
                return task
        
        return None
    
    def _update_status_color(self, item: QTableWidgetItem, status: TaskStatus):
        """
        Update status item color based on status.
        
        Args:
            item: Table item to update
            status: Task status
        """
        colors = {
            TaskStatus.PENDING: QColor(200, 200, 200),
            TaskStatus.PROCESSING: QColor(100, 150, 255),
            TaskStatus.DONE: QColor(100, 200, 100),
            TaskStatus.ERROR: QColor(255, 100, 100),
            TaskStatus.CANCELLED: QColor(255, 200, 100),
        }
        
        color = colors.get(status, QColor(200, 200, 200))
        item.setBackground(color)
    
    def _show_context_menu(self, position):
        """
        Show context menu for task.
        
        Args:
            position: Menu position
        """
        task = self.get_selected_task()
        if not task:
            return
        
        menu = QMenu(self)
        
        # Show error details (only for failed tasks)
        if task.status == TaskStatus.ERROR and task.error_message:
            error_action = QAction("Show Error Details", self)
            error_action.triggered.connect(lambda: self._show_error_details(task))
            menu.addAction(error_action)
            menu.addSeparator()
        
        # Retry action (only for failed tasks)
        if task.status == TaskStatus.ERROR:
            retry_action = QAction("Retry", self)
            retry_action.triggered.connect(lambda: self.task_retry_requested.emit(task))
            menu.addAction(retry_action)
        
        # Remove action (only for non-processing tasks)
        if not task.is_processing:
            remove_action = QAction("Remove", self)
            remove_action.triggered.connect(lambda: self.task_remove_requested.emit(task))
            menu.addAction(remove_action)
        
        # Open output folder (only for completed tasks)
        if task.status == TaskStatus.DONE:
            open_action = QAction("Open Output Folder", self)
            open_action.triggered.connect(lambda: self.task_open_output_requested.emit(task))
            menu.addAction(open_action)
        
        if not menu.isEmpty():
            menu.exec_(self.mapToGlobal(position))
    
    def _show_error_details(self, task: VideoTask):
        """
        Show error details dialog.
        
        Args:
            task: Task with error
        """
        from PyQt5.QtWidgets import QMessageBox
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Error Details")
        msg.setText(f"Task failed: {task.filename}")
        msg.setDetailedText(task.error_message)
        msg.exec_()
