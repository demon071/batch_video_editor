"""Split panel widget for video splitting settings."""
from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QCheckBox,
                             QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
                             QLineEdit, QTextEdit, QFormLayout)
from PyQt5.QtCore import pyqtSignal
from models.split_settings import SplitSettings
from models.enums import SplitMode


class SplitPanel(QGroupBox):
    """
    Panel for configuring video splitting settings.
    
    Supports:
    - Split by count (N equal parts)
    - Split by duration (every X seconds/minutes)
    - Output filename pattern customization
    - Stream copy and keyframe options
    """
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize split panel."""
        super().__init__("Video Splitting", parent)
        self._init_ui()
        self._connect_signals()
        self._update_ui_state()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable Video Splitting")
        self.enable_checkbox.setToolTip(
            "Split each video into multiple parts using fast stream copy"
        )
        layout.addWidget(self.enable_checkbox)
        
        # Form layout for settings
        form_layout = QFormLayout()
        
        # Split mode selector
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("By Count (N equal parts)", SplitMode.BY_COUNT)
        self.mode_combo.addItem("By Duration (every X seconds)", SplitMode.BY_DURATION)
        self.mode_combo.setToolTip("Choose how to split the video")
        form_layout.addRow("Split Mode:", self.mode_combo)
        
        # Number of parts (for BY_COUNT mode)
        self.num_parts_spin = QSpinBox()
        self.num_parts_spin.setRange(2, 100)
        self.num_parts_spin.setValue(3)
        self.num_parts_spin.setSuffix(" parts")
        self.num_parts_spin.setToolTip("Number of equal parts to split into (2-100)")
        form_layout.addRow("Number of Parts:", self.num_parts_spin)
        
        # Duration per part (for BY_DURATION mode)
        duration_layout = QHBoxLayout()
        
        self.duration_minutes_spin = QSpinBox()
        self.duration_minutes_spin.setRange(0, 999)
        self.duration_minutes_spin.setValue(5)
        self.duration_minutes_spin.setSuffix(" min")
        self.duration_minutes_spin.setToolTip("Minutes per segment")
        
        self.duration_seconds_spin = QSpinBox()
        self.duration_seconds_spin.setRange(0, 59)
        self.duration_seconds_spin.setValue(0)
        self.duration_seconds_spin.setSuffix(" sec")
        self.duration_seconds_spin.setToolTip("Seconds per segment")
        
        duration_layout.addWidget(self.duration_minutes_spin)
        duration_layout.addWidget(self.duration_seconds_spin)
        duration_layout.addStretch()
        
        form_layout.addRow("Duration per Part:", duration_layout)
        
        layout.addLayout(form_layout)
        
        # Options
        options_layout = QVBoxLayout()
        
        self.stream_copy_checkbox = QCheckBox("Use Stream Copy (fast, no re-encoding)")
        self.stream_copy_checkbox.setChecked(True)
        self.stream_copy_checkbox.setToolTip(
            "Copy video/audio streams without re-encoding for maximum speed.\n"
            "Recommended: Keep enabled for fast splitting."
        )
        options_layout.addWidget(self.stream_copy_checkbox)
        
        self.keyframe_checkbox = QCheckBox("Keyframe Accurate (prevent corruption)")
        self.keyframe_checkbox.setChecked(True)
        self.keyframe_checkbox.setToolTip(
            "Cut only at keyframes to prevent video corruption.\n"
            "May result in ±1-2 second variance in segment times."
        )
        options_layout.addWidget(self.keyframe_checkbox)
        
        self.process_parts_checkbox = QCheckBox("Process split parts with current settings")
        self.process_parts_checkbox.setChecked(False)
        self.process_parts_checkbox.setToolTip(
            "After splitting, automatically apply speed, crop, text overlay,\n"
            "and other effects to each split part.\n"
            "Intermediate split files will be auto-deleted after processing."
        )
        options_layout.addWidget(self.process_parts_checkbox)
        
        layout.addLayout(options_layout)
        
        # Output pattern
        pattern_layout = QFormLayout()
        
        self.pattern_edit = QLineEdit("{name}_part{num:03d}{ext}")
        self.pattern_edit.setToolTip(
            "Output filename pattern:\n"
            "{name} = original filename\n"
            "{num} = part number (1, 2, 3...)\n"
            "{num:03d} = zero-padded number (001, 002, 003...)\n"
            "{ext} = file extension"
        )
        pattern_layout.addRow("Output Pattern:", self.pattern_edit)
        
        layout.addLayout(pattern_layout)
        
        # Preview
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(80)
        self.preview_text.setStyleSheet(
            "QTextEdit { background-color: #f5f5f5; "
            "font-family: 'Consolas', 'Courier New', monospace; "
            "font-size: 9pt; }"
        )
        layout.addWidget(self.preview_text)
        
        self.setLayout(layout)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self.enable_checkbox.toggled.connect(self._on_enable_changed)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.num_parts_spin.valueChanged.connect(self._on_settings_changed)
        self.duration_minutes_spin.valueChanged.connect(self._on_settings_changed)
        self.duration_seconds_spin.valueChanged.connect(self._on_settings_changed)
        self.stream_copy_checkbox.toggled.connect(self._on_settings_changed)
        self.keyframe_checkbox.toggled.connect(self._on_settings_changed)
        self.process_parts_checkbox.toggled.connect(self._on_settings_changed)
        self.pattern_edit.textChanged.connect(self._on_settings_changed)
    
    def _on_enable_changed(self):
        """Handle enable checkbox change."""
        self._update_ui_state()
        self._on_settings_changed()
    
    def _on_mode_changed(self):
        """Handle split mode change."""
        self._update_ui_state()
        self._on_settings_changed()
    
    def _on_settings_changed(self):
        """Handle settings change."""
        self._update_preview()
        self.settings_changed.emit()
    
    def _update_ui_state(self):
        """Update UI state based on current settings."""
        enabled = self.enable_checkbox.isChecked()
        
        # Enable/disable all controls
        self.mode_combo.setEnabled(enabled)
        self.num_parts_spin.setEnabled(enabled)
        self.duration_minutes_spin.setEnabled(enabled)
        self.duration_seconds_spin.setEnabled(enabled)
        self.stream_copy_checkbox.setEnabled(enabled)
        self.keyframe_checkbox.setEnabled(enabled)
        self.pattern_edit.setEnabled(enabled)
        
        if enabled:
            # Show/hide controls based on mode
            mode = self.mode_combo.currentData()
            is_by_count = mode == SplitMode.BY_COUNT
            
            # Show/hide appropriate inputs
            self.num_parts_spin.setVisible(is_by_count)
            self.duration_minutes_spin.setVisible(not is_by_count)
            self.duration_seconds_spin.setVisible(not is_by_count)
        else:
            # When disabled, show all inputs
            self.num_parts_spin.setVisible(True)
            self.duration_minutes_spin.setVisible(True)
            self.duration_seconds_spin.setVisible(True)
        
        self._update_preview()
    
    def _update_preview(self):
        """Update output filename preview."""
        if not self.enable_checkbox.isChecked():
            self.preview_text.setPlainText("(Splitting disabled)")
            return
        
        mode = self.mode_combo.currentData()
        pattern = self.pattern_edit.text()
        
        # Generate preview
        preview_lines = []
        
        if mode == SplitMode.BY_COUNT:
            num_parts = self.num_parts_spin.value()
            preview_lines.append(f"Split into {num_parts} parts:\n")
            
            for i in range(1, min(num_parts + 1, 4)):  # Show max 3 examples
                filename = pattern.format(name="video", num=i, ext=".mp4")
                preview_lines.append(f"  video.mp4 → {filename}")
            
            if num_parts > 3:
                preview_lines.append(f"  ... ({num_parts - 3} more)")
        
        else:  # BY_DURATION
            minutes = self.duration_minutes_spin.value()
            seconds = self.duration_seconds_spin.value()
            total_seconds = minutes * 60 + seconds
            
            preview_lines.append(f"Split every {minutes}m {seconds}s:\n")
            
            for i in range(1, 4):  # Show 3 examples
                filename = pattern.format(name="video", num=i, ext=".mp4")
                preview_lines.append(f"  video.mp4 → {filename}")
            
            preview_lines.append("  ... (continues until end)")
        
        self.preview_text.setPlainText("\n".join(preview_lines))
    
    def get_settings(self) -> SplitSettings:
        """
        Get current split settings.
        
        Returns:
            SplitSettings instance
        """
        enabled = self.enable_checkbox.isChecked()
        mode = self.mode_combo.currentData() if enabled else SplitMode.DISABLED
        
        # Calculate duration in seconds
        duration_seconds = (
            self.duration_minutes_spin.value() * 60 +
            self.duration_seconds_spin.value()
        )
        
        return SplitSettings(
            enabled=enabled,
            mode=mode,
            num_parts=self.num_parts_spin.value(),
            duration_seconds=duration_seconds,
            output_pattern=self.pattern_edit.text(),
            use_stream_copy=self.stream_copy_checkbox.isChecked(),
            keyframe_accurate=self.keyframe_checkbox.isChecked(),
            process_split_parts=self.process_parts_checkbox.isChecked()
        )
    
    def set_settings(self, settings: SplitSettings):
        """
        Set split settings.
        
        Args:
            settings: SplitSettings to apply
        """
        # Block signals during update
        self.blockSignals(True)
        
        self.enable_checkbox.setChecked(settings.enabled)
        
        # Set mode
        for i in range(self.mode_combo.count()):
            if self.mode_combo.itemData(i) == settings.mode:
                self.mode_combo.setCurrentIndex(i)
                break
        
        self.num_parts_spin.setValue(settings.num_parts)
        
        # Set duration
        minutes = int(settings.duration_seconds // 60)
        seconds = int(settings.duration_seconds % 60)
        self.duration_minutes_spin.setValue(minutes)
        self.duration_seconds_spin.setValue(seconds)
        
        self.pattern_edit.setText(settings.output_pattern)
        self.stream_copy_checkbox.setChecked(settings.use_stream_copy)
        self.keyframe_checkbox.setChecked(settings.keyframe_accurate)
        self.process_parts_checkbox.setChecked(settings.process_split_parts)
        
        # Unblock signals and update UI
        self.blockSignals(False)
        self._update_ui_state()
        self._update_preview()
