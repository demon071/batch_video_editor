"""
Properties Panel Widget - Right panel for settings and parameters.

Displays collapsible sections for:
- Processing parameters
- Codec settings
- Text overlay
- Media overlays
- Advanced settings
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QGroupBox,
                             QPushButton, QLabel, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.widgets import (ProcessingParamsPanel, CodecSettingsPanel,
                        TextOverlayPanel, ImageOverlayPanel, VideoOverlayPanel,
                        IntroVideoPanel, OutroVideoPanel, StackingPanel,
                        BackgroundFramePanel, SplitPanel)


class CollapsibleSection(QWidget):
    """
    Custom collapsible section with a header button.
    Replaces QGroupBox to avoid double borders.
    """
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.is_expanded = True
        self._content_widget = None
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header button
        self.toggle_btn = QPushButton(f"▼ {title}")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                background-color: #3c3c3c;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:checked {
                background-color: #4a4a4a;
            }
        """)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False)
        self.toggle_btn.clicked.connect(self.toggle)
        self.main_layout.addWidget(self.toggle_btn)
        
        # Content container
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 5, 0, 5)
        self.main_layout.addWidget(self.content_area)
    
    def setContentWidget(self, widget: QWidget):
        """Set the content widget."""
        self._content_widget = widget
        self.content_layout.addWidget(widget)
    
    def toggle(self):
        """Toggle expansion state."""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.content_area.setVisible(True)
            self.toggle_btn.setText(self.toggle_btn.text().replace("▶", "▼"))
        else:
            self.content_area.setVisible(False)
            self.toggle_btn.setText(self.toggle_btn.text().replace("▼", "▶"))
            
    def setChecked(self, checked: bool):
        """Set expansion state (compatibility with QGroupBox)."""
        if self.is_expanded != checked:
            self.toggle()


class PropertiesPanelWidget(QWidget):
    """
    Properties panel with collapsible settings sections.
    
    Features:
    - Collapsible group boxes for each settings category
    - Scroll area for overflow
    - Apply settings buttons
    
    Signals:
        settings_changed: Emitted when any setting changes
    """
    
    # Signals
    settings_changed = pyqtSignal()
    apply_to_all_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        # Settings container
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(5)
        
        # Processing Parameters
        self.params_group = CollapsibleSection("Processing Parameters")
        self.params_panel = ProcessingParamsPanel()
        self.params_group.setContentWidget(self.params_panel)
        settings_layout.addWidget(self.params_group)
        
        # Codec Settings
        self.codec_group = CollapsibleSection("Codec Settings")
        self.codec_panel = CodecSettingsPanel()
        self.codec_group.setContentWidget(self.codec_panel)
        settings_layout.addWidget(self.codec_group)
        
        # Text Overlay
        self.text_group = CollapsibleSection("Text Overlay")
        self.text_overlay_panel = TextOverlayPanel()
        self.text_group.setContentWidget(self.text_overlay_panel)
        self.text_group.setChecked(False)  # Collapsed by default
        settings_layout.addWidget(self.text_group)
        
        # Image Overlay
        self.image_group = CollapsibleSection("Image Overlay")
        self.image_overlay_panel = ImageOverlayPanel()
        self.image_group.setContentWidget(self.image_overlay_panel)
        self.image_group.setChecked(False)
        settings_layout.addWidget(self.image_group)
        
        # Video Overlay
        self.video_group = CollapsibleSection("Video Overlay")
        self.video_overlay_panel = VideoOverlayPanel()
        self.video_group.setContentWidget(self.video_overlay_panel)
        self.video_group.setChecked(False)
        settings_layout.addWidget(self.video_group)
        
        # Intro Video
        self.intro_group = CollapsibleSection("Intro Video")
        self.intro_video_panel = IntroVideoPanel()
        self.intro_group.setContentWidget(self.intro_video_panel)
        self.intro_group.setChecked(False)
        settings_layout.addWidget(self.intro_group)
        
        # Outro Video
        self.outro_group = CollapsibleSection("Outro Video")
        self.outro_video_panel = OutroVideoPanel()
        self.outro_group.setContentWidget(self.outro_video_panel)
        self.outro_group.setChecked(False)
        settings_layout.addWidget(self.outro_group)
        
        # Stacking
        self.stacking_group = CollapsibleSection("Video Stacking")
        self.stacking_panel = StackingPanel()
        self.stacking_group.setContentWidget(self.stacking_panel)
        self.stacking_group.setChecked(False)
        settings_layout.addWidget(self.stacking_group)
        
        # Background Frame
        self.background_group = CollapsibleSection("Background Frame")
        self.background_frame_panel = BackgroundFramePanel()
        self.background_group.setContentWidget(self.background_frame_panel)
        self.background_group.setChecked(False)
        settings_layout.addWidget(self.background_group)
        
        # Split
        self.split_group = CollapsibleSection("Split Video")
        self.split_panel = SplitPanel()
        self.split_group.setContentWidget(self.split_panel)
        self.split_group.setChecked(False)
        settings_layout.addWidget(self.split_group)
        
        settings_layout.addStretch()
        
        scroll.setWidget(settings_widget)
        layout.addWidget(scroll)
        
        # Apply buttons
        button_layout = QVBoxLayout()
        
        self.apply_all_btn = QPushButton("Apply to All Tasks")
        self.apply_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.apply_all_btn.clicked.connect(self.apply_to_all_requested.emit)
        button_layout.addWidget(self.apply_all_btn)
        
        layout.addLayout(button_layout)
        
        # Connect change signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect all panel signals to settings_changed."""
        # Note: Individual panels may not have change signals yet
        # This is a placeholder for future implementation
        pass
    
    # Expose panel getters for compatibility
    def get_params_panel(self):
        return self.params_panel
    
    def get_codec_panel(self):
        return self.codec_panel
    
    def get_text_overlay_panel(self):
        return self.text_overlay_panel
    
    def get_image_overlay_panel(self):
        return self.image_overlay_panel
    
    def get_video_overlay_panel(self):
        return self.video_overlay_panel
    
    def get_intro_video_panel(self):
        return self.intro_video_panel
    
    def get_outro_video_panel(self):
        return self.outro_video_panel
    
    def get_stacking_panel(self):
        return self.stacking_panel
    
    def get_background_frame_panel(self):
        return self.background_frame_panel
    
    def get_split_panel(self):
        return self.split_panel
