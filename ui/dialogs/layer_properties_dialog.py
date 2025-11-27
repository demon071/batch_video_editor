"""
Layer Properties Dialogs for editing layer settings.

Provides professional dialogs for editing text, image, and video layer properties
with live preview.
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
                             QComboBox, QGroupBox, QFormLayout, QColorDialog,
                             QFileDialog, QSlider, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPixmap
from pathlib import Path
from typing import Optional
from models.layer import Layer, LayerType, TextLayerProperties, ImageLayerProperties, VideoLayerProperties
from utils.preview_renderer import PreviewRenderer


class TextLayerPropertiesDialog(QDialog):
    """Dialog for editing text layer properties."""
    
    def __init__(self, layer: Optional[Layer] = None, video_task=None, parent=None):
        super().__init__(parent)
        self.layer = layer or Layer(type=LayerType.TEXT)
        self.video_task = video_task
        self.preview_renderer = PreviewRenderer() if video_task else None
        
        self._init_ui()
        self._load_layer_properties()
        
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Text Layer Properties")
        self.resize(600, 700)
        
        layout = QVBoxLayout(self)
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(self.layer.name)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Text Content
        text_group = QGroupBox("Text Content")
        text_layout = QVBoxLayout(text_group)
        
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Enter text here...")
        self.text_edit.textChanged.connect(self._on_property_changed)
        text_layout.addWidget(self.text_edit)
        
        layout.addWidget(text_group)
        
        # Font Settings
        font_group = QGroupBox("Font")
        font_layout = QFormLayout(font_group)
        
        # Font family (simplified - just show current or default)
        self.font_family_edit = QLineEdit("Arial")
        font_layout.addRow("Family:", self.font_family_edit)
        
        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 200)
        self.font_size_spin.setValue(48)
        self.font_size_spin.valueChanged.connect(self._on_property_changed)
        font_layout.addRow("Size:", self.font_size_spin)
        
        # Font color
        color_layout = QHBoxLayout()
        self.font_color_edit = QLineEdit("#FFFFFF")
        self.font_color_btn = QPushButton("🎨")
        self.font_color_btn.setMaximumWidth(40)
        self.font_color_btn.clicked.connect(self._choose_font_color)
        color_layout.addWidget(self.font_color_edit)
        color_layout.addWidget(self.font_color_btn)
        font_layout.addRow("Color:", color_layout)
        
        # Border
        self.border_width_spin = QSpinBox()
        self.border_width_spin.setRange(0, 20)
        self.border_width_spin.setValue(2)
        self.border_width_spin.valueChanged.connect(self._on_property_changed)
        font_layout.addRow("Border Width:", self.border_width_spin)
        
        border_color_layout = QHBoxLayout()
        self.border_color_edit = QLineEdit("#000000")
        self.border_color_btn = QPushButton("🎨")
        self.border_color_btn.setMaximumWidth(40)
        self.border_color_btn.clicked.connect(self._choose_border_color)
        border_color_layout.addWidget(self.border_color_edit)
        border_color_layout.addWidget(self.border_color_btn)
        font_layout.addRow("Border Color:", border_color_layout)
        
        layout.addWidget(font_group)
        
        # Position
        position_group = QGroupBox("Position")
        position_layout = QFormLayout(position_group)
        
        self.pos_x_spin = QSpinBox()
        self.pos_x_spin.setRange(0, 9999)
        self.pos_x_spin.setValue(10)
        self.pos_x_spin.valueChanged.connect(self._on_property_changed)
        position_layout.addRow("X:", self.pos_x_spin)
        
        self.pos_y_spin = QSpinBox()
        self.pos_y_spin.setRange(0, 9999)
        self.pos_y_spin.setValue(10)
        self.pos_y_spin.valueChanged.connect(self._on_property_changed)
        position_layout.addRow("Y:", self.pos_y_spin)
        
        layout.addWidget(position_group)
        
        # Timing
        timing_group = QGroupBox("Timing")
        timing_layout = QVBoxLayout(timing_group)
        
        self.always_visible_check = QCheckBox("Always visible")
        self.always_visible_check.setChecked(True)
        self.always_visible_check.toggled.connect(self._on_always_visible_toggled)
        timing_layout.addWidget(self.always_visible_check)
        
        custom_timing_layout = QFormLayout()
        
        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setRange(0, 9999)
        self.start_time_spin.setValue(0)
        self.start_time_spin.setSuffix(" s")
        self.start_time_spin.setEnabled(False)
        custom_timing_layout.addRow("Start:", self.start_time_spin)
        
        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setRange(0, 9999)
        self.end_time_spin.setValue(5)
        self.end_time_spin.setSuffix(" s")
        self.end_time_spin.setEnabled(False)
        custom_timing_layout.addRow("End:", self.end_time_spin)
        
        timing_layout.addLayout(custom_timing_layout)
        layout.addWidget(timing_group)
        
        # Preview
        if self.video_task:
            preview_group = QGroupBox("Preview")
            preview_layout = QVBoxLayout(preview_group)
            
            from ui.widgets.visual_preview import VisualPreviewWidget
            self.preview_widget = VisualPreviewWidget()
            self.preview_widget.layer_moved.connect(self._on_visual_layer_moved)
            preview_layout.addWidget(self.preview_widget)
            
            refresh_btn = QPushButton("Refresh Preview")
            refresh_btn.clicked.connect(self._refresh_preview)
            preview_layout.addWidget(refresh_btn)
            
            layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _load_layer_properties(self):
        """Load layer properties into UI."""
        if not self.layer.properties:
            return
        
        props = self.layer.properties
        
        # Text
        text = props.get(TextLayerProperties.TEXT, "")
        self.text_edit.setText(text)
        
        # Font
        font_size = props.get(TextLayerProperties.FONT_SIZE, 48)
        self.font_size_spin.setValue(font_size)
        
        font_color = props.get(TextLayerProperties.FONT_COLOR, "#FFFFFF")
        self.font_color_edit.setText(font_color)
        
        border_width = props.get(TextLayerProperties.BORDER_WIDTH, 2)
        self.border_width_spin.setValue(border_width)
        
        border_color = props.get(TextLayerProperties.BORDER_COLOR, "#000000")
        self.border_color_edit.setText(border_color)
        
        # Position
        if self.layer.position:
            self.pos_x_spin.setValue(self.layer.position[0])
            self.pos_y_spin.setValue(self.layer.position[1])
        
        # Timing
        if self.layer.start_time is not None or self.layer.end_time is not None:
            self.always_visible_check.setChecked(False)
            if self.layer.start_time is not None:
                self.start_time_spin.setValue(self.layer.start_time)
            if self.layer.end_time is not None:
                self.end_time_spin.setValue(self.layer.end_time)
                
        # Initial preview refresh
        if self.video_task:
            self._refresh_preview()
    
    def _on_visual_layer_moved(self, layer_id: str, new_pos: tuple):
        """Handle layer movement in visual preview."""
        self.pos_x_spin.blockSignals(True)
        self.pos_y_spin.blockSignals(True)
        self.pos_x_spin.setValue(new_pos[0])
        self.pos_y_spin.setValue(new_pos[1])
        self.pos_x_spin.blockSignals(False)
        self.pos_y_spin.blockSignals(False)
    
    def _on_always_visible_toggled(self, checked):
        """Handle always visible checkbox toggle."""
        self.start_time_spin.setEnabled(not checked)
        self.end_time_spin.setEnabled(not checked)
    
    def _choose_font_color(self):
        """Open color picker for font color."""
        current_color = QColor(self.font_color_edit.text())
        color = QColorDialog.getColor(current_color, self, "Choose Font Color")
        if color.isValid():
            self.font_color_edit.setText(color.name())
            self._on_property_changed()
    
    def _choose_border_color(self):
        """Open color picker for border color."""
        current_color = QColor(self.border_color_edit.text())
        color = QColorDialog.getColor(current_color, self, "Choose Border Color")
        if color.isValid():
            self.border_color_edit.setText(color.name())
            self._on_property_changed()
    
    def _on_property_changed(self):
        """Handle property change - update preview if available."""
        if self.video_task and self.preview_renderer:
            # Update the layer object with current UI values so preview is accurate
            self.get_layer()
            self._refresh_preview()
    
    def _refresh_preview(self):
        """Refresh preview with current settings."""
        if not self.video_task or not self.preview_renderer:
            return
        
        # Create temporary layer with current settings
        temp_layer = self.get_layer()
        
        # Render preview frame
        frame = self.preview_renderer.render_preview(
            self.video_task.input_path,
            [temp_layer], # Render only this layer
            0.0,  # Preview at start
            max_width=400,
            max_height=225
        )
        
        if frame:
            # Update visual preview widget
            self.preview_widget.set_frame(frame, (1920, 1080)) # TODO: Get actual video size
            self.preview_widget.set_layers([temp_layer])
            self.preview_widget.set_selected_layer(temp_layer.id)

    
    def get_layer(self) -> Layer:
        """Get layer with current dialog settings."""
        # Update layer properties
        self.layer.name = self.name_edit.text() or "Text Layer"
        self.layer.type = LayerType.TEXT
        self.layer.position = (self.pos_x_spin.value(), self.pos_y_spin.value())
        
        # Timing
        if self.always_visible_check.isChecked():
            self.layer.start_time = None
            self.layer.end_time = None
        else:
            self.layer.start_time = self.start_time_spin.value()
            self.layer.end_time = self.end_time_spin.value()
        
        # Properties
        self.layer.properties = {
            TextLayerProperties.TEXT: self.text_edit.text(),
            TextLayerProperties.FONT_SIZE: self.font_size_spin.value(),
            TextLayerProperties.FONT_COLOR: self.font_color_edit.text(),
            TextLayerProperties.BORDER_WIDTH: self.border_width_spin.value(),
            TextLayerProperties.BORDER_COLOR: self.border_color_edit.text(),
        }
        
        return self.layer
