"""
Migration utilities for converting legacy overlay system to multi-layer system.

Converts old overlay fields (text_settings, image_overlay, video_overlay) 
to new Layer-based system.
"""
from typing import List
from pathlib import Path
from models.video_task import VideoTask
from models.layer import Layer, LayerType, TextLayerProperties, ImageLayerProperties, VideoLayerProperties


def migrate_task_to_layers(task: VideoTask) -> VideoTask:
    """
    Migrate a VideoTask from legacy overlay system to layer system.
    
    Args:
        task: VideoTask with legacy overlay fields
        
    Returns:
        VideoTask with populated layers field
    """
    if not task.use_legacy_overlays:
        # Already migrated
        return task
    
    if task.layers is None:
        task.layers = []
    
    z_index = 0
    
    # Migrate text overlay (text_settings)
    if task.text_settings and task.text_settings.is_active():
        text_layer = Layer(
            type=LayerType.TEXT,
            z_index=z_index,
            enabled=True,
            name=f"Text {z_index + 1}",
            position=(task.text_settings.position_x, task.text_settings.position_y),
            start_time=None,
            end_time=None,
            properties={
                TextLayerProperties.TEXT: task.text_settings.text,
                TextLayerProperties.FONT_FILE: task.text_settings.font_path,
                TextLayerProperties.FONT_SIZE: task.text_settings.font_size,
                TextLayerProperties.FONT_COLOR: task.text_settings.font_color,
                TextLayerProperties.BORDER_WIDTH: task.text_settings.outline_thickness,
                TextLayerProperties.BORDER_COLOR: task.text_settings.outline_color,
            }
        )
        task.layers.append(text_layer)
        z_index += 1
    
    # Migrate image overlay
    if task.image_overlay and task.image_overlay.get('enabled'):
        img_props = task.image_overlay
        
        # Extract position
        x = img_props.get('x', 10)
        y = img_props.get('y', 10)
        
        image_layer = Layer(
            type=LayerType.IMAGE,
            z_index=z_index,
            enabled=True,
            name=f"Image {z_index + 1}",
            position=(x, y),
            start_time=None,
            end_time=None,
            properties={
                ImageLayerProperties.FILE_PATH: img_props.get('file_path'),
                ImageLayerProperties.SCALE_WIDTH: img_props.get('scale_width'),
                ImageLayerProperties.SCALE_HEIGHT: img_props.get('scale_height'),
                ImageLayerProperties.OPACITY: img_props.get('opacity', 1.0),
            }
        )
        task.layers.append(image_layer)
        z_index += 1
    
    # Migrate video overlay
    if task.video_overlay and task.video_overlay.get('enabled'):
        vid_props = task.video_overlay
        
        # Extract position
        x = vid_props.get('x', 10)
        y = vid_props.get('y', 10)
        
        # Extract timing
        start_time = vid_props.get('start_time')
        end_time = vid_props.get('end_time')
        
        video_layer = Layer(
            type=LayerType.VIDEO,
            z_index=z_index,
            enabled=True,
            name=f"Video {z_index + 1}",
            position=(x, y),
            start_time=start_time,
            end_time=end_time,
            properties={
                VideoLayerProperties.FILE_PATH: vid_props.get('file_path'),
                VideoLayerProperties.SCALE_WIDTH: vid_props.get('scale_width'),
                VideoLayerProperties.SCALE_HEIGHT: vid_props.get('scale_height'),
                VideoLayerProperties.OPACITY: vid_props.get('opacity', 1.0),
                VideoLayerProperties.LOOP: vid_props.get('loop', False),
            }
        )
        task.layers.append(video_layer)
        z_index += 1
    
    # Mark as migrated
    task.use_legacy_overlays = False
    
    return task


def should_migrate(task: VideoTask) -> bool:
    """
    Check if a task needs migration.
    
    Args:
        task: VideoTask to check
        
    Returns:
        True if task has legacy overlays and needs migration
    """
    if not task.use_legacy_overlays:
        return False
    
    has_legacy_overlays = (
        (task.text_settings and task.text_settings.is_active()) or
        (task.image_overlay and task.image_overlay.get('enabled')) or
        (task.video_overlay and task.video_overlay.get('enabled'))
    )
    
    return has_legacy_overlays


def layers_to_dict_list(layers: List[Layer]) -> List[dict]:
    """
    Convert list of Layer objects to list of dicts for serialization.
    
    Args:
        layers: List of Layer objects
        
    Returns:
        List of dictionaries
    """
    return [layer.to_dict() for layer in layers]


def dict_list_to_layers(data: List[dict]) -> List[Layer]:
    """
    Convert list of dicts to list of Layer objects.
    
    Args:
        data: List of dictionaries
        
    Returns:
        List of Layer objects
    """
    return [Layer.from_dict(d) for d in data]
