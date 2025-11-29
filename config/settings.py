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
        'use_gpu_decoding': False,
        'window_geometry': None,
        'whisper_cli_path': '',
        'whisper_model': 'small',
        'whisper_language': 'auto',
        'whisper_device': 'cpu',
        'whisper_threads': 4,
        'whisper_word_count': 1,
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
        
    @property
    def use_gpu_decoding(self) -> bool:
        """Get GPU decoding preference."""
        return self.get('use_gpu_decoding', False)
    
    @use_gpu_decoding.setter
    def use_gpu_decoding(self, value: bool):
        """Set GPU decoding preference."""
        self.set('use_gpu_decoding', value)

    # Whisper Settings
    
    @property
    def whisper_cli_path(self) -> str:
        """Get Whisper CLI path."""
        return self.get('whisper_cli_path', '')
    
    @whisper_cli_path.setter
    def whisper_cli_path(self, value: str):
        """Set Whisper CLI path."""
        self.set('whisper_cli_path', value)
        
    @property
    def whisper_model(self) -> str:
        """Get Whisper model."""
        return self.get('whisper_model', 'small')
    
    @whisper_model.setter
    def whisper_model(self, value: str):
        """Set Whisper model."""
        self.set('whisper_model', value)
        
    @property
    def whisper_language(self) -> str:
        """Get Whisper language."""
        return self.get('whisper_language', 'auto')
    
    @whisper_language.setter
    def whisper_language(self, value: str):
        """Set Whisper language."""
        self.set('whisper_language', value)
        
    @property
    def whisper_device(self) -> str:
        """Get Whisper device."""
        return self.get('whisper_device', 'cpu')
    
    @whisper_device.setter
    def whisper_device(self, value: str):
        """Set Whisper device."""
        self.set('whisper_device', value)
        
    @property
    def whisper_threads(self) -> int:
        """Get Whisper threads."""
        return self.get('whisper_threads', 4)
    
    @whisper_threads.setter
    def whisper_threads(self, value: int):
        """Set Whisper threads."""
        self.set('whisper_threads', value)
        
    @property
    def whisper_word_count(self) -> int:
        """Get Whisper max word count per segment."""
        return self.get('whisper_word_count', 1)
    
    @whisper_word_count.setter
    def whisper_word_count(self, value: int):
        """Set Whisper max word count per segment."""
        self.set('whisper_word_count', value)
