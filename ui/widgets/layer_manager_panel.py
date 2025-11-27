"""
Layer Manager Panel - Main UI for multi-layer overlay system.

Provides interface for adding, editing, reordering, and previewing layers.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem, QSlider,
                             QGroupBox, QSplitter, QAbstractItemView, QMessageBox,
                             QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from pathlib import Path
from typing import List, Optional
from models.layer import Layer, LayerType
from models.video_task import VideoTask
from utils.preview_renderer import PreviewRenderer


class LayerListItem(QListWidgetItem):
    """Custom list item for layers."""
    
    def __init__(self, layer: Layer):
        super().__init__()
        self.layer = layer
        self.update_text()
    
    def update_text(self):
        """Update display text based on layer properties."""
        enabled_icon = "☑" if self.layer.enabled else "☐"
        type_icon = {
            LayerType.TEXT: "📝",
            LayerType.IMAGE: "🖼️",
            LayerType.VIDEO: "🎬",
            LayerType.MAIN_VIDEO: "🎞️"
        }.get(self.layer.type, "❓")
        
        if self.layer.type == LayerType.MAIN_VIDEO:
            self.setText(f"{type_icon} {self.layer.name}")
            # Make Main Video not draggable
            self.setFlags(self.flags() & ~Qt.ItemIsDragEnabled)
        else:
            self.setText(f"{enabled_icon} {type_icon} [{self.layer.z_index}] {self.layer.name}")


class LayerManagerPanel(QWidget):
    """
    Panel for managing multiple overlay layers.
    
    Features:
    - Layer list with drag-drop reordering
    - Preview area showing composited result
    - Timeline scrubber for preview at different times
    - Add/Remove/Edit layer buttons
    - Layer properties panel
    """
    
    # Signals
    layers_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layers: List[Layer] = []
        self.video_task: Optional[VideoTask] = None
        self.preview_renderer = PreviewRenderer()
        self.current_timestamp = 0.0
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Layer Manager")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Main splitter (preview | layer list)
        splitter = QSplitter(Qt.Vertical)
        
        # 1. Top: Preview area
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview group
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Visual Preview Widget
        from ui.widgets.visual_preview import VisualPreviewWidget
        self.preview_widget = VisualPreviewWidget()
        self.preview_widget.layer_moved.connect(self._on_visual_layer_moved)
        self.preview_widget.layer_selected.connect(self._on_visual_layer_selected)
        preview_layout.addWidget(self.preview_widget)
        
        # Timeline scrubber
        timeline_layout = QHBoxLayout()
        timeline_layout.addWidget(QLabel("Timeline:"))
        
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(100)
        self.timeline_slider.setValue(0)
        self.timeline_slider.valueChanged.connect(self._on_timeline_changed)
        timeline_layout.addWidget(self.timeline_slider)
        
        self.time_label = QLabel("0.0s")
        timeline_layout.addWidget(self.time_label)
        
        preview_layout.addLayout(timeline_layout)
        
        # Refresh preview button
        self.refresh_btn = QPushButton("Refresh Preview")
        self.refresh_btn.clicked.connect(self._refresh_preview)
        preview_layout.addWidget(self.refresh_btn)
        
        top_layout.addWidget(preview_group)
        
        splitter.addWidget(top_widget)
        
        # 2. Bottom: Layer list and controls
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Layer list
        list_group = QGroupBox("Layers")
        list_layout = QVBoxLayout(list_group)
        
        self.layer_list = QListWidget()
        self.layer_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.layer_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.layer_list.itemSelectionChanged.connect(self._on_layer_selected)
        self.layer_list.model().rowsMoved.connect(self._on_layers_reordered)
        list_layout.addWidget(self.layer_list)
        
        # Add layer buttons
        add_buttons_layout = QHBoxLayout()
        
        self.add_text_btn = QPushButton("+ Text")
        self.add_text_btn.clicked.connect(lambda: self._add_layer(LayerType.TEXT))
        add_buttons_layout.addWidget(self.add_text_btn)
        
        self.add_image_btn = QPushButton("+ Image")
        self.add_image_btn.clicked.connect(lambda: self._add_layer(LayerType.IMAGE))
        add_buttons_layout.addWidget(self.add_image_btn)
        
        self.add_video_btn = QPushButton("+ Video")
        self.add_video_btn.clicked.connect(lambda: self._add_layer(LayerType.VIDEO))
        add_buttons_layout.addWidget(self.add_video_btn)
        
        list_layout.addLayout(add_buttons_layout)
        
        # Remove/Toggle buttons
        control_buttons_layout = QHBoxLayout()
        
        self.toggle_btn = QPushButton("Toggle Enable")
        self.toggle_btn.clicked.connect(self._toggle_selected_layer)
        control_buttons_layout.addWidget(self.toggle_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self._remove_selected_layer)
        control_buttons_layout.addWidget(self.remove_btn)
        
        list_layout.addLayout(control_buttons_layout)
        
        bottom_layout.addWidget(list_group)
        
        splitter.addWidget(bottom_widget)
        
        # Set splitter sizes (60% preview, 40% list)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
    
    def set_video_task(self, task: VideoTask):
        """
        Set the video task to manage layers for.
        
        Args:
            task: VideoTask to manage
        """
        self.video_task = task
        
        # Load existing layers or create empty list
        if task.layers:
            self.layers = task.layers
        else:
            self.layers = []
        
        # Update timeline slider max based on video duration
        if task.duration > 0:
            self.timeline_slider.setMaximum(int(task.duration * 10))  # 0.1s precision
        
        self._refresh_layer_list()
        self._refresh_preview()
    
    def get_layers(self) -> List[Layer]:
        """Get current list of layers."""
        return self.layers
    
    def _refresh_layer_list(self):
        """Refresh the layer list widget."""
        self.layer_list.clear()
        
        # Add overlays in reverse order (Top to Bottom)
        for layer in reversed(self.layers):
            item = LayerListItem(layer)
            self.layer_list.addItem(item)
            
            # Restore selection
            if self.preview_widget.selected_layer_id == layer.id:
                item.setSelected(True)
        
        # Add Main Video layer at the bottom
        main_video_layer = Layer(
            type=LayerType.MAIN_VIDEO,
            name="Main Video",
            z_index=-1,
            enabled=True
        )
        main_video_item = LayerListItem(main_video_layer)
        self.layer_list.addItem(main_video_item)
    
    def _add_layer(self, layer_type: LayerType):
        """Add a new layer of specified type."""
        # Calculate next z_index
        next_z = len(self.layers)
        
        # Create new layer with defaults
        new_layer = Layer(
            type=layer_type,
            z_index=next_z,
            name=f"{layer_type.value.capitalize()} {next_z + 1}",
            position=(10, 10 + next_z * 30),  # Offset each layer
        )
        
        # Add type-specific defaults and open dialog
        if layer_type == LayerType.TEXT:
            from ui.dialogs.layer_properties_dialog import TextLayerPropertiesDialog
            from models.layer import TextLayerProperties
            
            # Set default properties
            new_layer.properties = {
                TextLayerProperties.TEXT: "New Text",
                TextLayerProperties.FONT_SIZE: 48,
                TextLayerProperties.FONT_COLOR: "#FFFFFF",
                TextLayerProperties.BORDER_WIDTH: 2,
                TextLayerProperties.BORDER_COLOR: "#000000"
            }
            
            # Open properties dialog
            dialog = TextLayerPropertiesDialog(new_layer, self.video_task, self)
            if dialog.exec_() == TextLayerPropertiesDialog.Accepted:
                new_layer = dialog.get_layer()
            else:
                return  # User cancelled
                
        elif layer_type == LayerType.IMAGE:
            # Prompt for image file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Image",
                "",
                "Image Files (*.jpg *.jpeg *.png *.bmp *.gif)"
            )
            if not file_path:
                return  # User cancelled
            
            from models.layer import ImageLayerProperties
            new_layer.properties = {
                ImageLayerProperties.FILE_PATH: file_path,
                ImageLayerProperties.OPACITY: 1.0
            }
        elif layer_type == LayerType.VIDEO:
            # Prompt for video file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Video",
                "",
                "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v)"
            )
            if not file_path:
                return  # User cancelled
            
            from models.layer import VideoLayerProperties
            new_layer.properties = {
                VideoLayerProperties.FILE_PATH: file_path,
                VideoLayerProperties.OPACITY: 1.0,
                VideoLayerProperties.LOOP: False
            }
        
        self.layers.append(new_layer)
        self._refresh_layer_list()
        self._refresh_preview()
        self.layers_changed.emit()
    
    def _remove_selected_layer(self):
        """Remove the currently selected layer."""
        item = self.layer_list.currentItem()
        if not item or not isinstance(item, LayerListItem):
            return
            
        layer = item.layer
        
        # Cannot remove Main Video
        if layer.type == LayerType.MAIN_VIDEO:
            QMessageBox.warning(self, "Cannot Remove", "Cannot remove the Main Video layer.")
            return
        
        # Confirm removal
        reply = QMessageBox.question(
            self,
            "Remove Layer",
            f"Remove layer '{layer.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if layer in self.layers:
                self.layers.remove(layer)
                self._reindex_layers()
                self._refresh_layer_list()
                self._refresh_preview()
                self.layers_changed.emit()
    
    def _toggle_selected_layer(self):
        """Toggle enabled state of selected layer."""
        item = self.layer_list.currentItem()
        if not item or not isinstance(item, LayerListItem):
            return
            
        layer = item.layer
        
        # Cannot toggle Main Video (for now, or maybe allow it to hide video?)
        if layer.type == LayerType.MAIN_VIDEO:
            return
            
        layer.enabled = not layer.enabled
        item.update_text()
        
        self._refresh_preview()
        self.layers_changed.emit()
    
    def _on_layers_reordered(self):
        """Handle layer reordering via drag-drop."""
        # Rebuild layers list based on new order
        # List is Top (High Z) -> Bottom (Low Z)
        # self.layers should be Bottom (Low Z) -> Top (High Z)
        
        new_layers = []
        main_video_found = False
        
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if isinstance(item, LayerListItem):
                if item.layer.type == LayerType.MAIN_VIDEO:
                    main_video_found = True
                    continue
                new_layers.append(item.layer)
        
        # Reverse to get Z-index order (0 to N)
        self.layers = list(reversed(new_layers))
        self._reindex_layers()
        
        # If Main Video was moved from bottom, force refresh to put it back
        # Actually, if we just rebuild self.layers and refresh, it will be put back at bottom
        self._refresh_layer_list()
        self._refresh_preview()
        self.layers_changed.emit()
    
    def _reindex_layers(self):
        """Reindex all layers based on current order."""
        for i, layer in enumerate(self.layers):
            layer.z_index = i
    
    def _on_layer_selected(self):
        """Handle layer selection change in list."""
        item = self.layer_list.currentItem()
        if not item or not isinstance(item, LayerListItem):
            return
            
        layer = item.layer
        
        if layer.type == LayerType.MAIN_VIDEO:
            # Main Video selected
            self.preview_widget.set_selected_layer(None)
            # TODO: Signal to show main video settings
        else:
            # Overlay selected
            self.preview_widget.set_selected_layer(layer.id)
    
    def _on_visual_layer_selected(self, layer_id: str):
        """Handle layer selection in visual preview."""
        if not layer_id:
            self.layer_list.clearSelection()
            # Maybe select Main Video if nothing else selected?
            # For now just clear
            return
            
        # Find item with this layer id
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if isinstance(item, LayerListItem) and item.layer.id == layer_id:
                self.layer_list.setCurrentItem(item)
                break
    
    def _on_visual_layer_moved(self, layer_id: str, new_pos: tuple):
        """Handle layer movement in visual preview."""
        # Layer object is already updated by VisualPreviewWidget
        # Just emit change signal
        self.layers_changed.emit()
    
    def _on_timeline_changed(self, value):
        """Handle timeline slider change."""
        # Convert slider value to timestamp (0.1s precision)
        self.current_timestamp = value / 10.0
        self.time_label.setText(f"{self.current_timestamp:.1f}s")
        self._refresh_preview()
    
    def _refresh_preview(self):
        """Refresh the preview with current layers and timestamp."""
        if not self.video_task or not self.video_task.input_path:
            return
        
        if not Path(self.video_task.input_path).exists():
            # self.preview_label.setText("Video file not found") # Label removed
            return
        
        # Render preview
        frame = self.preview_renderer.render_preview(
            self.video_task.input_path,
            self.layers,
            self.current_timestamp,
            max_width=self.preview_widget.width(),
            max_height=self.preview_widget.height()
        )
        
        if frame:
            # Update visual preview widget
            resolution = self.video_task.original_resolution if self.video_task.original_resolution else (1920, 1080)
            self.preview_widget.set_frame(frame, resolution)
            self.preview_widget.set_layers(self.layers)
            
            # Maintain selection
            current_row = self.layer_list.currentRow()
            if current_row >= 0 and current_row < len(self.layers):
                self.preview_widget.set_selected_layer(self.layers[current_row].id)

