"""Media overlay panel widget."""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QCheckBox, QComboBox, QLabel, QPushButton, QLineEdit,
                             QSlider, QSpinBox, QFileDialog, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from pathlib import Path
from models.media_overlay import MediaOverlay
from models.enums import OverlayType, OverlayPosition


class MediaOverlayPanel(QWidget):
    """
    Panel for configuring media overlay settings.
    
    Features collapsible UI that expands when enabled.
    Supports image overlay, video overlay, intro/outro videos.
    """
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize media overlay panel."""
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main group box
        self.group_box = QGroupBox("Media Overlay")
        group_layout = QVBoxLayout()
        
        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable Media Overlay")
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        group_layout.addWidget(self.enable_checkbox)
        
        # Options container (collapsible)
        self.options_container = QWidget()
        self.options_container.setVisible(False)
        options_layout = QVBoxLayout(self.options_container)
        options_layout.setContentsMargins(10, 5, 0, 0)
        
        # Build options UI
        self._build_options_ui(options_layout)
        
        group_layout.addWidget(self.options_container)
        self.group_box.setLayout(group_layout)
        layout.addWidget(self.group_box)
    
    def _build_options_ui(self, layout):
        """Build the options UI inside container."""
        
        # Overlay Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Overlay Type:"))
        self.type_combo = QComboBox()
        for overlay_type in OverlayType:
            self.type_combo.addItem(str(overlay_type), overlay_type)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # Media Source Group
        source_group = QGroupBox("Media Source")
        source_layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("No file selected")
        self.file_edit.setReadOnly(True)
        file_layout.addWidget(QLabel("File:"))
        file_layout.addWidget(self.file_edit)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_media)
        file_layout.addWidget(self.browse_btn)
        source_layout.addLayout(file_layout)
        
        # Preview (optional - just a label for now)
        self.preview_label = QLabel("Preview: (not available)")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(60)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
        source_layout.addWidget(self.preview_label)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Position & Size Group (for IMAGE and VIDEO only)
        self.position_size_group = QGroupBox("Position & Size")
        pos_size_layout = QVBoxLayout()
        
        # Position preset
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Position:"))
        self.position_combo = QComboBox()
        for position in OverlayPosition:
            self.position_combo.addItem(str(position), position)
        self.position_combo.currentIndexChanged.connect(self._on_position_changed)
        pos_layout.addWidget(self.position_combo)
        pos_layout.addStretch()
        pos_size_layout.addLayout(pos_layout)
        
        # Custom X/Y (only visible when CUSTOM selected)
        self.custom_pos_widget = QWidget()
        custom_pos_layout = QHBoxLayout(self.custom_pos_widget)
        custom_pos_layout.setContentsMargins(0, 0, 0, 0)
        custom_pos_layout.addWidget(QLabel("X:"))
        self.custom_x_spin = QSpinBox()
        self.custom_x_spin.setRange(0, 9999)
        self.custom_x_spin.setValue(10)
        custom_pos_layout.addWidget(self.custom_x_spin)
        custom_pos_layout.addWidget(QLabel("Y:"))
        self.custom_y_spin = QSpinBox()
        self.custom_y_spin.setRange(0, 9999)
        self.custom_y_spin.setValue(10)
        custom_pos_layout.addWidget(self.custom_y_spin)
        custom_pos_layout.addStretch()
        self.custom_pos_widget.setVisible(False)
        pos_size_layout.addWidget(self.custom_pos_widget)
        
        # Scale
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Scale:"))
        scale_layout.addWidget(QLabel("W:"))
        self.scale_width_spin = QSpinBox()
        self.scale_width_spin.setRange(0, 9999)
        self.scale_width_spin.setValue(0)
        self.scale_width_spin.setSpecialValueText("Auto")
        scale_layout.addWidget(self.scale_width_spin)
        scale_layout.addWidget(QLabel("H:"))
        self.scale_height_spin = QSpinBox()
        self.scale_height_spin.setRange(0, 9999)
        self.scale_height_spin.setValue(0)
        self.scale_height_spin.setSpecialValueText("Auto")
        scale_layout.addWidget(self.scale_height_spin)
        scale_layout.addStretch()
        pos_size_layout.addLayout(scale_layout)
        
        self.position_size_group.setLayout(pos_size_layout)
        layout.addWidget(self.position_size_group)
        
        # Appearance Group (for IMAGE and VIDEO only)
        self.appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout()
        
        # Opacity slider
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
        appearance_layout.addLayout(opacity_layout)
        
        self.appearance_group.setLayout(appearance_layout)
        layout.addWidget(self.appearance_group)
        
        # Timing Group (for VIDEO overlay only)
        self.timing_group = QGroupBox("Timing")
        timing_layout = QVBoxLayout()
        
        # Start time
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start Time (s):"))
        self.start_time_spin = QSpinBox()
        self.start_time_spin.setRange(0, 99999)
        self.start_time_spin.setValue(0)
        start_layout.addWidget(self.start_time_spin)
        start_layout.addStretch()
        timing_layout.addLayout(start_layout)
        
        # Duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (s):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 99999)
        self.duration_spin.setValue(0)
        self.duration_spin.setSpecialValueText("Until End")
        duration_layout.addWidget(self.duration_spin)
        duration_layout.addStretch()
        timing_layout.addLayout(duration_layout)
        
        # Loop checkbox
        self.loop_checkbox = QCheckBox("Loop overlay video")
        timing_layout.addWidget(self.loop_checkbox)
        
        self.timing_group.setLayout(timing_layout)
        self.timing_group.setVisible(False)
        layout.addWidget(self.timing_group)
        
        # Intro/Outro Group (for INTRO and OUTRO only)
        self.intro_outro_group = QGroupBox("Intro/Outro Settings")
        intro_outro_layout = QVBoxLayout()
        
        # Fade duration
        fade_layout = QHBoxLayout()
        fade_layout.addWidget(QLabel("Fade Duration (s):"))
        self.fade_spin = QSpinBox()
        self.fade_spin.setRange(0, 10)
        self.fade_spin.setValue(0)
        self.fade_spin.setSingleStep(1)
        fade_layout.addWidget(self.fade_spin)
        fade_layout.addStretch()
        intro_outro_layout.addLayout(fade_layout)
        
        # Audio mix
        self.mix_audio_checkbox = QCheckBox("Mix audio with main video")
        self.mix_audio_checkbox.setChecked(True)
        intro_outro_layout.addWidget(self.mix_audio_checkbox)
        
        self.intro_outro_group.setLayout(intro_outro_layout)
        self.intro_outro_group.setVisible(False)
        layout.addWidget(self.intro_outro_group)
        
        # Initial state
        self._on_type_changed(0)
    
    def _on_enable_changed(self, state):
        """Handle enable checkbox state change."""
        enabled = state == Qt.Checked
        self.options_container.setVisible(enabled)
        self.settings_changed.emit()
    
    def _on_type_changed(self, index):
        """Handle overlay type change."""
        overlay_type = self.type_combo.currentData()
        
        # Show/hide groups based on type
        is_image_or_video = overlay_type in [OverlayType.IMAGE, OverlayType.VIDEO]
        is_video = overlay_type == OverlayType.VIDEO
        is_intro_outro = overlay_type in [OverlayType.INTRO, OverlayType.OUTRO]
        
        self.position_size_group.setVisible(is_image_or_video)
        self.appearance_group.setVisible(is_image_or_video)
        self.timing_group.setVisible(is_video)
        self.intro_outro_group.setVisible(is_intro_outro)
        
        self.settings_changed.emit()
    
    def _on_position_changed(self, index):
        """Handle position preset change."""
        position = self.position_combo.currentData()
        self.custom_pos_widget.setVisible(position == OverlayPosition.CUSTOM)
        self.settings_changed.emit()
    
    def _on_opacity_changed(self, value):
        """Handle opacity slider change."""
        self.opacity_label.setText(f"{value}%")
        self.settings_changed.emit()
    
    def _browse_media(self):
        """Browse for media file."""
        overlay_type = self.type_combo.currentData()
        
        if overlay_type == OverlayType.IMAGE:
            file_filter = "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        else:
            file_filter = "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Media File",
            "",
            file_filter
        )
        
        if file_path:
            self.file_edit.setText(file_path)
            self._update_preview(file_path)
            self.settings_changed.emit()
    
    def _update_preview(self, file_path):
        """Update preview thumbnail (simple implementation)."""
        path = Path(file_path)
        if path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            # Show image preview
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(200, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled)
                self.preview_label.setText("")
            else:
                self.preview_label.setText(f"Preview: {path.name}")
        else:
            # Video - just show filename
            self.preview_label.setText(f"Preview: {path.name}")
    
    def get_media_overlay(self) -> MediaOverlay:
        """
        Get current media overlay settings.
        
        Returns:
            MediaOverlay object with current settings
        """
        media_path = None
        if self.file_edit.text():
            media_path = Path(self.file_edit.text())
        
        return MediaOverlay(
            enabled=self.enable_checkbox.isChecked(),
            overlay_type=self.type_combo.currentData(),
            media_path=media_path,
            position_preset=self.position_combo.currentData(),
            custom_x=self.custom_x_spin.value(),
            custom_y=self.custom_y_spin.value(),
            scale_width=self.scale_width_spin.value() if self.scale_width_spin.value() > 0 else None,
            scale_height=self.scale_height_spin.value() if self.scale_height_spin.value() > 0 else None,
            opacity=self.opacity_slider.value() / 100.0,
            start_time=self.start_time_spin.value(),
            duration=self.duration_spin.value() if self.duration_spin.value() > 0 else None,
            loop=self.loop_checkbox.isChecked(),
            fade_duration=self.fade_spin.value(),
            mix_audio=self.mix_audio_checkbox.isChecked(),
        )
    
    def set_media_overlay(self, overlay: MediaOverlay):
        """
        Set media overlay settings.
        
        Args:
            overlay: MediaOverlay object to load
        """
        self.enable_checkbox.setChecked(overlay.enabled)
        
        # Set type
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == overlay.overlay_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        # Set media path
        if overlay.media_path:
            self.file_edit.setText(str(overlay.media_path))
            self._update_preview(str(overlay.media_path))
        
        # Set position
        for i in range(self.position_combo.count()):
            if self.position_combo.itemData(i) == overlay.position_preset:
                self.position_combo.setCurrentIndex(i)
                break
        
        self.custom_x_spin.setValue(overlay.custom_x)
        self.custom_y_spin.setValue(overlay.custom_y)
        
        # Set size
        self.scale_width_spin.setValue(overlay.scale_width if overlay.scale_width else 0)
        self.scale_height_spin.setValue(overlay.scale_height if overlay.scale_height else 0)
        
        # Set opacity
        self.opacity_slider.setValue(int(overlay.opacity * 100))
        
        # Set timing
        self.start_time_spin.setValue(int(overlay.start_time))
        self.duration_spin.setValue(int(overlay.duration) if overlay.duration else 0)
        self.loop_checkbox.setChecked(overlay.loop)
        
        # Set intro/outro
        self.fade_spin.setValue(int(overlay.fade_duration))
        self.mix_audio_checkbox.setChecked(overlay.mix_audio)
