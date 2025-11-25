"""Video overlay panel widget."""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QCheckBox, QComboBox, QLabel, QPushButton, QLineEdit,
                             QSlider, QSpinBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path
from models.enums import OverlayPosition


class VideoOverlayPanel(QWidget):
    """Panel for configuring video overlay settings."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Group box
        self.group_box = QGroupBox("Video Overlay")
        group_layout = QVBoxLayout()
        
        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable Video Overlay")
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
        self.file_edit.setPlaceholderText("Select video file...")
        self.file_edit.setReadOnly(True)
        file_layout.addWidget(self.file_edit)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_btn)
        options_layout.addLayout(file_layout)
        
        # Position
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Position:"))
        self.position_combo = QComboBox()
        for position in OverlayPosition:
            self.position_combo.addItem(str(position), position)
        self.position_combo.currentIndexChanged.connect(self._on_position_changed)
        pos_layout.addWidget(self.position_combo)
        pos_layout.addStretch()
        options_layout.addLayout(pos_layout)
        
        # Custom X/Y
        self.custom_pos_widget = QWidget()
        custom_layout = QHBoxLayout(self.custom_pos_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.addWidget(QLabel("X:"))
        self.custom_x_spin = QSpinBox()
        self.custom_x_spin.setRange(0, 9999)
        self.custom_x_spin.setValue(10)
        custom_layout.addWidget(self.custom_x_spin)
        custom_layout.addWidget(QLabel("Y:"))
        self.custom_y_spin = QSpinBox()
        self.custom_y_spin.setRange(0, 9999)
        self.custom_y_spin.setValue(10)
        custom_layout.addWidget(self.custom_y_spin)
        custom_layout.addStretch()
        self.custom_pos_widget.setVisible(False)
        options_layout.addWidget(self.custom_pos_widget)
        
        # Scale
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Scale:"))
        scale_layout.addWidget(QLabel("W:"))
        self.scale_width_edit = QLineEdit()
        self.scale_width_edit.setPlaceholderText("Auto (e.g. 320 or iw/2)")
        scale_layout.addWidget(self.scale_width_edit)
        scale_layout.addWidget(QLabel("H:"))
        self.scale_height_edit = QLineEdit()
        self.scale_height_edit.setPlaceholderText("Auto (e.g. -1 or ih/2)")
        scale_layout.addWidget(self.scale_height_edit)
        scale_layout.addStretch()
        options_layout.addLayout(scale_layout)
        
        # Opacity
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("100%")
        self.opacity_label.setMinimumWidth(40)
        opacity_layout.addWidget(self.opacity_label)
        options_layout.addLayout(opacity_layout)
        
        # Timing
        timing_layout = QHBoxLayout()
        timing_layout.addWidget(QLabel("Start (s):"))
        self.start_time_spin = QSpinBox()
        self.start_time_spin.setRange(0, 99999)
        self.start_time_spin.setValue(0)
        timing_layout.addWidget(self.start_time_spin)
        timing_layout.addWidget(QLabel("Duration (s):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 99999)
        self.duration_spin.setValue(0)
        self.duration_spin.setSpecialValueText("Until End")
        timing_layout.addWidget(self.duration_spin)
        timing_layout.addStretch()
        options_layout.addLayout(timing_layout)
        
        # Loop
        self.loop_checkbox = QCheckBox("Loop overlay video")
        options_layout.addWidget(self.loop_checkbox)
        
        group_layout.addWidget(self.options_container)
        self.group_box.setLayout(group_layout)
        layout.addWidget(self.group_box)
    
    def _on_enable_changed(self, state):
        self.options_container.setVisible(state == Qt.Checked)
        self.settings_changed.emit()
    
    def _on_position_changed(self, index):
        position = self.position_combo.currentData()
        self.custom_pos_widget.setVisible(position == OverlayPosition.CUSTOM)
        self.settings_changed.emit()
    
    def _on_opacity_changed(self, value):
        self.opacity_label.setText(f"{value}%")
        self.settings_changed.emit()
    
    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm)"
        )
        if file_path:
            self.file_edit.setText(file_path)
            self.settings_changed.emit()
    
    def get_settings(self) -> dict:
        w_text = self.scale_width_edit.text().strip()
        h_text = self.scale_height_edit.text().strip()
        
        # Try to parse as int if possible, otherwise keep as string
        def parse_scale(val):
            if not val: return None
            try:
                return int(val)
            except ValueError:
                return val

        return {
            'enabled': self.enable_checkbox.isChecked(),
            'file_path': self.file_edit.text(),
            'position': self.position_combo.currentData(),
            'custom_x': self.custom_x_spin.value(),
            'custom_y': self.custom_y_spin.value(),
            'scale_width': parse_scale(w_text),
            'scale_height': parse_scale(h_text),
            'opacity': self.opacity_slider.value() / 100.0,
            'start_time': self.start_time_spin.value(),
            'duration': self.duration_spin.value() if self.duration_spin.value() > 0 else None,
            'loop': self.loop_checkbox.isChecked(),
        }
