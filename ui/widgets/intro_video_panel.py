"""Intro video panel widget."""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QCheckBox, QLabel, QPushButton, QLineEdit,
                             QSpinBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path


class IntroVideoPanel(QWidget):
    """Panel for configuring intro video settings."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Group box
        self.group_box = QGroupBox("Intro Video")
        group_layout = QVBoxLayout()
        
        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable Intro Video")
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        group_layout.addWidget(self.enable_checkbox)
        
        # Options container
        self.options_container = QWidget()
        self.options_container.setVisible(False)
        options_layout = QVBoxLayout(self.options_container)
        options_layout.setContentsMargins(10, 5, 0, 0)
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Video:"))
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Select intro video...")
        self.file_edit.setReadOnly(True)
        file_layout.addWidget(self.file_edit)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_btn)
        options_layout.addLayout(file_layout)
        
        # Fade duration
        fade_layout = QHBoxLayout()
        fade_layout.addWidget(QLabel("Fade Duration (s):"))
        self.fade_spin = QSpinBox()
        self.fade_spin.setRange(0, 10)
        self.fade_spin.setValue(0)
        fade_layout.addWidget(self.fade_spin)
        fade_layout.addStretch()
        options_layout.addLayout(fade_layout)
        
        # Audio mix
        self.mix_audio_checkbox = QCheckBox("Mix audio with main video")
        self.mix_audio_checkbox.setChecked(True)
        options_layout.addWidget(self.mix_audio_checkbox)
        
        group_layout.addWidget(self.options_container)
        self.group_box.setLayout(group_layout)
        layout.addWidget(self.group_box)
    
    def _on_enable_changed(self, state):
        self.options_container.setVisible(state == Qt.Checked)
        self.settings_changed.emit()
    
    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Intro Video",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm)"
        )
        if file_path:
            self.file_edit.setText(file_path)
            self.settings_changed.emit()
    
    def get_settings(self) -> dict:
        return {
            'enabled': self.enable_checkbox.isChecked(),
            'file_path': self.file_edit.text(),
            'fade_duration': self.fade_spin.value(),
            'mix_audio': self.mix_audio_checkbox.isChecked(),
        }
