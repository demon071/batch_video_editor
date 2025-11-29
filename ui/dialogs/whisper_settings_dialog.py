"""
Whisper Settings Dialog - Configure and run Whisper subtitle extraction.
"""
from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QSpinBox, 
                             QFileDialog, QGroupBox, QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal

from config.settings import AppConfig
from core.whisper_worker import WhisperWorker


class WhisperSettingsDialog(QDialog):
    """
    Dialog to configure Whisper settings and optionally run generation.
    """
    
    subtitle_generated = pyqtSignal(Path)  # Emits path to generated SRT
    
    def __init__(self, config: AppConfig, input_file: Path = None, parent=None):
        """
        Initialize dialog.
        
        Args:
            config: Application configuration
            input_file: Optional input file to process immediately
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config
        self.input_file = input_file
        self.worker = None
        
        self.setWindowTitle("Whisper Subtitle Settings")
        self.setMinimumWidth(500)
        self._init_ui()
        self._load_settings()
        
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # CLI Path
        cli_group = QGroupBox("Whisper CLI")
        cli_layout = QHBoxLayout()
        
        self.cli_path_edit = QLineEdit()
        self.cli_path_edit.setPlaceholderText("Path to whisper executable")
        self.cli_browse_btn = QPushButton("Browse...")
        self.cli_browse_btn.clicked.connect(self._browse_cli)
        
        cli_layout.addWidget(self.cli_path_edit)
        cli_layout.addWidget(self.cli_browse_btn)
        cli_group.setLayout(cli_layout)
        layout.addWidget(cli_group)
        
        # Model Settings
        model_group = QGroupBox("Model Settings")
        model_layout = QVBoxLayout()
        
        # Model selection
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.model_combo.setEditable(True) # Allow custom model path
        model_row.addWidget(self.model_combo)
        
        self.model_browse_btn = QPushButton("Browse...")
        self.model_browse_btn.clicked.connect(self._browse_model)
        model_row.addWidget(self.model_browse_btn)
        
        model_layout.addLayout(model_row)
        
        # Device selection
        device_row = QHBoxLayout()
        device_row.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(["cpu", "cuda"])
        device_row.addWidget(self.device_combo)
        model_layout.addLayout(device_row)
        
        # Language selection
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["auto", "en", "vi", "ja", "ko", "zh", "fr", "de", "es", "ru"])
        self.lang_combo.setEditable(True)
        lang_row.addWidget(self.lang_combo)
        model_layout.addLayout(lang_row)
        
        # Threads
        thread_row = QHBoxLayout()
        thread_row.addWidget(QLabel("Threads:"))
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 32)
        self.thread_spin.setValue(4)
        thread_row.addWidget(self.thread_spin)
        model_layout.addLayout(thread_row)
        
        # Word count
        word_row = QHBoxLayout()
        word_row.addWidget(QLabel("Max Words per Segment:"))
        self.word_spin = QSpinBox()
        self.word_spin.setRange(1, 100)
        self.word_spin.setValue(1)
        word_row.addWidget(self.word_spin)
        model_layout.addLayout(word_row)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Progress (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self._save_settings)
        
        self.generate_btn = QPushButton("Generate Subtitle")
        self.generate_btn.clicked.connect(self._generate)
        self.generate_btn.setEnabled(self.input_file is not None)
        if self.input_file:
            self.generate_btn.setText(f"Generate for {self.input_file.name}")
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
    def _load_settings(self):
        """Load settings from config."""
        self.cli_path_edit.setText(self.config.whisper_cli_path)
        
        model = self.config.whisper_model
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        else:
            self.model_combo.setCurrentText(model)
            
        device = self.config.whisper_device
        index = self.device_combo.findText(device)
        if index >= 0:
            self.device_combo.setCurrentIndex(index)
            
        index = self.device_combo.findText(device)
        if index >= 0:
            self.device_combo.setCurrentIndex(index)
            
        lang = self.config.whisper_language
        index = self.lang_combo.findText(lang)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
        else:
            self.lang_combo.setCurrentText(lang)
            
        self.thread_spin.setValue(self.config.whisper_threads)
        self.word_spin.setValue(self.config.whisper_word_count)
        
    def _save_settings(self):
        """Save settings to config."""
        self.config.whisper_cli_path = self.cli_path_edit.text()
        self.config.whisper_model = self.model_combo.currentText()
        self.config.whisper_device = self.device_combo.currentText()
        self.config.whisper_language = self.lang_combo.currentText()
        self.config.whisper_threads = self.thread_spin.value()
        self.config.whisper_word_count = self.word_spin.value()
        self.config.save()
        
    def _browse_cli(self):
        """Browse for CLI executable."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Whisper Executable", "", "Executables (*.exe);;All Files (*.*)"
        )
        if path:
            self.cli_path_edit.setText(path)
            
    def _browse_model(self):
        """Browse for model file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Whisper Model", "", "Model Files (*.pt *.bin);;All Files (*.*)"
        )
        if path:
            self.model_combo.setCurrentText(path)
            
    def _generate(self):
        """Run generation."""
        if not self.input_file:
            return
            
        cli_path = self.cli_path_edit.text()
        if not cli_path or not Path(cli_path).exists():
            QMessageBox.warning(self, "Error", "Please select a valid Whisper executable.")
            return
            
        # Save settings first
        self._save_settings()
        
        # Disable UI
        self.generate_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.status_label.setText("Generating subtitles...")
        
        # Start worker
        self.worker = WhisperWorker(
            cli_path=cli_path,
            model=self.model_combo.currentText(),
            device=self.device_combo.currentText(),
            language=self.lang_combo.currentText(),
            threads=self.thread_spin.value(),
            word_count=self.word_spin.value()
        )
        
        self.worker.log_message.connect(self._on_log)
        self.worker.task_completed.connect(self._on_success)
        self.worker.task_failed.connect(self._on_failure)
        
        output_dir = self.input_file.parent
        self.worker.start_processing(self.input_file, output_dir)
        
    def _on_log(self, msg):
        """Handle log message."""
        # Could append to a log text area if we had one
        pass
        
    def _on_success(self, result):
        """Handle success."""
        self.status_label.setText("Generation complete!")
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        # Assume output is input_file.srt
        srt_path = self.input_file.with_suffix('.srt')
        if srt_path.exists():
            self.subtitle_generated.emit(srt_path)
            QMessageBox.information(self, "Success", f"Subtitle generated:\n{srt_path.name}")
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "Process finished but SRT file not found.")
            
    def _on_failure(self, error):
        """Handle failure."""
        self.status_label.setText("Generation failed.")
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Generation failed:\n{error}")
