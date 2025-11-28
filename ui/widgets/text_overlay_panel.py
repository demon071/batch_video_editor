"""Text overlay panel widget with collapsible design."""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QTextEdit, QComboBox, QSpinBox, QPushButton,
                             QCheckBox, QSlider, QColorDialog, QFontComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from pathlib import Path

from models.text_settings import TextSettings
from models.enums import TextPosition
from utils.font_utils import get_system_fonts, get_default_font


class TextOverlayPanel(QWidget):
    """Panel for configuring text overlay settings with collapsible design."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.system_fonts = []
        self._init_ui()
        self._load_system_fonts()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Group box
        self.group_box = QGroupBox("Text Overlay")
        group_layout = QVBoxLayout()
        
        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable Text Overlay")
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        group_layout.addWidget(self.enable_checkbox)
        
        # Options container (collapsible)
        self.options_container = QWidget()
        self.options_container.setVisible(False)
        options_layout = QVBoxLayout(self.options_container)
        options_layout.setContentsMargins(10, 5, 0, 0)
        
        # Text input
        text_label = QLabel("Text:")
        options_layout.addWidget(text_label)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter text to overlay...")
        self.text_edit.setMaximumHeight(80)
        options_layout.addWidget(self.text_edit)
        
        # Font settings
        font_group = QGroupBox("Font")
        font_layout = QVBoxLayout()
        
        # Font family
        font_family_layout = QHBoxLayout()
        font_family_layout.addWidget(QLabel("Font:"))
        self.font_combo = QFontComboBox()
        font_family_layout.addWidget(self.font_combo)
        font_layout.addLayout(font_family_layout)
        
        # Font size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 200)
        self.font_size_spin.setValue(48)
        size_layout.addWidget(self.font_size_spin)
        size_layout.addStretch()
        font_layout.addLayout(size_layout)
        
        # Font style
        style_layout = QHBoxLayout()
        self.bold_checkbox = QCheckBox("Bold")
        self.italic_checkbox = QCheckBox("Italic")
        style_layout.addWidget(self.bold_checkbox)
        style_layout.addWidget(self.italic_checkbox)
        style_layout.addStretch()
        font_layout.addLayout(style_layout)
        
        font_group.setLayout(font_layout)
        options_layout.addWidget(font_group)
        
        # Color settings
        color_group = QGroupBox("Colors")
        color_layout = QVBoxLayout()
        
        # Text color
        text_color_layout = QHBoxLayout()
        text_color_layout.addWidget(QLabel("Text:"))
        self.text_color_btn = QPushButton()
        self.text_color_btn.setFixedSize(50, 25)
        self.text_color_btn.setStyleSheet("background-color: white;")
        self.text_color_btn.clicked.connect(self._choose_text_color)
        self.text_color = QColor(255, 255, 255)
        text_color_layout.addWidget(self.text_color_btn)
        text_color_layout.addStretch()
        color_layout.addLayout(text_color_layout)
        
        # Border
        self.border_checkbox = QCheckBox("Enable Border")
        color_layout.addWidget(self.border_checkbox)
        
        border_layout = QHBoxLayout()
        border_layout.addWidget(QLabel("Border:"))
        self.border_color_btn = QPushButton()
        self.border_color_btn.setFixedSize(50, 25)
        self.border_color_btn.setStyleSheet("background-color: black;")
        self.border_color_btn.clicked.connect(self._choose_border_color)
        self.border_color = QColor(0, 0, 0)
        border_layout.addWidget(self.border_color_btn)
        border_layout.addWidget(QLabel("Width:"))
        self.border_width_spin = QSpinBox()
        self.border_width_spin.setRange(1, 10)
        self.border_width_spin.setValue(2)
        border_layout.addWidget(self.border_width_spin)
        border_layout.addStretch()
        color_layout.addLayout(border_layout)
        
        # Background
        self.background_checkbox = QCheckBox("Enable Background")
        color_layout.addWidget(self.background_checkbox)
        
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background:"))
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(50, 25)
        self.bg_color_btn.setStyleSheet("background-color: rgba(0,0,0,128);")
        self.bg_color_btn.clicked.connect(self._choose_bg_color)
        self.bg_color = QColor(0, 0, 0, 128)
        bg_layout.addWidget(self.bg_color_btn)
        bg_layout.addStretch()
        color_layout.addLayout(bg_layout)
        
        color_group.setLayout(color_layout)
        options_layout.addWidget(color_group)
        
        # Position settings
        position_group = QGroupBox("Position")
        position_layout = QVBoxLayout()
        
        # Position preset
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        self.position_combo = QComboBox()
        for position in TextPosition:
            self.position_combo.addItem(str(position), position)
        self.position_combo.currentIndexChanged.connect(self._on_position_changed)
        preset_layout.addWidget(self.position_combo)
        preset_layout.addStretch()
        position_layout.addLayout(preset_layout)
        
        # Custom position
        self.custom_position_widget = QWidget()
        custom_layout = QHBoxLayout(self.custom_position_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.addWidget(QLabel("X:"))
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 9999)
        self.x_spin.setValue(10)
        custom_layout.addWidget(self.x_spin)
        custom_layout.addWidget(QLabel("Y:"))
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 9999)
        self.y_spin.setValue(10)
        custom_layout.addWidget(self.y_spin)
        custom_layout.addStretch()
        self.custom_position_widget.setVisible(False)
        position_layout.addWidget(self.custom_position_widget)
        
        position_group.setLayout(position_layout)
        options_layout.addWidget(position_group)
        
        # Timing
        timing_group = QGroupBox("Timing")
        timing_layout = QVBoxLayout()
        
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start (s):"))
        self.start_time_spin = QSpinBox()
        self.start_time_spin.setRange(0, 99999)
        self.start_time_spin.setValue(0)
        start_layout.addWidget(self.start_time_spin)
        start_layout.addWidget(QLabel("End (s):"))
        self.end_time_spin = QSpinBox()
        self.end_time_spin.setRange(0, 99999)
        self.end_time_spin.setValue(0)
        self.end_time_spin.setSpecialValueText("Until End")
        start_layout.addWidget(self.end_time_spin)
        start_layout.addStretch()
        timing_layout.addLayout(start_layout)
        
        timing_group.setLayout(timing_layout)
        options_layout.addWidget(timing_group)
        
        # Close options container
        group_layout.addWidget(self.options_container)
        self.group_box.setLayout(group_layout)
        layout.addWidget(self.group_box)
    
    
    def _load_system_fonts(self):
        """Load system fonts."""
        # QFontComboBox already loads system fonts automatically
        # We just need to store the font list for path lookup
        try:
            self.system_fonts = get_system_fonts()
            # print(f"DEBUG: Loaded {len(self.system_fonts)} fonts from system")
        except Exception as e:
            print(f"Error loading fonts: {e}")
            self.system_fonts = []
    
    def _on_enable_changed(self, state):
        """Handle enable checkbox change."""
        self.options_container.setVisible(state == Qt.Checked)
        self.settings_changed.emit()
    
    def _on_position_changed(self, index):
        """Handle position change."""
        position = self.position_combo.currentData()
        self.custom_position_widget.setVisible(position == TextPosition.CUSTOM)
        self.settings_changed.emit()
    
    def _choose_text_color(self):
        """Choose text color."""
        color = QColorDialog.getColor(self.text_color, self, "Choose Text Color")
        if color.isValid():
            self.text_color = color
            self.text_color_btn.setStyleSheet(f"background-color: {color.name()};")
            self.settings_changed.emit()
    
    def _choose_border_color(self):
        """Choose border color."""
        color = QColorDialog.getColor(self.border_color, self, "Choose Border Color")
        if color.isValid():
            self.border_color = color
            self.border_color_btn.setStyleSheet(f"background-color: {color.name()};")
            self.settings_changed.emit()
    
    def _choose_bg_color(self):
        """Choose background color."""
        color = QColorDialog.getColor(self.bg_color, self, "Choose Background Color")
        if color.isValid():
            self.bg_color = color
            self.bg_color_btn.setStyleSheet(f"background-color: rgba({color.red()},{color.green()},{color.blue()},{color.alpha()});")
            self.settings_changed.emit()
    
    def get_text_settings(self) -> TextSettings:
        """Get current text settings."""
        # Get font path from selected font family
        from PyQt5.QtGui import QFontDatabase
        
        font_path = None
        current_font = self.font_combo.currentText()
        
        # DEBUG: Show font selection
        # print(f"\nDEBUG: Font selection in text overlay panel")
        # print(f"  Selected font family: '{current_font}'")
        
        # Try to find font file path using QFontDatabase
        font_db = QFontDatabase()
        
        # Get the actual font file path from Windows registry or system
        # For now, try to match with system_fonts list using case-insensitive search
        for font_name, path in self.system_fonts:
            # Try exact match first
            if font_name == current_font:
                font_path = Path(path)
                # print(f"  Found exact match: {font_path}")
                break
            # Try case-insensitive partial match
            if current_font.lower().replace(' ', '') in font_name.lower().replace(' ', ''):
                font_path = Path(path)
                # print(f"  Found partial match: {font_name} -> {font_path}")
                break
        
        if not font_path:
            # print(f"  WARNING: No matching font path found, will use default")
            pass
        
        return TextSettings(
            enabled=self.enable_checkbox.isChecked(),
            text=self.text_edit.toPlainText(),
            font_family=current_font,
            font_path=font_path,
            font_size=self.font_size_spin.value(),
            font_color=self.text_color.name(),
            bold=self.bold_checkbox.isChecked(),
            italic=self.italic_checkbox.isChecked(),
            outline_color=self.border_color.name(),
            outline_thickness=self.border_width_spin.value() if self.border_checkbox.isChecked() else 0,
            box_enabled=self.background_checkbox.isChecked(),
            box_color=self.bg_color.name(),
            box_opacity=self.bg_color.alpha() / 255.0,
            position_preset=self.position_combo.currentData(),
            position_x=self.x_spin.value(),
            position_y=self.y_spin.value(),
        )
    
    def set_text_settings(self, settings: TextSettings):
        """Load text settings into UI."""
        self.enable_checkbox.setChecked(settings.enabled)
        self.text_edit.setPlainText(settings.text)
        
        # Set font
        index = self.font_combo.findText(settings.font_family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        
        self.font_size_spin.setValue(settings.font_size)
        self.bold_checkbox.setChecked(settings.bold)
        self.italic_checkbox.setChecked(settings.italic)
        
        # Colors
        self.text_color = QColor(settings.font_color)
        self.text_color_btn.setStyleSheet(f"background-color: {settings.font_color};")
        
        self.border_checkbox.setChecked(settings.border_enabled)
        self.border_color = QColor(settings.border_color)
        self.border_color_btn.setStyleSheet(f"background-color: {settings.border_color};")
        self.border_width_spin.setValue(settings.border_width)
        
        self.background_checkbox.setChecked(settings.background_enabled)
        self.bg_color = QColor(settings.background_color)
        self.bg_color.setAlpha(int(settings.background_opacity * 255))
        self.bg_color_btn.setStyleSheet(f"background-color: {settings.background_color};")
        
        # Position
        for i in range(self.position_combo.count()):
            if self.position_combo.itemData(i) == settings.position:
                self.position_combo.setCurrentIndex(i)
                break
        
        self.x_spin.setValue(settings.custom_x)
        self.y_spin.setValue(settings.custom_y)
        
        # Timing
        self.start_time_spin.setValue(int(settings.start_time))
        if settings.end_time:
            self.end_time_spin.setValue(int(settings.end_time))
