"""UI widgets package."""
from .task_table import TaskTableWidget
from .params_panel import ProcessingParamsPanel
from .codec_panel import CodecSettingsPanel
from .text_overlay_panel import TextOverlayPanel
from .image_overlay_panel import ImageOverlayPanel
from .video_overlay_panel import VideoOverlayPanel
from .media_overlay_panel import MediaOverlayPanel
from .intro_video_panel import IntroVideoPanel
from .outro_video_panel import OutroVideoPanel
from .stacking_panel import StackingPanel
from .background_frame_panel import BackgroundFramePanel
from .split_panel import SplitPanel
from .layer_manager_panel import LayerManagerPanel
from .visual_preview import VisualPreviewWidget

# New professional layout widgets
from .project_browser_widget import ProjectBrowserWidget
from .preview_player_widget import PreviewPlayerWidget
from .properties_panel_widget import PropertiesPanelWidget

__all__ = [
    'TaskTableWidget',
    'ProcessingParamsPanel',
    'CodecSettingsPanel',
    'TextOverlayPanel',
    'ImageOverlayPanel',
    'VideoOverlayPanel',
    'MediaOverlayPanel',
    'IntroVideoPanel',
    'OutroVideoPanel',
    'StackingPanel',
    'BackgroundFramePanel',
    'SplitPanel',
    'LayerManagerPanel',
    'VisualPreviewWidget',
    'ProjectBrowserWidget',
    'PreviewPlayerWidget',
    'PropertiesPanelWidget',
]
