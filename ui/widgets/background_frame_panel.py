"""
Background Frame Panel Widget.

Provides UI for configuring background frame with aspect ratio and background type.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QRadioButton, QButtonGroup,
                             QGroupBox, QLineEdit, QComboBox, QColorDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from pathlib import Path
from typing import Optional, Dict

# Resolution presets for each aspect ratio
RESOLUTION_PRESETS = {
    '16:9': [
        (1920, 1080, '1080p (Full HD)'),
        (1280, 720, '720p (HD)'),
        (3840, 2160, '4K (UHD)'),
        (2560, 1440, '1440p (2K)'),
    ],
    '9:16': [
        (1080, 1920, '1080x1920 (Vertical Full HD)'),
        (720, 1280, '720x1280 (Vertical HD)'),
        (1080, 1920, '1080x1920 (Instagram/TikTok)'),
    ],
    '1:1': [
        (1080, 1080, '1080x1080 (Instagram Square)'),
        (1920, 1920, '1920x1920 (Large Square)'),
        (720, 720, '720x720 (Small Square)'),
    ],
    '4:3': [
        (1024, 768, '1024x768 (XGA)'),
        (1280, 960, '1280x960'),
        (1600, 1200, '1600x1200 (UXGA)'),
    ],
    '3:4': [
        (768, 1024, '768x1024 (Vertical XGA)'),
        (960, 1280, '960x1280'),
        (1200, 1600, '1200x1600'),
    ],
}

class BackgroundFramePanel(QWidget):
    """Panel for configuring background frame settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_color = '#000000'  # Default black
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main Group Box
        self.group_box = QGroupBox("Background Frame")
        self.group_box.setCheckable(True)
        self.group_box.setChecked(False)
        group_layout = QVBoxLayout(self.group_box)
        
        # Aspect Ratio Selection
        aspect_layout = QHBoxLayout()
        aspect_layout.addWidget(QLabel("Aspect Ratio:"))
        
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(['16:9', '9:16', '1:1', '4:3', '3:4'])
        self.aspect_combo.currentTextChanged.connect(self._on_aspect_changed)
        aspect_layout.addWidget(self.aspect_combo)
        aspect_layout.addStretch()
        group_layout.addLayout(aspect_layout)
        
        # Resolution Selection
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Resolution:"))
        
        self.resolution_combo = QComboBox()
        self._update_resolution_list('16:9')
        resolution_layout.addWidget(self.resolution_combo)
        resolution_layout.addStretch()
        group_layout.addLayout(resolution_layout)
        
        # Background Type Selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Background Type:"))
        
        self.type_group = QButtonGroup(self)
        
        self.color_radio = QRadioButton("Color")
        self.color_radio.setChecked(True)
        self.type_group.addButton(self.color_radio)
        type_layout.addWidget(self.color_radio)
        
        self.image_radio = QRadioButton("Image")
        self.type_group.addButton(self.image_radio)
        type_layout.addWidget(self.image_radio)
        
        self.video_radio = QRadioButton("Video")
        self.type_group.addButton(self.video_radio)
        type_layout.addWidget(self.video_radio)
        
        type_layout.addStretch()
        group_layout.addLayout(type_layout)
        
        # Color Picker
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        
        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self._choose_color)
        self._update_color_button()
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        group_layout.addLayout(color_layout)
        
        # File Path Selection
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("File:"))
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select image or video file...")
        self.path_input.setEnabled(False)
        path_layout.addWidget(self.path_input)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_file)
        self.browse_btn.setEnabled(False)
        path_layout.addWidget(self.browse_btn)
        
        group_layout.addLayout(path_layout)
        
        # Connect signals
        self.type_group.buttonClicked.connect(self._on_type_changed)
        
        layout.addWidget(self.group_box)
        
    def _on_aspect_changed(self, aspect_ratio: str):
        """Handle aspect ratio change."""
        self._update_resolution_list(aspect_ratio)
        
    def _update_resolution_list(self, aspect_ratio: str):
        """Update resolution combo box based on aspect ratio."""
        self.resolution_combo.clear()
        presets = RESOLUTION_PRESETS.get(aspect_ratio, [])
        for width, height, label in presets:
            self.resolution_combo.addItem(label, (width, height))
            
    def _on_type_changed(self):
        """Handle background type change."""
        is_color = self.color_radio.isChecked()
        is_file = self.image_radio.isChecked() or self.video_radio.isChecked()
        
        self.color_btn.setEnabled(is_color)
        self.path_input.setEnabled(is_file)
        self.browse_btn.setEnabled(is_file)
        
        if self.image_radio.isChecked():
            self.path_input.setPlaceholderText("Select image file...")
        elif self.video_radio.isChecked():
            self.path_input.setPlaceholderText("Select video file...")
            
    def _choose_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Choose Background Color")
        if color.isValid():
            self.selected_color = color.name()
            self._update_color_button()
            
    def _update_color_button(self):
        """Update color button appearance."""
        self.color_btn.setStyleSheet(f"background-color: {self.selected_color}; color: white;")
        self.color_btn.setText(f"Color: {self.selected_color}")
        
    def _browse_file(self):
        """Browse for image or video file."""
        if self.image_radio.isChecked():
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Background Image",
                "",
                "Image Files (*.jpg *.jpeg *.png *.bmp *.gif)"
            )
        else:  # video
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Background Video",
                "",
                "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v)"
            )
            
        if path:
            self.path_input.setText(path)
            
    def get_settings(self) -> Optional[Dict]:
        """Get background frame settings."""
        if not self.group_box.isChecked():
            return None
            
        aspect_ratio = self.aspect_combo.currentText()
        resolution = self.resolution_combo.currentData()
        
        if not resolution:
            return None
            
        settings = {
            'enabled': True,
            'aspect_ratio': aspect_ratio,
            'resolution': resolution,
        }
        
        if self.color_radio.isChecked():
            settings['background_type'] = 'color'
            settings['background_color'] = self.selected_color
        elif self.image_radio.isChecked():
            path_str = self.path_input.text().strip()
            if not path_str:
                return None
            settings['background_type'] = 'image'
            settings['background_path'] = Path(path_str)
        else:  # video
            path_str = self.path_input.text().strip()
            if not path_str:
                return None
            settings['background_type'] = 'video'
            settings['background_path'] = Path(path_str)
            
        return settings
