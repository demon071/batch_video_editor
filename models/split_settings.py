"""Split settings data model."""
from dataclasses import dataclass
from typing import Optional
from .enums import SplitMode


@dataclass
class SplitSettings:
    """
    Settings for video splitting.
    
    Attributes:
        enabled: Whether splitting is enabled
        mode: Split mode (BY_COUNT or BY_DURATION)
        num_parts: Number of parts to split into (for BY_COUNT mode)
        duration_seconds: Duration of each part in seconds (for BY_DURATION mode)
        output_pattern: Output filename pattern
        use_stream_copy: Use stream copy (no re-encoding) for fast splitting
        keyframe_accurate: Cut at keyframes only to prevent corruption
    """
    
    enabled: bool = False
    mode: SplitMode = SplitMode.DISABLED
    
    # For BY_COUNT mode
    num_parts: int = 2  # Split into N parts (2-100)
    
    # For BY_DURATION mode
    duration_seconds: float = 300.0  # Split every X seconds (default: 5 minutes)
    
    # Output settings
    output_pattern: str = "{name}_part{num:03d}{ext}"
    use_stream_copy: bool = True  # No re-encoding
    keyframe_accurate: bool = True  # Cut at keyframes only
    
    # Post-split processing
    process_split_parts: bool = False  # Apply effects to each split part
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'enabled': self.enabled,
            'mode': self.mode.value if isinstance(self.mode, SplitMode) else self.mode,
            'num_parts': self.num_parts,
            'duration_seconds': self.duration_seconds,
            'output_pattern': self.output_pattern,
            'use_stream_copy': self.use_stream_copy,
            'keyframe_accurate': self.keyframe_accurate,
            'process_split_parts': self.process_split_parts,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SplitSettings':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary with split settings
            
        Returns:
            SplitSettings instance
        """
        mode = data.get('mode', SplitMode.DISABLED.value)
        if isinstance(mode, str):
            mode = SplitMode(mode)
        
        return cls(
            enabled=data.get('enabled', False),
            mode=mode,
            num_parts=data.get('num_parts', 2),
            duration_seconds=data.get('duration_seconds', 300.0),
            output_pattern=data.get('output_pattern', "{name}_part{num:03d}{ext}"),
            use_stream_copy=data.get('use_stream_copy', True),
            keyframe_accurate=data.get('keyframe_accurate', True),
            process_split_parts=data.get('process_split_parts', False),
        )
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate split settings.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.enabled:
            return True, ""
        
        if self.mode == SplitMode.DISABLED:
            return True, ""
        
        if self.mode == SplitMode.BY_COUNT:
            if self.num_parts < 2:
                return False, "Number of parts must be at least 2"
            if self.num_parts > 100:
                return False, "Number of parts cannot exceed 100"
        
        elif self.mode == SplitMode.BY_DURATION:
            if self.duration_seconds <= 0:
                return False, "Duration must be greater than 0"
            if self.duration_seconds < 1.0:
                return False, "Duration must be at least 1 second"
        
        if not self.output_pattern:
            return False, "Output pattern cannot be empty"
        
        # Check if pattern contains required placeholders
        if '{num' not in self.output_pattern:
            return False, "Output pattern must contain {num} or {num:03d} placeholder"
        
        return True, ""
