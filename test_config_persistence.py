"""
Test script to verify settings persistence.
This script will:
1. Load current config
2. Modify settings
3. Save config
4. Reload config
5. Verify settings are persisted
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.settings import AppConfig
from models.enums import VideoCodec, QualityMode, Preset

def test_settings_persistence():
    print("Testing Settings Persistence...")
    print("=" * 60)
    
    # Create config instance
    config = AppConfig()
    
    # Display current settings
    print("\n1. Current Settings:")
    print(f"   Codec: {config.codec}")
    print(f"   Quality Mode: {config.quality_mode}")
    print(f"   CRF: {config.crf}")
    print(f"   Bitrate: {config.bitrate}")
    print(f"   Preset: {config.preset}")
    
    # Modify settings
    print("\n2. Modifying Settings...")
    config.codec = VideoCodec.HEVC
    config.quality_mode = QualityMode.BITRATE
    config.crf = 18
    config.bitrate = "10M"
    config.preset = Preset.SLOW
    
    print(f"   Codec: {config.codec}")
    print(f"   Quality Mode: {config.quality_mode}")
    print(f"   CRF: {config.crf}")
    print(f"   Bitrate: {config.bitrate}")
    print(f"   Preset: {config.preset}")
    
    # Reload config
    print("\n3. Reloading Config...")
    config2 = AppConfig()
    
    print(f"   Codec: {config2.codec}")
    print(f"   Quality Mode: {config2.quality_mode}")
    print(f"   CRF: {config2.crf}")
    print(f"   Bitrate: {config2.bitrate}")
    print(f"   Preset: {config2.preset}")
    
    # Verify
    print("\n4. Verification:")
    all_ok = True
    
    if config2.codec != VideoCodec.HEVC:
        print(f"   ❌ Codec mismatch: expected HEVC, got {config2.codec}")
        all_ok = False
    else:
        print(f"   ✓ Codec: {config2.codec}")
    
    if config2.quality_mode != QualityMode.BITRATE:
        print(f"   ❌ Quality Mode mismatch: expected BITRATE, got {config2.quality_mode}")
        all_ok = False
    else:
        print(f"   ✓ Quality Mode: {config2.quality_mode}")
    
    if config2.crf != 18:
        print(f"   ❌ CRF mismatch: expected 18, got {config2.crf}")
        all_ok = False
    else:
        print(f"   ✓ CRF: {config2.crf}")
    
    if config2.bitrate != "10M":
        print(f"   ❌ Bitrate mismatch: expected 10M, got {config2.bitrate}")
        all_ok = False
    else:
        print(f"   ✓ Bitrate: {config2.bitrate}")
    
    if config2.preset != Preset.SLOW:
        print(f"   ❌ Preset mismatch: expected SLOW, got {config2.preset}")
        all_ok = False
    else:
        print(f"   ✓ Preset: {config2.preset}")
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ All settings persisted correctly!")
    else:
        print("❌ Some settings were not persisted!")
    
    return all_ok

if __name__ == "__main__":
    success = test_settings_persistence()
    sys.exit(0 if success else 1)
