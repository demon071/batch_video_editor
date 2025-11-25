"""Processing parameters panel widget."""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QSlider, QLineEdit, QComboBox, QPushButton,
                             QFileDialog, QRadioButton, QButtonGroup, QSpinBox,
                             QDoubleSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path
from models.enums import WatermarkType


class ProcessingParamsPanel(QWidget):
    """
    Panel for configuring video processing parameters.
    
    Includes controls for speed, volume, trim, scale, crop, watermark, and subtitle.
    """
    
    # Signals
    params_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize parameters panel."""
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Speed control
        speed_group = QGroupBox("Speed")
        speed_layout = QVBoxLayout()
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)  # 0.5x
        self.speed_slider.setMaximum(200)  # 2.0x
        self.speed_slider.setValue(100)  # 1.0x
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(25)
        
        self.speed_label = QLabel("1.0x")
        self.speed_slider.valueChanged.connect(self._update_speed_label)
        
        speed_layout.addWidget(self.speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)
        
        # Volume control
        volume_group = QGroupBox("Volume")
        volume_layout = QVBoxLayout()
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)  # 0%
        self.volume_slider.setMaximum(200)  # 200%
        self.volume_slider.setValue(100)  # 100%
        self.volume_slider.setTickPosition(QSlider.TicksBelow)
        self.volume_slider.setTickInterval(25)
        
        self.volume_label = QLabel("100%")
        self.volume_slider.valueChanged.connect(self._update_volume_label)
        
        volume_layout.addWidget(self.volume_label)
        volume_layout.addWidget(self.volume_slider)
        volume_group.setLayout(volume_layout)
        layout.addWidget(volume_group)
        
        # Trim control
        trim_group = QGroupBox("Trim")
        trim_layout = QVBoxLayout()
        
        trim_start_layout = QHBoxLayout()
        trim_start_layout.addWidget(QLabel("Cut Start (s):"))
        self.trim_start_spin = QDoubleSpinBox()
        self.trim_start_spin.setRange(0, 99999)
        self.trim_start_spin.setSingleStep(0.5)
        self.trim_start_spin.setValue(0)
        trim_start_layout.addWidget(self.trim_start_spin)
        trim_layout.addLayout(trim_start_layout)
        
        trim_end_layout = QHBoxLayout()
        trim_end_layout.addWidget(QLabel("Cut End (s):"))
        self.trim_end_spin = QDoubleSpinBox()
        self.trim_end_spin.setRange(0, 99999)
        self.trim_end_spin.setSingleStep(0.5)
        self.trim_end_spin.setValue(0)
        trim_end_layout.addWidget(self.trim_end_spin)
        trim_layout.addLayout(trim_end_layout)
        
        trim_group.setLayout(trim_layout)
        layout.addWidget(trim_group)
        
        # Scale control
        scale_group = QGroupBox("Scale")
        scale_layout = QHBoxLayout()
        
        scale_layout.addWidget(QLabel("Resolution:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItems([
            "Original",
            "1920x1080 (1080p)",
            "1280x720 (720p)",
            "854x480 (480p)",
            "640x360 (360p)"
        ])
        scale_layout.addWidget(self.scale_combo)
        
        scale_group.setLayout(scale_layout)
        layout.addWidget(scale_group)
        
        # Crop control
        crop_group = QGroupBox("Crop")
        crop_layout = QVBoxLayout()
        
        crop_row1 = QHBoxLayout()
        crop_row1.addWidget(QLabel("X:"))
        self.crop_x_spin = QSpinBox()
        self.crop_x_spin.setMaximum(9999)
        crop_row1.addWidget(self.crop_x_spin)
        crop_row1.addWidget(QLabel("Y:"))
        self.crop_y_spin = QSpinBox()
        self.crop_y_spin.setMaximum(9999)
        crop_row1.addWidget(self.crop_y_spin)
        crop_layout.addLayout(crop_row1)
        
        crop_row2 = QHBoxLayout()
        crop_row2.addWidget(QLabel("Width:"))
        self.crop_width_spin = QSpinBox()
        self.crop_width_spin.setMaximum(9999)
        crop_row2.addWidget(self.crop_width_spin)
        crop_row2.addWidget(QLabel("Height:"))
        self.crop_height_spin = QSpinBox()
        self.crop_height_spin.setMaximum(9999)
        crop_row2.addWidget(self.crop_height_spin)
        crop_layout.addLayout(crop_row2)
        
        crop_group.setLayout(crop_layout)
        layout.addWidget(crop_group)
        
        # Watermark control
        watermark_group = QGroupBox("Watermark")
        watermark_layout = QVBoxLayout()
        
        # Watermark type
        type_layout = QHBoxLayout()
        self.watermark_none_radio = QRadioButton("None")
        self.watermark_text_radio = QRadioButton("Text")
        self.watermark_image_radio = QRadioButton("Image")
        self.watermark_none_radio.setChecked(True)
        
        self.watermark_group_buttons = QButtonGroup()
        self.watermark_group_buttons.addButton(self.watermark_none_radio, 0)
        self.watermark_group_buttons.addButton(self.watermark_text_radio, 1)
        self.watermark_group_buttons.addButton(self.watermark_image_radio, 2)
        
        type_layout.addWidget(self.watermark_none_radio)
        type_layout.addWidget(self.watermark_text_radio)
        type_layout.addWidget(self.watermark_image_radio)
        watermark_layout.addLayout(type_layout)
        
        # Text watermark
        self.watermark_text_edit = QLineEdit()
        self.watermark_text_edit.setPlaceholderText("Watermark text")
        self.watermark_text_edit.setEnabled(False)
        watermark_layout.addWidget(self.watermark_text_edit)
        
        # Image watermark
        image_layout = QHBoxLayout()
        self.watermark_image_edit = QLineEdit()
        self.watermark_image_edit.setPlaceholderText("Watermark image path")
        self.watermark_image_edit.setEnabled(False)
        self.watermark_image_btn = QPushButton("Browse...")
        self.watermark_image_btn.setEnabled(False)
        self.watermark_image_btn.clicked.connect(self._browse_watermark_image)
        image_layout.addWidget(self.watermark_image_edit)
        image_layout.addWidget(self.watermark_image_btn)
        watermark_layout.addLayout(image_layout)
        
        # Position
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Position X:"))
        self.watermark_x_spin = QSpinBox()
        self.watermark_x_spin.setMaximum(9999)
        self.watermark_x_spin.setValue(10)
        pos_layout.addWidget(self.watermark_x_spin)
        pos_layout.addWidget(QLabel("Y:"))
        self.watermark_y_spin = QSpinBox()
        self.watermark_y_spin.setMaximum(9999)
        self.watermark_y_spin.setValue(10)
        pos_layout.addWidget(self.watermark_y_spin)
        watermark_layout.addLayout(pos_layout)
        
        # Connect watermark type changes
        self.watermark_group_buttons.buttonClicked.connect(self._on_watermark_type_changed)
        
        watermark_group.setLayout(watermark_layout)
        layout.addWidget(watermark_group)
        
        # Subtitle control
        subtitle_group = QGroupBox("Subtitle")
        subtitle_layout = QHBoxLayout()
        
        self.subtitle_edit = QLineEdit()
        self.subtitle_edit.setPlaceholderText("Subtitle file (.srt)")
        self.subtitle_btn = QPushButton("Browse...")
        self.subtitle_btn.clicked.connect(self._browse_subtitle)
        
        subtitle_layout.addWidget(self.subtitle_edit)
        subtitle_layout.addWidget(self.subtitle_btn)
        subtitle_group.setLayout(subtitle_layout)
        layout.addWidget(subtitle_group)
        
        layout.addStretch()
    
    def _update_speed_label(self, value):
        """Update speed label."""
        speed = value / 100.0
        self.speed_label.setText(f"{speed:.1f}x")
        self.params_changed.emit()
    
    def _update_volume_label(self, value):
        """Update volume label."""
        self.volume_label.setText(f"{value}%")
        self.params_changed.emit()
    
    def _on_watermark_type_changed(self):
        """Handle watermark type change."""
        is_text = self.watermark_text_radio.isChecked()
        is_image = self.watermark_image_radio.isChecked()
        
        self.watermark_text_edit.setEnabled(is_text)
        self.watermark_image_edit.setEnabled(is_image)
        self.watermark_image_btn.setEnabled(is_image)
        
        self.params_changed.emit()
    
    def _browse_watermark_image(self):
        """Browse for watermark image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Watermark Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.watermark_image_edit.setText(file_path)
            self.params_changed.emit()
    
    def _browse_subtitle(self):
        """Browse for subtitle file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Subtitle File",
            "",
            "Subtitle Files (*.srt)"
        )
        if file_path:
            self.subtitle_edit.setText(file_path)
            self.params_changed.emit()
    
    # Getters
    
    def get_speed(self) -> float:
        """Get speed value."""
        return self.speed_slider.value() / 100.0
    
    def get_volume(self) -> float:
        """Get volume value."""
        return self.volume_slider.value() / 100.0
    
    def get_trim_start(self) -> float:
        """Get cut from start (seconds)."""
        return self.trim_start_spin.value()
    
    def get_cut_from_end(self) -> float:
        """Get cut from end (seconds)."""
        return self.trim_end_spin.value()
    
    def get_scale(self):
        """Get scale resolution."""
        scale_text = self.scale_combo.currentText()
        if scale_text == "Original":
            return None
        
        # Extract resolution from text
        resolution_map = {
            "1920x1080 (1080p)": (1920, 1080),
            "1280x720 (720p)": (1280, 720),
            "854x480 (480p)": (854, 480),
            "640x360 (360p)": (640, 360)
        }
        return resolution_map.get(scale_text)
    
    def get_crop(self):
        """Get crop region."""
        if self.crop_width_spin.value() == 0 or self.crop_height_spin.value() == 0:
            return None
        return (
            self.crop_x_spin.value(),
            self.crop_y_spin.value(),
            self.crop_width_spin.value(),
            self.crop_height_spin.value()
        )
    
    def get_watermark_type(self) -> WatermarkType:
        """Get watermark type."""
        if self.watermark_text_radio.isChecked():
            return WatermarkType.TEXT
        elif self.watermark_image_radio.isChecked():
            return WatermarkType.IMAGE
        else:
            return WatermarkType.NONE
    
    def get_watermark_text(self) -> str:
        """Get watermark text."""
        return self.watermark_text_edit.text().strip()
    
    def get_watermark_image(self) -> Path:
        """Get watermark image path."""
        path_str = self.watermark_image_edit.text().strip()
        return Path(path_str) if path_str else None
    
    def get_watermark_position(self):
        """Get watermark position."""
        return (self.watermark_x_spin.value(), self.watermark_y_spin.value())
    
    def get_subtitle_file(self) -> Path:
        """Get subtitle file path."""
        path_str = self.subtitle_edit.text().strip()
        return Path(path_str) if path_str else None
