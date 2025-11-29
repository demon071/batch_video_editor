"""
Properties Panel Widget - Right panel for settings and parameters.

Refactored to use QTabWidget for better organization:
- General: Processing parameters (Speed, Volume, Trim, etc.) + Codec settings
- Overlays: Text, Image, Video overlays
- Advanced: Intro, Outro, Stacking, Split, Background
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QPushButton, 
                             QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

from config.settings import AppConfig
from ui.widgets import (ProcessingParamsPanel, CodecSettingsPanel,
                        TextOverlayPanel, ImageOverlayPanel, VideoOverlayPanel,
                        IntroVideoPanel, OutroVideoPanel, StackingPanel,
                        BackgroundFramePanel, SplitPanel)


class PropertiesPanelWidget(QWidget):
    """
    Properties panel with Tabbed layout.
    
    Signals:
        settings_changed: Emitted when any setting changes
        apply_to_all_requested: Emitted when apply to all button is clicked
    """
    
    # Signals
    settings_changed = pyqtSignal()
    apply_to_all_requested = pyqtSignal()
    
    def __init__(self, config: AppConfig = None, parent=None):
        super().__init__(parent)
        self.config = config or AppConfig()
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #e0e0e0;
                padding: 8px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #4a4a4a;
            }
        """)
        
        # 1. General Tab
        self.general_tab = QWidget()
        general_layout = QVBoxLayout(self.general_tab)
        general_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area for General tab
        general_scroll = QScrollArea()
        general_scroll.setWidgetResizable(True)
        general_scroll.setFrameShape(QScrollArea.NoFrame)
        
        # Create content widget for scroll area
        general_content = QWidget()
        general_content_layout = QVBoxLayout(general_content)
        general_content_layout.setContentsMargins(5, 5, 5, 5)
        general_content_layout.setSpacing(10)
        
        general_content_layout.setSpacing(10)
        
        self.params_panel = ProcessingParamsPanel(self.config)
        general_content_layout.addWidget(self.params_panel)
        
        self.codec_panel = CodecSettingsPanel()
        general_content_layout.addWidget(self.codec_panel)
        
        general_content_layout.addStretch()
        
        general_scroll.setWidget(general_content)
        general_layout.addWidget(general_scroll)
        self.tabs.addTab(self.general_tab, "General")
        
        # 2. Overlays Tab
        self.overlays_tab = QWidget()
        overlays_layout = QVBoxLayout(self.overlays_tab)
        overlays_layout.setContentsMargins(0, 0, 0, 0)
        
        overlays_scroll = QScrollArea()
        overlays_scroll.setWidgetResizable(True)
        overlays_scroll.setFrameShape(QScrollArea.NoFrame)
        
        overlays_content = QWidget()
        overlays_content_layout = QVBoxLayout(overlays_content)
        overlays_content_layout.setContentsMargins(5, 5, 5, 5)
        overlays_content_layout.setSpacing(10)
        
        self.text_overlay_panel = TextOverlayPanel()
        self.image_overlay_panel = ImageOverlayPanel()
        self.video_overlay_panel = VideoOverlayPanel()
        
        overlays_content_layout.addWidget(self.text_overlay_panel)
        overlays_content_layout.addWidget(self.image_overlay_panel)
        overlays_content_layout.addWidget(self.video_overlay_panel)
        overlays_content_layout.addStretch()
        
        overlays_scroll.setWidget(overlays_content)
        overlays_layout.addWidget(overlays_scroll)
        self.tabs.addTab(self.overlays_tab, "Overlays")
        
        # 3. Advanced Tab
        self.advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(self.advanced_tab)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        
        advanced_scroll = QScrollArea()
        advanced_scroll.setWidgetResizable(True)
        advanced_scroll.setFrameShape(QScrollArea.NoFrame)
        
        advanced_content = QWidget()
        advanced_content_layout = QVBoxLayout(advanced_content)
        advanced_content_layout.setContentsMargins(5, 5, 5, 5)
        advanced_content_layout.setSpacing(10)
        
        self.intro_video_panel = IntroVideoPanel()
        self.outro_video_panel = OutroVideoPanel()
        self.stacking_panel = StackingPanel()
        self.background_frame_panel = BackgroundFramePanel()
        self.split_panel = SplitPanel()
        
        advanced_content_layout.addWidget(self.intro_video_panel)
        advanced_content_layout.addWidget(self.outro_video_panel)
        advanced_content_layout.addWidget(self.stacking_panel)
        advanced_content_layout.addWidget(self.background_frame_panel)
        advanced_content_layout.addWidget(self.split_panel)
        advanced_content_layout.addStretch()
        
        advanced_scroll.setWidget(advanced_content)
        advanced_layout.addWidget(advanced_scroll)
        self.tabs.addTab(self.advanced_tab, "Advanced")
        
        layout.addWidget(self.tabs)
        
        # Apply buttons area
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(5, 5, 5, 5)
        
        self.apply_all_btn = QPushButton("Apply to All Tasks")
        self.apply_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.apply_all_btn.clicked.connect(self.apply_to_all_requested.emit)
        button_layout.addWidget(self.apply_all_btn)
        
        layout.addLayout(button_layout)
    
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
