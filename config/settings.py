"""Application configuration management."""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from models.enums import VideoCodec, Preset, QualityMode


class AppConfig:
    """
    Manages application configuration with JSON persistence.
    
    Stores user preferences and last-used settings.
    """
    
    DEFAULT_CONFIG = {
        'last_input_folder': '',
        'last_output_folder': '',
        'codec': 'H264',
        'quality_mode': 'CRF',
        'crf': 23,
        'bitrate': '5M',
        'preset': 'MEDIUM',
        'speed': 1.0,
        'volume': 1.0,
        'window_geometry': None,
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to config file (default: user home directory)
        """
        if config_path is None:
            # Store in user's home directory
            config_dir = Path.home() / '.batch_video_editor'
            config_dir.mkdir(exist_ok=True)
            self.config_path = config_dir / 'config.json'
        else:
            self.config_path = Path(config_path)
        
        self.config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self):
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}. Using defaults.")
    
    def save(self):
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value and save.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value
        self.save()
    
    # Convenience properties
    
    @property
    def last_input_folder(self) -> str:
        """Get last used input folder."""
        return self.get('last_input_folder', '')
    
    @last_input_folder.setter
    def last_input_folder(self, value: str):
        """Set last used input folder."""
        self.set('last_input_folder', value)
    
    @property
    def last_output_folder(self) -> str:
        """Get last used output folder."""
        return self.get('last_output_folder', '')
    
    @last_output_folder.setter
    def last_output_folder(self, value: str):
        """Set last used output folder."""
        self.set('last_output_folder', value)
    
    @property
    def codec(self) -> VideoCodec:
        """Get default codec."""
        codec_name = self.get('codec', 'H264')
        try:
            return VideoCodec[codec_name]
        except KeyError:
            return VideoCodec.H264
    
    @codec.setter
    def codec(self, value: VideoCodec):
        """Set default codec."""
        self.set('codec', value.name)
    
    @property
    def quality_mode(self) -> QualityMode:
        """Get default quality mode."""
        mode_name = self.get('quality_mode', 'CRF')
        try:
            return QualityMode[mode_name]
        except KeyError:
            return QualityMode.CRF
    
    @quality_mode.setter
    def quality_mode(self, value: QualityMode):
        """Set default quality mode."""
        self.set('quality_mode', value.name)
    
    @property
    def crf(self) -> int:
        """Get default CRF value."""
        return self.get('crf', 23)
    
    @crf.setter
    def crf(self, value: int):
        """Set default CRF value."""
        self.set('crf', value)
    
    @property
    def bitrate(self) -> str:
        """Get default bitrate."""
        return self.get('bitrate', '5M')
    
    @bitrate.setter
    def bitrate(self, value: str):
        """Set default bitrate."""
        self.set('bitrate', value)
    
    @property
    def preset(self) -> Preset:
        """Get default preset."""
        preset_name = self.get('preset', 'MEDIUM')
        try:
            return Preset[preset_name]
        except KeyError:
            return Preset.MEDIUM
    
    @preset.setter
    def preset(self, value: Preset):
        """Set default preset."""
        self.set('preset', value.name)
    
    @property
    def speed(self) -> float:
        """Get default speed."""
        return self.get('speed', 1.0)
    
    @speed.setter
    def speed(self, value: float):
        """Set default speed."""
        self.set('speed', value)
    
    @property
    def volume(self) -> float:
        """Get default volume."""
        return self.get('volume', 1.0)
    
    @volume.setter
    def volume(self, value: float):
        """Set default volume."""
        self.set('volume', value)
