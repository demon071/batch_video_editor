"""Codec settings panel widget."""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QComboBox, QSlider, QLineEdit, QRadioButton,
                             QButtonGroup, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal
from models.enums import VideoCodec, Preset, QualityMode


class CodecSettingsPanel(QWidget):
    """
    Panel for configuring codec and quality settings.
    
    Includes codec selection, quality mode (CRF/Bitrate), and preset.
    """
    
    # Signals
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize codec settings panel."""
        super().__init__(parent)
        self.gpu_available = False
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Codec selection
        codec_group = QGroupBox("Video Codec")
        codec_layout = QVBoxLayout()
        
        codec_select_layout = QHBoxLayout()
        codec_select_layout.addWidget(QLabel("Codec:"))
        self.codec_combo = QComboBox()
        self.codec_combo.addItem("H.264 (CPU)", VideoCodec.H264)
        self.codec_combo.addItem("HEVC/H.265 (CPU)", VideoCodec.HEVC)
        self.codec_combo.addItem("H.264 NVENC (GPU)", VideoCodec.H264_NVENC)
        self.codec_combo.addItem("HEVC NVENC (GPU)", VideoCodec.HEVC_NVENC)
        self.codec_combo.currentIndexChanged.connect(self.settings_changed.emit)
        codec_select_layout.addWidget(self.codec_combo)
        codec_layout.addLayout(codec_select_layout)
        
        # GPU indicator
        self.gpu_label = QLabel("GPU: Not detected")
        self.gpu_label.setStyleSheet("color: gray;")
        codec_layout.addWidget(self.gpu_label)
        
        # GPU Decoding Checkbox
        from PyQt5.QtWidgets import QCheckBox
        self.gpu_decoding_check = QCheckBox("Use GPU for Input Decoding (Experimental)")
        self.gpu_decoding_check.setToolTip("Enable hardware acceleration for reading input files.\n"
                                         "Warning: May fail with newer codecs (AV1) on older GPUs.\n"
                                         "Leave unchecked for maximum compatibility.")
        self.gpu_decoding_check.setEnabled(False)
        self.gpu_decoding_check.stateChanged.connect(self.settings_changed.emit)
        codec_layout.addWidget(self.gpu_decoding_check)
        
        codec_group.setLayout(codec_layout)
        layout.addWidget(codec_group)
        
        # Quality mode
        quality_group = QGroupBox("Quality Settings")
        quality_layout = QVBoxLayout()
        
        # Mode selection
        mode_layout = QHBoxLayout()
        self.crf_radio = QRadioButton("CRF (Constant Quality)")
        self.bitrate_radio = QRadioButton("Bitrate (Target Size)")
        self.crf_radio.setChecked(True)
        
        self.quality_mode_group = QButtonGroup()
        self.quality_mode_group.addButton(self.crf_radio, 0)
        self.quality_mode_group.addButton(self.bitrate_radio, 1)
        self.quality_mode_group.buttonClicked.connect(self._on_quality_mode_changed)
        
        mode_layout.addWidget(self.crf_radio)
        mode_layout.addWidget(self.bitrate_radio)
        quality_layout.addLayout(mode_layout)
        
        # CRF slider
        crf_layout = QVBoxLayout()
        crf_label_layout = QHBoxLayout()
        crf_label_layout.addWidget(QLabel("CRF Value:"))
        self.crf_value_label = QLabel("23")
        crf_label_layout.addWidget(self.crf_value_label)
        crf_label_layout.addStretch()
        crf_layout.addLayout(crf_label_layout)
        
        self.crf_slider = QSlider(Qt.Horizontal)
        self.crf_slider.setMinimum(0)
        self.crf_slider.setMaximum(51)
        self.crf_slider.setValue(23)
        self.crf_slider.setTickPosition(QSlider.TicksBelow)
        self.crf_slider.setTickInterval(5)
        self.crf_slider.valueChanged.connect(self._update_crf_label)
        crf_layout.addWidget(self.crf_slider)
        
        crf_hint = QLabel("Lower = better quality, larger file")
        crf_hint.setStyleSheet("color: gray; font-size: 9pt;")
        crf_layout.addWidget(crf_hint)
        
        quality_layout.addLayout(crf_layout)
        
        # Bitrate input
        bitrate_layout = QHBoxLayout()
        bitrate_layout.addWidget(QLabel("Bitrate:"))
        self.bitrate_edit = QLineEdit()
        self.bitrate_edit.setText("5M")
        self.bitrate_edit.setPlaceholderText("e.g., 5M, 1000k")
        self.bitrate_edit.setEnabled(False)
        self.bitrate_edit.textChanged.connect(self.settings_changed.emit)
        bitrate_layout.addWidget(self.bitrate_edit)
        quality_layout.addLayout(bitrate_layout)
        
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)
        
        # Preset
        preset_group = QGroupBox("Encoding Preset")
        preset_layout = QVBoxLayout()
        
        preset_select_layout = QHBoxLayout()
        preset_select_layout.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        for preset in [Preset.ULTRAFAST, Preset.SUPERFAST, Preset.VERYFAST, 
                      Preset.FASTER, Preset.FAST, Preset.MEDIUM, 
                      Preset.SLOW, Preset.SLOWER, Preset.VERYSLOW]:
            self.preset_combo.addItem(str(preset), preset)
        self.preset_combo.setCurrentIndex(5)  # MEDIUM
        self.preset_combo.currentIndexChanged.connect(self.settings_changed.emit)
        preset_select_layout.addWidget(self.preset_combo)
        preset_layout.addLayout(preset_select_layout)
        
        preset_hint = QLabel("Faster = quicker encoding, lower quality/larger file")
        preset_hint.setStyleSheet("color: gray; font-size: 9pt;")
        preset_layout.addWidget(preset_hint)
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        layout.addStretch()
    
    def set_gpu_available(self, available: bool):
        """
        Set GPU availability status.
        
        Args:
            available: True if GPU encoding is available
        """
        self.gpu_available = available
        
        if available:
            self.gpu_label.setText("GPU: Available ✓")
            self.gpu_label.setStyleSheet("color: green;")
            self.gpu_decoding_check.setEnabled(True)
        else:
            self.gpu_label.setText("GPU: Not available")
            self.gpu_label.setStyleSheet("color: red;")
            self.gpu_decoding_check.setEnabled(False)
            self.gpu_decoding_check.setChecked(False)
            
            # Disable GPU codec options
            for i in range(self.codec_combo.count()):
                codec = self.codec_combo.itemData(i)
                if codec.is_gpu:
                    # Can't disable items in QComboBox, so we'll just show warning
                    pass
    
    def _update_crf_label(self, value):
        """Update CRF value label."""
        self.crf_value_label.setText(str(value))
        self.settings_changed.emit()
    
    def _on_quality_mode_changed(self):
        """Handle quality mode change."""
        is_crf = self.crf_radio.isChecked()
        
        self.crf_slider.setEnabled(is_crf)
        self.bitrate_edit.setEnabled(not is_crf)
        
        self.settings_changed.emit()
    
    # Getters
    
    def get_codec(self) -> VideoCodec:
        """Get selected codec."""
        return self.codec_combo.currentData()
    
    def get_quality_mode(self) -> QualityMode:
        """Get quality mode."""
        return QualityMode.CRF if self.crf_radio.isChecked() else QualityMode.BITRATE
    
    def get_crf(self) -> int:
        """Get CRF value."""
        return self.crf_slider.value()
    
    def get_bitrate(self) -> str:
        """Get bitrate value."""
        return self.bitrate_edit.text().strip()
    
    def get_preset(self) -> Preset:
        """Get encoding preset."""
        return self.preset_combo.currentData()
        
    def get_gpu_decoding(self) -> bool:
        """Get GPU decoding status."""
        return self.gpu_decoding_check.isChecked()
    
    # Setters
    
    def set_codec(self, codec: VideoCodec):
        """Set codec."""
        for i in range(self.codec_combo.count()):
            if self.codec_combo.itemData(i) == codec:
                self.codec_combo.setCurrentIndex(i)
                break
                
    def set_gpu_decoding(self, enabled: bool):
        """Set GPU decoding status."""
        if self.gpu_available:
            self.gpu_decoding_check.setChecked(enabled)
    
    def set_quality_mode(self, mode: QualityMode):
        """Set quality mode."""
        if mode == QualityMode.CRF:
            self.crf_radio.setChecked(True)
        else:
            self.bitrate_radio.setChecked(True)
        self._on_quality_mode_changed()
    
    def set_crf(self, value: int):
        """Set CRF value."""
        self.crf_slider.setValue(value)
    
    def set_bitrate(self, value: str):
        """Set bitrate value."""
        self.bitrate_edit.setText(value)
    
    def set_preset(self, preset: Preset):
        """Set encoding preset."""
        for i in range(self.preset_combo.count()):
            if self.preset_combo.itemData(i) == preset:
                self.preset_combo.setCurrentIndex(i)
                break
