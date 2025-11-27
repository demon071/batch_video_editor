"""Main application window with professional video editor layout."""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QProgressBar, QStatusBar, QMenu, QAction,
                             QSplitter, QToolBar, QSizePolicy, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtGui import QIcon
from pathlib import Path
import os

from config.settings import AppConfig
from models.video_task import VideoTask
from core.queue_manager import QueueManager
from ui.widgets import (ProjectBrowserWidget, PreviewPlayerWidget, PropertiesPanelWidget)
from utils.system_check import check_ffmpeg, check_nvenc_support, get_video_info


class MainWindow(QMainWindow):
    """
    Main application window for batch video editor.
    
    Professional 3-panel layout:
    - Left: Project browser with task list
    - Center: Preview player
    - Right: Properties/settings panels
    """
    
    def __init__(self, config: AppConfig):
        """Initialize main window."""
        super().__init__()
        self.config = config
        self.queue_manager = QueueManager(self)
        self.video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        
        self._init_ui()
        self._connect_signals()
        self._load_config()
    
    def _init_ui(self):
        """Initialize UI components with professional layout."""
        self.setWindowTitle("Batch Video Editor - Professional")
        self.setMinimumSize(1400, 900)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create toolbar
        self._create_toolbar()
        
        # Central widget with 3-panel layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter (3 panels: left | center | right)
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # LEFT PANEL: Project Browser
        self.project_browser = ProjectBrowserWidget()
        self.main_splitter.addWidget(self.project_browser)
        
        # CENTER PANEL: Preview Player
        self.preview_player = PreviewPlayerWidget()
        self.main_splitter.addWidget(self.preview_player)
        
        # RIGHT PANEL: Properties
        self.properties_panel = PropertiesPanelWidget()
        self.main_splitter.addWidget(self.properties_panel)
        
        # Set initial sizes (25% | 50% | 25%)
        self.main_splitter.setSizes([350, 700, 350])
        
        main_layout.addWidget(self.main_splitter)
        
        # Bottom: Status bar with progress
        self._create_status_bar()
        
        # Apply dark theme
        self._apply_dark_theme()
    
    def _create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        add_files_action = QAction("Add Files...", self)
        add_files_action.setShortcut("Ctrl+O")
        add_files_action.triggered.connect(self._add_files)
        file_menu.addAction(add_files_action)
        
        load_folder_action = QAction("Load Folder...", self)
        load_folder_action.setShortcut("Ctrl+Shift+O")
        load_folder_action.triggered.connect(self._load_folder)
        file_menu.addAction(load_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        apply_settings_action = QAction("Apply Settings to All", self)
        apply_settings_action.setShortcut("Ctrl+A")
        apply_settings_action.triggered.connect(self._apply_settings_to_all)
        edit_menu.addAction(apply_settings_action)
        
        clear_action = QAction("Clear All Tasks", self)
        clear_action.triggered.connect(self._clear_tasks)
        edit_menu.addAction(clear_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_toolbar(self):
        """Create toolbar with common actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Add Files button
        add_files_btn = QPushButton("📁 Add Files")
        add_files_btn.clicked.connect(self._add_files)
        toolbar.addWidget(add_files_btn)
        
        # Load Folder button
        load_folder_btn = QPushButton("📂 Load Folder")
        load_folder_btn.clicked.connect(self._load_folder)
        toolbar.addWidget(load_folder_btn)
        
        toolbar.addSeparator()
        
        # Start button
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 4px 12px;")
        self.start_btn.clicked.connect(self._start_processing)
        self.start_btn.setEnabled(False)
        toolbar.addWidget(self.start_btn)
        
        # Pause button
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self._pause_processing)
        self.pause_btn.setEnabled(False)
        toolbar.addWidget(self.pause_btn)
        
        # Stop button
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; padding: 4px 12px;")
        self.stop_btn.clicked.connect(self._stop_processing)
        self.stop_btn.setEnabled(False)
        toolbar.addWidget(self.stop_btn)
        
        toolbar.addSeparator()
        
        # Clear button
        clear_btn = QPushButton("🗑 Clear All")
        clear_btn.clicked.connect(self._clear_tasks)
        toolbar.addWidget(clear_btn)
        
        toolbar.addSeparator()
        
        # Folder selection container
        folder_widget = QWidget()
        folder_layout = QHBoxLayout(folder_widget)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(5)
        
        # Input folder
        folder_layout.addWidget(QLabel("Input:"))
        self.input_folder_edit = QLineEdit()
        self.input_folder_edit.setPlaceholderText("Select input folder...")
        self.input_folder_edit.setMinimumWidth(150)
        self.input_folder_edit.setMaximumWidth(300)
        self.input_folder_edit.setFixedHeight(24)
        folder_layout.addWidget(self.input_folder_edit)
        
        input_browse_btn = QPushButton("...")
        input_browse_btn.setToolTip("Browse Input Folder")
        input_browse_btn.setFixedWidth(30)
        input_browse_btn.setFixedHeight(24)
        input_browse_btn.clicked.connect(self._browse_input_folder)
        folder_layout.addWidget(input_browse_btn)
        
        # Output folder
        folder_layout.addWidget(QLabel("Output:"))
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setPlaceholderText("Select output folder...")
        self.output_folder_edit.setMinimumWidth(150)
        self.output_folder_edit.setMaximumWidth(300)
        self.output_folder_edit.setFixedHeight(24)
        folder_layout.addWidget(self.output_folder_edit)
        
        output_browse_btn = QPushButton("...")
        output_browse_btn.setToolTip("Browse Output Folder")
        output_browse_btn.setFixedWidth(30)
        output_browse_btn.setFixedHeight(24)
        output_browse_btn.clicked.connect(self._browse_output_folder)
        folder_layout.addWidget(output_browse_btn)
        
        # Load button
        load_btn = QPushButton("Load")
        load_btn.setToolTip("Load Files from Input Folder")
        load_btn.setFixedHeight(24)
        load_btn.clicked.connect(self._load_files)
        load_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 2px 10px;")
        folder_layout.addWidget(load_btn)
        
        toolbar.addWidget(folder_widget)
        
        # Add spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
    
    def _create_status_bar(self):
        """Create status bar with progress."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status message
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, 1)
        
        # Overall progress
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimum(0)
        self.overall_progress.setMaximum(100)
        self.overall_progress.setMaximumWidth(200)
        self.overall_progress.setTextVisible(True)
        self.status_bar.addPermanentWidget(QLabel("Progress:"))
        self.status_bar.addPermanentWidget(self.overall_progress)
        
        # Task count
        self.task_count_label = QLabel("0/0 tasks")
        self.status_bar.addPermanentWidget(self.task_count_label)
    
    def _apply_dark_theme(self):
        """Apply dark theme stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            
            QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e0e0e0;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
            }
            
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #3c3c3c;
                text-align: center;
                color: #e0e0e0;
            }
            
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
            
            QSplitter::handle {
                background-color: #1e1e1e;
                width: 2px;
            }
            
            QSplitter::handle:hover {
                background-color: #4a4a4a;
            }
            
            QGroupBox {
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: bold;
            }
            
            QGroupBox::title {
                color: #e0e0e0;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
            
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
            
            QListWidget {
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            
            QListWidget::item {
                padding: 4px;
            }
            
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            
            QListWidget::item:hover {
                background-color: #3c3c3c;
            }
            
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #2b2b2b;
                height: 12px;
                border: none;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #555555;
                border-radius: 6px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #666666;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            QMenuBar {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            
            QMenuBar::item:selected {
                background-color: #3c3c3c;
            }
            
            QMenu {
                background-color: #2b2b2b;
                border: 1px solid #555555;
            }
            
            QMenu::item:selected {
                background-color: #4CAF50;
            }
            
            QToolBar {
                background-color: #2b2b2b;
                border-bottom: 1px solid #555555;
                spacing: 5px;
                padding: 5px;
            }
            
            QStatusBar {
                background-color: #2b2b2b;
                border-top: 1px solid #555555;
                color: #e0e0e0;
            }
            
            QSlider::groove:horizontal {
                border: 1px solid #555555;
                height: 8px;
                background: #3c3c3c;
                margin: 2px 0;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #555555;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            
            QSlider::handle:horizontal:hover {
                background: #45a049;
            }
        """)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        # Project browser signals
        self.project_browser.task_selected.connect(self._on_task_selected)
        self.project_browser.task_add_requested.connect(self._add_files)
        self.project_browser.task_remove_requested.connect(self._remove_task)
        self.project_browser.task_view_settings_requested.connect(self._view_task_settings)
        self.project_browser.task_retry_requested.connect(self._retry_task)
        self.project_browser.task_open_output_requested.connect(self._open_output_folder)
        
        # Properties panel signals
        self.properties_panel.settings_changed.connect(self._on_settings_changed)
        self.properties_panel.apply_to_all_requested.connect(self._apply_settings_to_all)
        
        # Codec panel settings changed
        codec_panel = self.properties_panel.get_codec_panel()
        codec_panel.settings_changed.connect(self._save_codec_settings)
        
        # Queue manager signals
        self.queue_manager.queue_started.connect(self._on_queue_started)
        self.queue_manager.queue_paused.connect(self._on_queue_paused)
        self.queue_manager.queue_completed.connect(self._on_queue_completed)
        self.queue_manager.task_started.connect(self._on_task_started)
        self.queue_manager.task_progress.connect(self._on_task_progress)
        self.queue_manager.task_completed.connect(self._on_task_completed)
        self.queue_manager.task_failed.connect(self._on_task_failed)
        self.queue_manager.task_added.connect(self._on_task_added)
    
    def _load_config(self):
        """Load configuration."""
        # Load last used folders
        if self.config.last_input_folder:
            self.input_folder_edit.setText(self.config.last_input_folder)
        if self.config.last_output_folder:
            self.output_folder_edit.setText(self.config.last_output_folder)
        
        # Set codec settings
        codec_panel = self.properties_panel.get_codec_panel()
        codec_panel.blockSignals(True)
        codec_panel.set_codec(self.config.codec)
        codec_panel.set_quality_mode(self.config.quality_mode)
        codec_panel.set_crf(self.config.crf)
        codec_panel.set_bitrate(self.config.bitrate)
        codec_panel.set_preset(self.config.preset)
        codec_panel.set_gpu_decoding(self.config.use_gpu_decoding)
        codec_panel.blockSignals(False)
        
        # Check GPU support
        gpu_available, gpu_msg = check_nvenc_support()
        codec_panel.set_gpu_available(gpu_available)
        
        # Check FFmpeg
        ffmpeg_available, ffmpeg_msg = check_ffmpeg()
        if ffmpeg_available:
            self._update_status(f"Ready - {ffmpeg_msg} - {gpu_msg}")
        else:
            QMessageBox.critical(
                self,
                "FFmpeg Not Found",
                f"{ffmpeg_msg}\n\nPlease install FFmpeg and add it to your system PATH."
            )
    
    def _save_codec_settings(self):
        """Save codec settings to config."""
        codec_panel = self.properties_panel.get_codec_panel()
        self.config.codec = codec_panel.get_codec()
        self.config.quality_mode = codec_panel.get_quality_mode()
        self.config.crf = codec_panel.get_crf()
        self.config.bitrate = codec_panel.get_bitrate()
        self.config.preset = codec_panel.get_preset()
        self.config.use_gpu_decoding = codec_panel.get_gpu_decoding()
    
    # Folder operations
    
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
        self._update_status(f"Loaded {len(video_files)} video(s)")
    
    # File operations
    
    def _add_files(self):
        """Add individual video files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video Files",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v)"
        )
        
        if files:
            video_files = [Path(f) for f in files]
            
            # Ask for output folder
            output_folder = QFileDialog.getExistingDirectory(
                self,
                "Select Output Folder"
            )
            
            if output_folder:
                self._create_tasks(video_files, Path(output_folder))
                self._update_status(f"Added {len(files)} video(s)")
    
    def _load_folder(self):
        """Load video files from folder."""
        input_folder = QFileDialog.getExistingDirectory(
            self,
            "Select Input Folder"
        )
        
        if not input_folder:
            return
        
        output_folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder"
        )
        
        if not output_folder:
            return
        
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        
        # Find video files
        video_files = []
        for file in input_path.iterdir():
            if file.is_file() and file.suffix.lower() in self.video_extensions:
                video_files.append(file)
        
        if not video_files:
            QMessageBox.information(self, "No Videos", "No video files found in input folder.")
            return
        
        self._create_tasks(video_files, output_path)
        self._update_status(f"Loaded {len(video_files)} video(s)")
    
    def _create_tasks(self, video_files: list, output_folder: Path):
        """Create tasks from video files."""
        params_panel = self.properties_panel.get_params_panel()
        codec_panel = self.properties_panel.get_codec_panel()
        text_panel = self.properties_panel.get_text_overlay_panel()
        image_panel = self.properties_panel.get_image_overlay_panel()
        video_panel = self.properties_panel.get_video_overlay_panel()
        intro_panel = self.properties_panel.get_intro_video_panel()
        outro_panel = self.properties_panel.get_outro_video_panel()
        stacking_panel = self.properties_panel.get_stacking_panel()
        background_panel = self.properties_panel.get_background_frame_panel()
        split_panel = self.properties_panel.get_split_panel()
        
        for video_file in video_files:
            # Get video info
            info = get_video_info(video_file)
            
            # Create output path
            output_file = output_folder / f"{video_file.stem}_processed{video_file.suffix}"
            
            # Create task
            task = VideoTask(
                input_path=video_file,
                output_path=output_file,
                speed=params_panel.get_speed(),
                volume=params_panel.get_volume(),
                scale=params_panel.get_scale(),
                crop=params_panel.get_crop(),
                watermark_type=params_panel.get_watermark_type(),
                watermark_image=params_panel.get_watermark_image(),
                watermark_position=params_panel.get_watermark_position(),
                subtitle_file=params_panel.get_subtitle_file(),
                codec=codec_panel.get_codec(),
                quality_mode=codec_panel.get_quality_mode(),
                crf=codec_panel.get_crf(),
                bitrate=codec_panel.get_bitrate(),
                preset=codec_panel.get_preset(),
                use_gpu_decoding=codec_panel.get_gpu_decoding()
            )
            
            # Parse trim times
            trim_start = params_panel.get_trim_start()
            if trim_start > 0:
                task.trim_start = trim_start
            
            cut_end = params_panel.get_cut_from_end()
            if cut_end > 0:
                task.cut_from_end = cut_end
            
            # Set video info
            if info:
                task.duration = info['duration']
                task.original_resolution = (info['width'], info['height'])
            
            # Add overlay settings
            task.text_settings = text_panel.get_text_settings()
            task.image_overlay = image_panel.get_settings()
            task.video_overlay = video_panel.get_settings()
            task.intro_video = intro_panel.get_settings()
            task.outro_video = outro_panel.get_settings()
            task.stack_settings = stacking_panel.get_settings()
            task.background_frame = background_panel.get_settings()
            task.split_settings = split_panel.get_settings()
            
            # Add to queue and browser
            self.queue_manager.add_task(task)
            self.project_browser.add_task(task)
        
        self.start_btn.setEnabled(True)
        self._update_task_count()
    
    def _on_settings_changed(self):
        """Handle settings changes from properties panel."""
        task = self.project_browser.get_selected_task()
        if not task:
            return
            
        # Update task with current settings
        params_panel = self.properties_panel.get_params_panel()
        codec_panel = self.properties_panel.get_codec_panel()
        
        # Processing Params
        task.speed = params_panel.get_speed()
        task.volume = params_panel.get_volume()
        task.trim_start = params_panel.get_trim_start()
        task.cut_from_end = params_panel.get_cut_from_end()
        task.target_resolution = params_panel.get_scale()
        task.crop = params_panel.get_crop()
        task.watermark_type = params_panel.get_watermark_type()
        task.watermark_text = params_panel.get_watermark_text()
        task.watermark_image = params_panel.get_watermark_image()
        task.watermark_position = params_panel.get_watermark_position()
        task.subtitle_file = params_panel.get_subtitle_file()
        
        # Codec Settings
        task.codec = codec_panel.get_codec()
        task.quality_mode = codec_panel.get_quality_mode()
        task.crf = codec_panel.get_crf()
        task.bitrate = codec_panel.get_bitrate()
        task.preset = codec_panel.get_preset()
        task.use_gpu_decoding = codec_panel.get_gpu_decoding()
        
        # Refresh preview
        self.preview_player.refresh_preview()
        
        # Update project browser display (e.g. duration might change)
        self.project_browser.update_task(task)

    def _apply_settings_to_all(self):
        """Apply current UI settings to all loaded tasks."""
        if self.queue_manager.is_running:
            QMessageBox.warning(self, "Cannot Apply", "Stop processing before applying new settings.")
            return
        
        tasks = self.queue_manager.get_all_tasks()
        
        if not tasks:
            QMessageBox.information(self, "No Tasks", "No tasks loaded. Please load videos first.")
            return
        
        reply = QMessageBox.question(
            self,
            "Apply Settings",
            f"Apply current settings to all {len(tasks)} tasks?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        params_panel = self.properties_panel.get_params_panel()
        codec_panel = self.properties_panel.get_codec_panel()
        text_panel = self.properties_panel.get_text_overlay_panel()
        image_panel = self.properties_panel.get_image_overlay_panel()
        video_panel = self.properties_panel.get_video_overlay_panel()
        intro_panel = self.properties_panel.get_intro_video_panel()
        outro_panel = self.properties_panel.get_outro_video_panel()
        stacking_panel = self.properties_panel.get_stacking_panel()
        background_panel = self.properties_panel.get_background_frame_panel()
        split_panel = self.properties_panel.get_split_panel()
        
        for task in tasks:
            task.speed = params_panel.get_speed()
            task.volume = params_panel.get_volume()
            task.scale = params_panel.get_scale()
            task.crop = params_panel.get_crop()
            task.watermark_type = params_panel.get_watermark_type()
            task.watermark_image = params_panel.get_watermark_image()
            task.watermark_position = params_panel.get_watermark_position()
            task.subtitle_file = params_panel.get_subtitle_file()
            
            trim_start = params_panel.get_trim_start()
            task.trim_start = trim_start if trim_start > 0 else None
            
            cut_end = params_panel.get_cut_from_end()
            task.cut_from_end = cut_end if cut_end > 0 else None
            
            task.codec = codec_panel.get_codec()
            task.quality_mode = codec_panel.get_quality_mode()
            task.crf = codec_panel.get_crf()
            task.bitrate = codec_panel.get_bitrate()
            task.preset = codec_panel.get_preset()
            task.use_gpu_decoding = codec_panel.get_gpu_decoding()
            
            task.text_settings = text_panel.get_text_settings()
            task.image_overlay = image_panel.get_settings()
            task.video_overlay = video_panel.get_settings()
            task.intro_video = intro_panel.get_settings()
            task.outro_video = outro_panel.get_settings()
            task.stack_settings = stacking_panel.get_settings()
            task.background_frame = background_panel.get_settings()
            task.split_settings = split_panel.get_settings()
            
            self.project_browser.update_task(task)
        
        self._update_status(f"Settings applied to {len(tasks)} tasks")
        QMessageBox.information(self, "Settings Applied", f"Successfully applied settings to {len(tasks)} tasks!")
    
    # Processing controls
    
    def _start_processing(self):
        """Start processing queue."""
        self.queue_manager.start()
    
    def _pause_processing(self):
        """Pause processing queue."""
        if not self.queue_manager.is_running:
            return
        
        if self.queue_manager.is_paused:
            self.queue_manager.resume()
            self.pause_btn.setText("⏸ Pause")
            self._update_status("Processing resumed")
        else:
            self.queue_manager.pause()
            self.pause_btn.setText("▶ Resume")
            self._update_status("Processing paused")
    
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
            self.pause_btn.setText("⏸ Pause")
            self._update_status("Processing stopped")
    
    def _clear_tasks(self):
        """Clear all tasks."""
        if self.queue_manager.is_running:
            QMessageBox.warning(self, "Cannot Clear", "Stop processing before clearing tasks.")
            return
        
        self.queue_manager.clear_tasks()
        self.project_browser.clear_tasks()
        self.start_btn.setEnabled(False)
        self._update_status("Tasks cleared")
        self._update_task_count()
    
    # Task operations
    
    def _retry_task(self, task: VideoTask):
        """Retry failed task."""
        self.queue_manager.retry_task(task)
        self.project_browser.update_task(task)
    
    def _remove_task(self, task: VideoTask):
        """Remove task from queue."""
        self.queue_manager.remove_task(task)
        self.project_browser.remove_task(task)
        self._update_task_count()
    
    def _open_output_folder(self, task: VideoTask):
        """Open output folder in file explorer."""
        folder = task.output_path.parent
        if folder.exists():
            os.startfile(str(folder))
    
    def _view_task_settings(self, task: VideoTask):
        """View task settings dialog."""
        from models.enums import TaskStatus
        
        # Show error details for failed tasks
        if task.status == TaskStatus.ERROR and task.error_message:
            QMessageBox.critical(
                self,
                f"Error Details - {task.filename}",
                f"Task failed with error:\n\n{task.error_message}"
            )
            return
        
        # Show basic settings info
        settings_text = f"Settings for: {task.filename}\n\n"
        settings_text += f"Speed: {task.speed}x\n"
        settings_text += f"Volume: {task.volume}\n"
        settings_text += f"Codec: {task.codec.name}\n"
        settings_text += f"Quality: {task.quality_mode.name}"
        
        if task.quality_mode.name == "CRF":
            settings_text += f" (CRF: {task.crf})\n"
        else:
            settings_text += f" (Bitrate: {task.bitrate})\n"
        
        settings_text += f"Preset: {task.preset.name}\n"
        settings_text += f"GPU Decoding: {'Yes' if task.use_gpu_decoding else 'No'}\n"
        
        if task.trim_start:
            settings_text += f"\nTrim Start: {task.trim_start}s"
        if task.cut_from_end:
            settings_text += f"\nCut from End: {task.cut_from_end}s"
        
        QMessageBox.information(
            self,
            "Task Settings",
            settings_text
        )
    
    # Event handlers
    
    def _on_task_selected(self, task: VideoTask):
        """Handle task selection."""
        self.preview_player.set_task(task)
    
    @pyqtSlot()
    def _on_queue_started(self):
        """Handle queue started."""
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self._update_status("Processing...")
    
    @pyqtSlot()
    def _on_queue_paused(self):
        """Handle queue paused."""
        self.pause_btn.setText("▶ Resume")
        self._update_status("Paused")
    
    @pyqtSlot()
    def _on_queue_completed(self):
        """Handle queue completed."""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setText("⏸ Pause")
        
        self.overall_progress.setValue(100)
        
        completed = self.queue_manager.completed_count
        failed = self.queue_manager.failed_count
        
        msg = f"Processing complete!\n\nCompleted: {completed}\nFailed: {failed}"
        QMessageBox.information(self, "Processing Complete", msg)
        
        self._update_status(f"Complete - {completed} succeeded, {failed} failed")
        self.preview_player.clear_render_preview()
    
    @pyqtSlot(VideoTask)
    def _on_task_started(self, task: VideoTask):
        """Handle task started."""
        self.project_browser.update_task(task)
        self._update_status(f"Processing: {task.filename}")
        self._update_task_count()
    
    @pyqtSlot(VideoTask, float)
    def _on_task_progress(self, task: VideoTask, progress: float):
        """Handle task progress."""
        self.project_browser.update_task(task)
        
        overall = self.queue_manager.total_progress
        self.overall_progress.setValue(int(overall))
    
    @pyqtSlot(VideoTask)
    def _on_task_completed(self, task: VideoTask):
        """Handle task completed."""
        self.project_browser.update_task(task)
        self._update_task_count()
    
    @pyqtSlot(VideoTask)
    def _on_task_added(self, task: VideoTask):
        """Handle new task added dynamically."""
        self.project_browser.add_task(task)
        self._update_status(f"Added split part: {task.filename}")
        self._update_task_count()
    
    def _on_task_failed(self, task: VideoTask, error: str):
        """Handle task failed."""
        self.project_browser.update_task(task)
        self._update_status(f"Error: {task.filename} - {error}")
        self._update_task_count()
    
    # UI updates
    
    def _update_status(self, message: str):
        """Update status bar message."""
        self.status_label.setText(message)
    
    def _update_task_count(self):
        """Update task count display."""
        total = len(self.queue_manager.get_all_tasks())
        completed = self.queue_manager.completed_count
        self.task_count_label.setText(f"{completed}/{total} tasks")
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Batch Video Editor",
            "Batch Video Editor v2.0 - Professional Edition\n\n"
            "A powerful desktop application for batch video processing using FFmpeg.\n\n"
            "Features:\n"
            "• Professional 3-panel layout\n"
            "• Batch processing with queue management\n"
            "• GPU acceleration (NVENC)\n"
            "• Multiple video filters and effects\n"
            "• Flexible codec and quality settings\n"
            "• Live preview during rendering\n\n"
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
