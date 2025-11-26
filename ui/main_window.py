"""Main application window."""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QProgressBar, QStatusBar, QMenuBar, QMenu, QAction,
                             QLineEdit, QScrollArea, QSplitter)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon
from pathlib import Path
import os

from config.settings import AppConfig
from models.video_task import VideoTask
from core.queue_manager import QueueManager
from ui.widgets import (ProcessingParamsPanel, CodecSettingsPanel, TaskTableWidget,
                       TextOverlayPanel, ImageOverlayPanel, VideoOverlayPanel,
                       IntroVideoPanel, OutroVideoPanel, StackingPanel, BackgroundFramePanel)
from utils.system_check import check_ffmpeg, check_nvenc_support, get_video_info, parse_duration
class MainWindow(QMainWindow):
    """
    Main application window for batch video editor.
    
    Provides UI for selecting files, configuring parameters, and monitoring processing.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize main window.
        
        Args:
            config: Application configuration
        """
        super().__init__()
        self.config = config
        self.queue_manager = QueueManager(self)
        self.video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        
        self._init_ui()
        self._connect_signals()
        self._load_config()
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Batch Video Editor")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Input/Output folder selection
        folder_layout = QHBoxLayout()
        
        # Input folder
        folder_layout.addWidget(QLabel("Input Folder:"))
        self.input_folder_edit = QLineEdit()
        self.input_folder_edit.setPlaceholderText("Select input folder...")
        folder_layout.addWidget(self.input_folder_edit)
        self.input_browse_btn = QPushButton("Browse...")
        self.input_browse_btn.clicked.connect(self._browse_input_folder)
        folder_layout.addWidget(self.input_browse_btn)
        
        # Output folder
        folder_layout.addWidget(QLabel("Output Folder:"))
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setPlaceholderText("Select output folder...")
        folder_layout.addWidget(self.output_folder_edit)
        self.output_browse_btn = QPushButton("Browse...")
        self.output_browse_btn.clicked.connect(self._browse_output_folder)
        folder_layout.addWidget(self.output_browse_btn)
        
        # Load files button
        self.load_files_btn = QPushButton("Load Files")
        self.load_files_btn.clicked.connect(self._load_files)
        folder_layout.addWidget(self.load_files_btn)
        
        main_layout.addLayout(folder_layout)
        
        # Splitter for table and settings
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Task table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.task_table = TaskTableWidget()
        left_layout.addWidget(self.task_table)
        
        splitter.addWidget(left_widget)
        
        # Right side: Settings panels
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        # Processing parameters panel
        self.params_panel = ProcessingParamsPanel()
        settings_layout.addWidget(self.params_panel)
        
        # Codec settings panel
        self.codec_panel = CodecSettingsPanel()
        settings_layout.addWidget(self.codec_panel)
        
        # Text overlay panel
        self.text_overlay_panel = TextOverlayPanel()
        settings_layout.addWidget(self.text_overlay_panel)
        
        # Image overlay panel
        self.image_overlay_panel = ImageOverlayPanel()
        settings_layout.addWidget(self.image_overlay_panel)
        
        # Video overlay panel
        self.video_overlay_panel = VideoOverlayPanel()
        settings_layout.addWidget(self.video_overlay_panel)
        
        # Intro video panel
        self.intro_video_panel = IntroVideoPanel()
        settings_layout.addWidget(self.intro_video_panel)
        
        # Outro video panel
        self.outro_video_panel = OutroVideoPanel()
        settings_layout.addWidget(self.outro_video_panel)
        
        # Stacking panel
        self.stacking_panel = StackingPanel()
        settings_layout.addWidget(self.stacking_panel)
        
        # Background frame panel
        self.background_frame_panel = BackgroundFramePanel()
        settings_layout.addWidget(self.background_frame_panel)
        
        settings_layout.addStretch()
        scroll.setWidget(settings_widget)
        right_layout.addWidget(scroll)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([800, 400])
        
        main_layout.addWidget(splitter)
        
        # Bottom controls
        controls_layout = QHBoxLayout()
        
        # Overall progress
        controls_layout.addWidget(QLabel("Overall Progress:"))
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimum(0)
        self.overall_progress.setMaximum(100)
        controls_layout.addWidget(self.overall_progress)
        
        # Apply Settings button
        self.apply_settings_btn = QPushButton("Apply Settings to All Tasks")
        self.apply_settings_btn.clicked.connect(self._apply_settings_to_all)
        self.apply_settings_btn.setEnabled(False)
        self.apply_settings_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        controls_layout.addWidget(self.apply_settings_btn)
        
        # Control buttons
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.clicked.connect(self._start_processing)
        self.start_btn.setEnabled(False)
        controls_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self._pause_processing)
        self.pause_btn.setEnabled(False)
        controls_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop_processing)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self._clear_tasks)
        controls_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(controls_layout)
        
        # Menu bar
        self._create_menu_bar()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar("Ready")
    
    def _create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        add_files_action = QAction("Add Files...", self)
        add_files_action.triggered.connect(self._add_files)
        file_menu.addAction(add_files_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        # Queue manager signals
        self.queue_manager.queue_started.connect(self._on_queue_started)
        self.queue_manager.queue_paused.connect(self._on_queue_paused)
        self.queue_manager.queue_completed.connect(self._on_queue_completed)
        self.queue_manager.task_started.connect(self._on_task_started)
        self.queue_manager.task_progress.connect(self._on_task_progress)
        self.queue_manager.task_completed.connect(self._on_task_completed)
        self.queue_manager.task_failed.connect(self._on_task_failed)
        
        # Task table signals
        self.task_table.task_retry_requested.connect(self._retry_task)
        self.task_table.task_remove_requested.connect(self._remove_task)
        self.task_table.task_open_output_requested.connect(self._open_output_folder)
        
        # Codec settings signals
        self.codec_panel.settings_changed.connect(self._save_codec_settings)
    
    def _load_config(self):
        """Load configuration."""
        # Set last used folders
        if self.config.last_input_folder:
            self.input_folder_edit.setText(self.config.last_input_folder)
        if self.config.last_output_folder:
            self.output_folder_edit.setText(self.config.last_output_folder)
        
        # Block signals while loading to prevent saving during load
        self.codec_panel.blockSignals(True)
        
        # Set codec settings
        self.codec_panel.set_codec(self.config.codec)
        self.codec_panel.set_quality_mode(self.config.quality_mode)
        self.codec_panel.set_crf(self.config.crf)
        self.codec_panel.set_bitrate(self.config.bitrate)
        self.codec_panel.set_preset(self.config.preset)
        
        # Unblock signals
        self.codec_panel.blockSignals(False)
        
        # Check GPU support
        gpu_available, gpu_msg = check_nvenc_support()
        self.codec_panel.set_gpu_available(gpu_available)
        
        # Check FFmpeg
        ffmpeg_available, ffmpeg_msg = check_ffmpeg()
        if ffmpeg_available:
            self._update_status_bar(f"Ready - {ffmpeg_msg} - {gpu_msg}")
        else:
            QMessageBox.critical(
                self,
                "FFmpeg Not Found",
                f"{ffmpeg_msg}\n\nPlease install FFmpeg and add it to your system PATH."
            )
    
    def _save_codec_settings(self):
        """Save codec settings to config when changed."""
        self.config.codec = self.codec_panel.get_codec()
        self.config.quality_mode = self.codec_panel.get_quality_mode()
        self.config.crf = self.codec_panel.get_crf()
        self.config.bitrate = self.codec_panel.get_bitrate()
        self.config.preset = self.codec_panel.get_preset()
    
    def _browse_input_folder(self):
        """Browse for input folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Input Folder",
            self.input_folder_edit.text() or ""
        )
        if folder:
            self.input_folder_edit.setText(folder)
            self.config.last_input_folder = folder
    
    def _browse_output_folder(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            self.output_folder_edit.text() or ""
        )
        if folder:
            self.output_folder_edit.setText(folder)
            self.config.last_output_folder = folder
    
    def _load_files(self):
        """Load video files from input folder."""
        input_folder = self.input_folder_edit.text().strip()
        output_folder = self.output_folder_edit.text().strip()
        
        if not input_folder or not output_folder:
            QMessageBox.warning(self, "Missing Folders", "Please select both input and output folders.")
            return
        
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        
        if not input_path.exists():
            QMessageBox.warning(self, "Invalid Input", "Input folder does not exist.")
            return
        
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
        
        # Find video files
        video_files = []
        for file in input_path.iterdir():
            if file.is_file() and file.suffix.lower() in self.video_extensions:
                video_files.append(file)
        
        if not video_files:
            QMessageBox.information(self, "No Videos", "No video files found in input folder.")
            return
        
        # Create tasks
        self._create_tasks(video_files, output_path)
        
        self._update_status_bar(f"Loaded {len(video_files)} video(s)")
    
    def _add_files(self):
        """Add individual video files."""
        output_folder = self.output_folder_edit.text().strip()
        
        if not output_folder:
            QMessageBox.warning(self, "Missing Output Folder", "Please select an output folder first.")
            return
        
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video Files",
            self.input_folder_edit.text() or "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v)"
        )
        
        if files:
            video_files = [Path(f) for f in files]
            output_path = Path(output_folder)
            self._create_tasks(video_files, output_path)
            self._update_status_bar(f"Added {len(files)} video(s)")
    
    def _create_tasks(self, video_files: list, output_folder: Path):
        """
        Create tasks from video files.
        
        Args:
            video_files: List of video file paths
            output_folder: Output folder path
        """
        for video_file in video_files:
            # Get video info
            info = get_video_info(video_file)
            
            # Create output path
            output_file = output_folder / f"{video_file.stem}_processed{video_file.suffix}"
            
            # Create task
            task = VideoTask(
                input_path=video_file,
                output_path=output_file,
                speed=self.params_panel.get_speed(),
                volume=self.params_panel.get_volume(),
                scale=self.params_panel.get_scale(),
                crop=self.params_panel.get_crop(),
                watermark_type=self.params_panel.get_watermark_type(),
                watermark_text=self.params_panel.get_watermark_text(),
                watermark_image=self.params_panel.get_watermark_image(),
                watermark_position=self.params_panel.get_watermark_position(),
                subtitle_file=self.params_panel.get_subtitle_file(),
                codec=self.codec_panel.get_codec(),
                quality_mode=self.codec_panel.get_quality_mode(),
                crf=self.codec_panel.get_crf(),
                bitrate=self.codec_panel.get_bitrate(),
                preset=self.codec_panel.get_preset()
            )
            
            # Parse trim times
            trim_start = self.params_panel.get_trim_start()
            if trim_start > 0:
                task.trim_start = trim_start
            
            cut_end = self.params_panel.get_cut_from_end()
            if cut_end > 0:
                task.cut_from_end = cut_end
            
            # Set video info
            if info:
                task.duration = info['duration']
                task.original_resolution = (info['width'], info['height'])
            
            # Add text overlay settings
            task.text_settings = self.text_overlay_panel.get_text_settings()
            
            # Add media overlay settings
            task.image_overlay = self.image_overlay_panel.get_settings()
            task.video_overlay = self.video_overlay_panel.get_settings()
            task.intro_video = self.intro_video_panel.get_settings()
            task.outro_video = self.outro_video_panel.get_settings()
            
            # Add stacking settings
            task.stack_settings = self.stacking_panel.get_settings()
            
            # Add background frame settings
            task.background_frame = self.background_frame_panel.get_settings()
            
            # Add to queue and table
            self.queue_manager.add_task(task)
            self.task_table.add_task(task)
        
        self.start_btn.setEnabled(True)
        self.apply_settings_btn.setEnabled(True)

    def _apply_settings_to_all(self):
        """Apply current UI settings to all loaded tasks."""
        if self.queue_manager.is_running:
            QMessageBox.warning(self, "Cannot Apply", "Stop processing before applying new settings.")
            return
        
        # Get all tasks from queue manager
        tasks = self.queue_manager.get_all_tasks()
        
        if not tasks:
            QMessageBox.information(self, "No Tasks", "No tasks loaded. Please load videos first.")
            return
        
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Apply Settings",
            f"Apply current settings to all {len(tasks)} tasks?\n\n"
            "This will update:\n"
            "• Processing parameters (speed, volume, trim, scale, crop)\n"
            "• Text overlay settings\n"
            "• Watermark settings\n"
            "• Codec and quality settings",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Apply settings to each task
        for task in tasks:
            # Update processing parameters
            task.speed = self.params_panel.get_speed()
            task.volume = self.params_panel.get_volume()
            task.scale = self.params_panel.get_scale()
            task.crop = self.params_panel.get_crop()
            task.watermark_type = self.params_panel.get_watermark_type()
            task.watermark_text = self.params_panel.get_watermark_text()
            task.watermark_image = self.params_panel.get_watermark_image()
            task.watermark_position = self.params_panel.get_watermark_position()
            task.subtitle_file = self.params_panel.get_subtitle_file()
            
            # Update trim times
            trim_start = self.params_panel.get_trim_start()
            if trim_start > 0:
                task.trim_start = trim_start
            else:
                task.trim_start = None
            
            cut_end = self.params_panel.get_cut_from_end()
            if cut_end > 0:
                task.cut_from_end = cut_end
            else:
                task.cut_from_end = None
            
            # Update codec settings
            task.codec = self.codec_panel.get_codec()
            task.quality_mode = self.codec_panel.get_quality_mode()
            task.crf = self.codec_panel.get_crf()
            task.bitrate = self.codec_panel.get_bitrate()
            task.preset = self.codec_panel.get_preset()
            
            # Update text overlay settings
            task.text_settings = self.text_overlay_panel.get_text_settings()
            
            # Update stacking settings
            task.stack_settings = self.stacking_panel.get_settings()
            
            # Update background frame settings
            task.background_frame = self.background_frame_panel.get_settings()
            
            # Update task in table
            self.task_table.update_task(task)
        
        self._update_status_bar(f"Settings applied to {len(tasks)} tasks")
        QMessageBox.information(
            self,
            "Settings Applied",
            f"Successfully applied settings to {len(tasks)} tasks!"
        )
    
    def _start_processing(self):
        """Start processing queue."""
        self.queue_manager.start()
    
    def _pause_processing(self):
        """Pause processing queue."""
        if not self.queue_manager.is_running:
            return
        
        if self.queue_manager.is_paused:
            # Resume
            self.queue_manager.resume()
            self.pause_btn.setText("Pause")
            self._update_status_bar("Processing resumed")
        else:
            # Pause
            self.queue_manager.pause()
            self.pause_btn.setText("Resume")
            self._update_status_bar("Processing paused")
    
    def _stop_processing(self):
        """Stop processing queue."""
        if not self.queue_manager.is_running:
            return
        
        reply = QMessageBox.question(
            self,
            "Stop Processing",
            "Are you sure you want to stop processing?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.queue_manager.stop()
            self.pause_btn.setText("Pause")
            self._update_status_bar("Processing stopped")
    
    def _clear_tasks(self):
        """Clear all tasks."""
        if self.queue_manager.is_running:
            QMessageBox.warning(self, "Cannot Clear", "Stop processing before clearing tasks.")
            return
        
        self.queue_manager.clear_tasks()
        self.task_table.clear_tasks()
        self.start_btn.setEnabled(False)
        self.apply_settings_btn.setEnabled(False)
        self._update_status_bar("Tasks cleared")
    
    def _retry_task(self, task: VideoTask):
        """Retry failed task."""
        self.queue_manager.retry_task(task)
        self.task_table.update_task(task)
    
    def _remove_task(self, task: VideoTask):
        """Remove task from queue."""
        self.queue_manager.remove_task(task)
        self.task_table.remove_task(task)
    
    def _open_output_folder(self, task: VideoTask):
        """Open output folder in file explorer."""
        folder = task.output_path.parent
        if folder.exists():
            os.startfile(str(folder))
    
    # Queue manager slots
    
    @pyqtSlot()
    def _on_queue_started(self):
        """Handle queue started."""
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.load_files_btn.setEnabled(False)
        self._update_status_bar("Processing...")
    
    @pyqtSlot()
    def _on_queue_paused(self):
        """Handle queue paused."""
        self.pause_btn.setText("Resume")
        self._update_status_bar("Paused")
    
    @pyqtSlot()
    def _on_queue_completed(self):
        """Handle queue completed."""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.load_files_btn.setEnabled(True)
        self.pause_btn.setText("Pause")
        
        # Update overall progress
        self.overall_progress.setValue(100)
        
        # Show completion message
        completed = self.queue_manager.completed_count
        failed = self.queue_manager.failed_count
        
        msg = f"Processing complete!\n\nCompleted: {completed}\nFailed: {failed}"
        QMessageBox.information(self, "Processing Complete", msg)
        
        self._update_status_bar(f"Complete - {completed} succeeded, {failed} failed")
    
    @pyqtSlot(VideoTask)
    def _on_task_started(self, task: VideoTask):
        """Handle task started."""
        self.task_table.update_task(task)
        self._update_status_bar(f"Processing: {task.filename}")
    
    @pyqtSlot(VideoTask, float)
    def _on_task_progress(self, task: VideoTask, progress: float):
        """Handle task progress."""
        self.task_table.update_task(task)
        
        # Update overall progress
        overall = self.queue_manager.total_progress
        self.overall_progress.setValue(int(overall))
    
    @pyqtSlot(VideoTask)
    def _on_task_completed(self, task: VideoTask):
        """Handle task completed."""
        self.task_table.update_task(task)
    
    @pyqtSlot(VideoTask, str)
    def _on_task_failed(self, task: VideoTask, error: str):
        """Handle task failed."""
        self.task_table.update_task(task)
        self._update_status_bar(f"Error: {task.filename} - {error}")
    
    def _update_status_bar(self, message: str):
        """Update status bar message."""
        self.status_bar.showMessage(message)
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Batch Video Editor",
            "Batch Video Editor v1.0\n\n"
            "A powerful desktop application for batch video processing using FFmpeg.\n\n"
            "Features:\n"
            "â€¢ Batch processing with queue management\n"
            "â€¢ GPU acceleration (NVENC)\n"
            "â€¢ Multiple video filters and effects\n"
            "â€¢ Flexible codec and quality settings\n\n"
            "Built with PyQt5 and FFmpeg"
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.queue_manager.is_running:
            reply = QMessageBox.question(
                self,
                "Processing Active",
                "Processing is still active. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            self.queue_manager.stop()
        
        event.accept()
