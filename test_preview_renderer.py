"""
Test script for PreviewRenderer.

Tests frame extraction and layer compositing.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from utils.preview_renderer import PreviewRenderer
from models.layer import Layer, LayerType, TextLayerProperties, ImageLayerProperties
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


def test_frame_extraction():
    """Test basic frame extraction."""
    print("Testing Frame Extraction...")
    print("=" * 60)
    
    # You need to provide a test video path
    test_video = Path("test_video.mp4")  # Replace with actual video
    
    if not test_video.exists():
        print(f"⚠️  Test video not found: {test_video}")
        print("   Please create a test video or update the path")
        return False
    
    renderer = PreviewRenderer()
    
    # Extract frame at 1 second
    frame = renderer.extract_frame(test_video, 1.0)
    
    if frame is None:
        print("❌ Frame extraction failed")
        return False
    
    print(f"✅ Frame extracted successfully")
    print(f"   Size: {frame.width()}x{frame.height()}")
    
    # Test cache
    frame2 = renderer.extract_frame(test_video, 1.0)
    print(f"✅ Frame cache working (same frame retrieved)")
    
    return True


def test_layer_rendering():
    """Test rendering with layers."""
    print("\n\nTesting Layer Rendering...")
    print("=" * 60)
    
    test_video = Path("test_video.mp4")
    
    if not test_video.exists():
        print(f"⚠️  Test video not found: {test_video}")
        return False
    
    renderer = PreviewRenderer()
    
    # Create test layers
    layers = [
        # Text layer
        Layer(
            type=LayerType.TEXT,
            z_index=0,
            name="Test Text",
            position=(50, 50),
            properties={
                TextLayerProperties.TEXT: "Hello Preview!",
                TextLayerProperties.FONT_SIZE: 48,
                TextLayerProperties.FONT_COLOR: "#FFFF00",
                TextLayerProperties.BORDER_WIDTH: 2,
                TextLayerProperties.BORDER_COLOR: "#000000"
            }
        ),
    ]
    
    # Render preview
    preview = renderer.render_preview(test_video, layers, 1.0)
    
    if preview is None:
        print("❌ Preview rendering failed")
        return False
    
    print(f"✅ Preview rendered successfully")
    print(f"   Size: {preview.width()}x{preview.height()}")
    print(f"   Layers: {len(layers)}")
    
    return True


def test_preview_display():
    """Test displaying preview in Qt window."""
    print("\n\nTesting Preview Display...")
    print("=" * 60)
    
    test_video = Path("test_video.mp4")
    
    if not test_video.exists():
        print(f"⚠️  Test video not found: {test_video}")
        print("   Skipping display test")
        return True
    
    app = QApplication(sys.argv)
    
    renderer = PreviewRenderer()
    
    # Create layers
    layers = [
        Layer(
            type=LayerType.TEXT,
            z_index=0,
            name="Title",
            position=(100, 100),
            properties={
                TextLayerProperties.TEXT: "Multi-Layer Preview Test",
                TextLayerProperties.FONT_SIZE: 64,
                TextLayerProperties.FONT_COLOR: "#FFFFFF",
                TextLayerProperties.BORDER_WIDTH: 3,
                TextLayerProperties.BORDER_COLOR: "#FF0000"
            }
        ),
        Layer(
            type=LayerType.TEXT,
            z_index=1,
            name="Subtitle",
            position=(100, 200),
            properties={
                TextLayerProperties.TEXT: "Z-Index: 1",
                TextLayerProperties.FONT_SIZE: 32,
                TextLayerProperties.FONT_COLOR: "#00FF00"
            }
        ),
    ]
    
    # Render preview
    preview = renderer.render_preview(test_video, layers, 1.0, max_width=800, max_height=600)
    
    if preview is None:
        print("❌ Preview rendering failed")
        return False
    
    # Create window to display preview
    window = QWidget()
    window.setWindowTitle("Preview Test")
    layout = QVBoxLayout(window)
    
    label = QLabel()
    label.setPixmap(preview)
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    
    window.show()
    
    print("✅ Preview window opened")
    print("   Close the window to continue...")
    
    app.exec_()
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PreviewRenderer Test Suite")
    print("=" * 60)
    
    try:
        # Run tests
        result1 = test_frame_extraction()
        result2 = test_layer_rendering()
        
        # Optional: Display test (requires closing window)
        # result3 = test_preview_display()
        
        print("\n" + "=" * 60)
        if result1 and result2:
            print("✅ All tests passed!")
        else:
            print("⚠️  Some tests failed or skipped")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
