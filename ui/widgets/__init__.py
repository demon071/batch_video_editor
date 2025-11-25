"""UI widgets package."""
from .task_table import TaskTableWidget
from .params_panel import ProcessingParamsPanel
from .codec_panel import CodecSettingsPanel
from .text_overlay_panel import TextOverlayPanel
from .image_overlay_panel import ImageOverlayPanel
from .video_overlay_panel import VideoOverlayPanel
from .intro_video_panel import IntroVideoPanel
from .outro_video_panel import OutroVideoPanel

__all__ = ['TaskTableWidget', 'ProcessingParamsPanel', 'CodecSettingsPanel', 
           'TextOverlayPanel', 'ImageOverlayPanel', 'VideoOverlayPanel',
           'IntroVideoPanel', 'OutroVideoPanel']
