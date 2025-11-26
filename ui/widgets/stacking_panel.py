"""
Stacking Panel Widget.

Provides UI for configuring video stacking (HStack/VStack).
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QRadioButton, QButtonGroup,
                             QGroupBox, QLineEdit, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path
from typing import Optional, Dict

class StackingPanel(QWidget):
    """Panel for configuring video stacking settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main Group Box
        self.group_box = QGroupBox("Video Stacking (HStack / VStack)")
        self.group_box.setCheckable(True)
        self.group_box.setChecked(False)
        group_layout = QVBoxLayout(self.group_box)
        
        # Stack Mode Selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Horizontal Stack (HStack)", "Vertical Stack (VStack)"])
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        group_layout.addLayout(mode_layout)
        
        # Source Type Selection
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Secondary Video Source:"))
        
        self.source_group = QButtonGroup(self)
        
        self.file_radio = QRadioButton("Single File")
        self.file_radio.setChecked(True)
        self.source_group.addButton(self.file_radio)
        source_layout.addWidget(self.file_radio)
        
        self.folder_radio = QRadioButton("Random from Folder")
        self.source_group.addButton(self.folder_radio)
        source_layout.addWidget(self.folder_radio)
        
        source_layout.addStretch()
        group_layout.addLayout(source_layout)
        
        # Path Selection
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select video file...")
        path_layout.addWidget(self.path_input)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(self.browse_btn)
        
        group_layout.addLayout(path_layout)
        
        # Connect signals
        self.source_group.buttonClicked.connect(self._on_source_type_changed)
        
        layout.addWidget(self.group_box)
        
    def _on_source_type_changed(self):
        """Handle source type change."""
        if self.file_radio.isChecked():
            self.path_input.setPlaceholderText("Select video file...")
        else:
            self.path_input.setPlaceholderText("Select folder containing videos...")
            
    def _browse_path(self):
        """Browse for file or folder."""
        if self.file_radio.isChecked():
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Secondary Video",
                "",
                "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v)"
            )
        else:
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Video Folder",
                ""
            )
            
        if path:
            self.path_input.setText(path)
            
    def get_settings(self) -> Optional[Dict]:
        """Get stacking settings."""
        if not self.group_box.isChecked():
            return None
            
        path_str = self.path_input.text().strip()
        if not path_str:
            return None
            
        return {
            'mode': 'hstack' if self.mode_combo.currentIndex() == 0 else 'vstack',
            'type': 'file' if self.file_radio.isChecked() else 'folder',
            'path': Path(path_str)
        }
