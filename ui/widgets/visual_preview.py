"""
Visual Preview Widget for interactive layer editing.

Allows users to drag-and-drop layers to position them visually.
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect, QSize
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap, QMouseEvent, QResizeEvent
from typing import List, Optional, Tuple
from models.layer import Layer, LayerType, TextLayerProperties, ImageLayerProperties, VideoLayerProperties

class VisualPreviewWidget(QWidget):
    """
    Widget for displaying video frame and handling interactive layer editing.
    """
    
    # Signals
    layer_moved = pyqtSignal(str, tuple)  # layer_id, (x, y)
    layer_selected = pyqtSignal(str)      # layer_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(400, 225)
        
        # State
        self.current_frame: Optional[QPixmap] = None
        self.layers: List[Layer] = []
        self.selected_layer_id: Optional[str] = None
        self.video_size = QSize(1920, 1080)  # Default, will update
        
        # Dragging state
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.layer_start_pos = QPoint()
        self.hovered_layer_id: Optional[str] = None
        
        # Visual settings
        self.handle_color = QColor(0, 120, 215)  # Windows blue
        self.hover_color = QColor(0, 120, 215, 100)
        self.selection_pen = QPen(self.handle_color, 2, Qt.SolidLine)
        self.hover_pen = QPen(self.handle_color, 1, Qt.DashLine)
        
    def set_frame(self, frame: QPixmap, video_size: Tuple[int, int]):
        """Update the displayed frame."""
        self.current_frame = frame
        self.video_size = QSize(video_size[0], video_size[1])
        self.update()
        
    def set_layers(self, layers: List[Layer]):
        """Update the list of layers."""
        # Sort by z-index (highest last)
        self.layers = sorted(layers, key=lambda l: l.z_index)
        self.update()
        
    def set_selected_layer(self, layer_id: Optional[str]):
        """Set the currently selected layer."""
        self.selected_layer_id = layer_id
        self.update()
        
    def paintEvent(self, event):
        """Draw the frame and layer overlays."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Draw background/frame
        if self.current_frame:
            # Scale frame to fit widget while maintaining aspect ratio
            scaled_frame = self.current_frame.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            # Center the frame
            x = (self.width() - scaled_frame.width()) // 2
            y = (self.height() - scaled_frame.height()) // 2
            
            painter.drawPixmap(x, y, scaled_frame)
            
            # Store display rect for coordinate mapping
            self.display_rect = QRect(x, y, scaled_frame.width(), scaled_frame.height())
        else:
            # Draw placeholder
            painter.fillRect(self.rect(), Qt.black)
            painter.setPen(Qt.white)
            painter.drawText(self.rect(), Qt.AlignCenter, "No Preview Available")
            self.display_rect = self.rect()
            return
            
        # 2. Draw layer overlays
        for layer in self.layers:
            if not layer.enabled:
                continue
                
            # Calculate layer rect in screen coordinates
            rect = self._get_layer_rect(layer)
            if not rect:
                continue
                
            # Draw selection/hover indicators
            if layer.id == self.selected_layer_id:
                painter.setPen(self.selection_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)
                
                # Draw handles (corners)
                handle_size = 6
                painter.setBrush(self.handle_color)
                painter.setPen(Qt.NoPen)
                painter.drawRect(rect.left() - handle_size//2, rect.top() - handle_size//2, handle_size, handle_size)
                painter.drawRect(rect.right() - handle_size//2, rect.top() - handle_size//2, handle_size, handle_size)
                painter.drawRect(rect.left() - handle_size//2, rect.bottom() - handle_size//2, handle_size, handle_size)
                painter.drawRect(rect.right() - handle_size//2, rect.bottom() - handle_size//2, handle_size, handle_size)
                
            elif layer.id == self.hovered_layer_id:
                painter.setPen(self.hover_pen)
                painter.setBrush(self.hover_color)
                painter.drawRect(rect)
                
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for selection and dragging."""
        if not self.display_rect:
            return
            
        pos = event.pos()
        
        # Check if clicking on a layer (iterate reverse to check top-most first)
        clicked_layer = None
        for layer in reversed(self.layers):
            if not layer.enabled:
                continue
            rect = self._get_layer_rect(layer)
            if rect and rect.contains(pos):
                clicked_layer = layer
                break
        
        if clicked_layer:
            self.selected_layer_id = clicked_layer.id
            self.layer_selected.emit(clicked_layer.id)
            
            # Start dragging
            self.is_dragging = True
            self.drag_start_pos = pos
            self.layer_start_pos = QPoint(clicked_layer.position[0], clicked_layer.position[1])
            
            self.update()
        else:
            # Deselect if clicking empty space
            self.selected_layer_id = None
            self.layer_selected.emit("")
            self.update()
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for dragging and hover effects."""
        pos = event.pos()
        
        if self.is_dragging and self.selected_layer_id:
            # Calculate delta
            delta = pos - self.drag_start_pos
            
            # Map delta to video coordinates
            scale_x = self.video_size.width() / self.display_rect.width()
            scale_y = self.video_size.height() / self.display_rect.height()
            
            video_delta_x = int(delta.x() * scale_x)
            video_delta_y = int(delta.y() * scale_y)
            
            # Update layer position
            new_x = self.layer_start_pos.x() + video_delta_x
            new_y = self.layer_start_pos.y() + video_delta_y
            
            # Find the layer object
            for layer in self.layers:
                if layer.id == self.selected_layer_id:
                    layer.position = (new_x, new_y)
                    self.layer_moved.emit(layer.id, (new_x, new_y))
                    break
            
            self.update()
            
        else:
            # Handle hover effect
            hovered = None
            for layer in reversed(self.layers):
                if not layer.enabled:
                    continue
                rect = self._get_layer_rect(layer)
                if rect and rect.contains(pos):
                    hovered = layer.id
                    break
            
            if hovered != self.hovered_layer_id:
                self.hovered_layer_id = hovered
                self.update()
                
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stop dragging."""
        self.is_dragging = False
        
    def _get_layer_rect(self, layer: Layer) -> Optional[QRect]:
        """Calculate screen rectangle for a layer."""
        if not self.display_rect:
            return None
            
        # Calculate scale factors
        scale_x = self.display_rect.width() / self.video_size.width()
        scale_y = self.display_rect.height() / self.video_size.height()
        
        # Layer position in screen coords (relative to display_rect)
        x = int(layer.position[0] * scale_x) + self.display_rect.x()
        y = int(layer.position[1] * scale_y) + self.display_rect.y()
        
        # Estimate size based on layer type
        width, height = 100, 50  # Default
        
        if layer.type == LayerType.TEXT:
            # Estimate text size (rough approximation)
            font_size = layer.properties.get(TextLayerProperties.FONT_SIZE, 48)
            text = layer.properties.get(TextLayerProperties.TEXT, "Text")
            # Scale font size visually
            display_font_size = int(font_size * scale_y)
            width = len(text) * display_font_size * 0.6  # Approx width
            height = display_font_size * 1.2
            
        elif layer.type == LayerType.IMAGE:
            # Use actual image size if available, or default
            # For now, use a fixed size or try to get from properties if we stored it
            # Ideally we should store width/height in properties
            width = 200 * scale_x
            height = 150 * scale_y
            
        elif layer.type == LayerType.VIDEO:
            width = 300 * scale_x
            height = 169 * scale_y
            
        return QRect(int(x), int(y), int(width), int(height))
