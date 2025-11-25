# Example Workflows

This document provides example configurations for common video processing scenarios.

## Workflow 1: YouTube Upload Optimization

**Goal**: Prepare videos for YouTube upload with good quality and reasonable file size.

**Settings**:
- **Input**: Raw footage folder
- **Output**: YouTube_ready folder
- **Speed**: 1.0x (no change)
- **Volume**: 1.0 (100%)
- **Scale**: 1920x1080 (1080p)
- **Codec**: H.264
- **Quality**: CRF 21
- **Preset**: Medium
- **Watermark**: Text "© YourChannel 2025" at position (10, 1040)

**Expected Result**: High-quality 1080p videos suitable for YouTube.

---

## Workflow 2: Fast Social Media Clips

**Goal**: Create quick, small clips for Instagram/TikTok.

**Settings**:
- **Input**: Long videos
- **Output**: Social_clips folder
- **Speed**: 1.2x (slightly faster)
- **Volume**: 1.2 (120% - louder)
- **Trim**: Start 00:00:10, End 00:01:10 (1 minute clip)
- **Scale**: 1080x1920 (vertical for mobile)
- **Codec**: H.264 NVENC (if GPU available)
- **Quality**: Bitrate 8M
- **Preset**: Fast
- **Watermark**: Image logo at position (10, 10)

**Expected Result**: Fast-processed vertical clips optimized for mobile.

---

## Workflow 3: Archive/Backup with Maximum Compression

**Goal**: Archive old videos with smallest file size.

**Settings**:
- **Input**: Archive_source folder
- **Output**: Archive_compressed folder
- **Speed**: 1.0x
- **Volume**: 1.0
- **Scale**: 1280x720 (720p to reduce size)
- **Codec**: HEVC (H.265)
- **Quality**: CRF 28 (higher = smaller file)
- **Preset**: Slow (better compression)

**Expected Result**: Significantly smaller files with acceptable quality.

---

## Workflow 4: Tutorial Videos with Subtitles

**Goal**: Add subtitles and watermark to tutorial videos.

**Settings**:
- **Input**: Tutorial_raw folder
- **Output**: Tutorial_final folder
- **Speed**: 1.0x
- **Volume**: 1.0
- **Scale**: Original
- **Codec**: H.264
- **Quality**: CRF 20
- **Preset**: Medium
- **Watermark**: Text "Tutorial Series - Episode X" at (10, 10)
- **Subtitle**: tutorial.srt file

**Expected Result**: Professional tutorial videos with burned-in subtitles.

---

## Workflow 5: GPU-Accelerated Batch Processing

**Goal**: Process large batch of videos quickly using GPU.

**Settings**:
- **Input**: Batch_input folder (100+ videos)
- **Output**: Batch_output folder
- **Speed**: 1.0x
- **Volume**: 1.0
- **Scale**: 1920x1080
- **Codec**: H.264 NVENC
- **Quality**: CRF 23
- **Preset**: Fast
- **GPU**: Enabled (auto-detected)

**Expected Result**: Fast processing of large batches using GPU acceleration.

---

## Workflow 6: Slow Motion Effect

**Goal**: Create slow-motion videos.

**Settings**:
- **Input**: Action_footage folder
- **Output**: Slowmo_output folder
- **Speed**: 0.5x (half speed)
- **Volume**: 1.0
- **Scale**: Original
- **Codec**: H.264
- **Quality**: CRF 18 (high quality for slow-mo)
- **Preset**: Slow

**Expected Result**: Smooth slow-motion videos at half speed.

---

## Workflow 7: Timelapse Creation

**Goal**: Speed up long recordings into timelapse.

**Settings**:
- **Input**: Timelapse_raw folder
- **Output**: Timelapse_final folder
- **Speed**: 2.0x (double speed)
- **Volume**: 0.0 (mute audio)
- **Scale**: 1920x1080
- **Codec**: H.264
- **Quality**: CRF 20
- **Preset**: Medium

**Expected Result**: Fast-paced timelapse videos.

---

## Workflow 8: Crop and Watermark for Branding

**Goal**: Crop to specific aspect ratio and add brand watermark.

**Settings**:
- **Input**: Raw_content folder
- **Output**: Branded_content folder
- **Speed**: 1.0x
- **Volume**: 1.0
- **Crop**: X=0, Y=140, Width=1920, Height=1080 (remove top/bottom bars)
- **Scale**: Original
- **Codec**: H.264
- **Quality**: CRF 21
- **Preset**: Medium
- **Watermark**: Image "logo.png" at (1820, 980) (bottom-right)

**Expected Result**: Cropped videos with brand logo in corner.

---

## Tips for Optimal Results

### Quality vs. File Size
- **CRF 18-20**: Very high quality, large files (archival)
- **CRF 21-23**: High quality, moderate files (recommended)
- **CRF 24-28**: Good quality, small files (web/mobile)
- **CRF 29+**: Lower quality, very small files (preview/draft)

### Preset Selection
- **Ultrafast/Superfast**: Very fast, larger files, lower quality
- **Fast/Medium**: Balanced speed and quality (recommended)
- **Slow/Slower**: Slow encoding, smaller files, better quality
- **Veryslow**: Very slow, best compression (archival only)

### GPU vs. CPU
- **GPU (NVENC)**: 5-10x faster, slightly larger files
- **CPU (libx264/libx265)**: Slower, better compression
- **Use GPU for**: Large batches, time-sensitive work
- **Use CPU for**: Best quality, archival, small batches

### Speed Adjustments
- **0.5x**: Smooth slow motion (requires high FPS source)
- **0.75x**: Slight slow motion
- **1.0x**: Normal speed
- **1.25x**: Slightly faster (good for lectures)
- **1.5x-2.0x**: Timelapse effect

### Watermark Positioning
- **Top-left**: (10, 10)
- **Top-right**: (width - watermark_width - 10, 10)
- **Bottom-left**: (10, height - watermark_height - 10)
- **Bottom-right**: (width - watermark_width - 10, height - watermark_height - 10)
- **Center**: ((width - watermark_width) / 2, (height - watermark_height) / 2)

---

## Troubleshooting Common Issues

### Issue: Processing is very slow
**Solution**: 
- Use GPU codec (NVENC) if available
- Increase preset speed (Fast instead of Slow)
- Reduce output resolution
- Close other applications

### Issue: Output file is too large
**Solution**:
- Increase CRF value (higher = smaller)
- Use HEVC codec instead of H.264
- Reduce resolution (scale down)
- Use slower preset for better compression

### Issue: Output quality is poor
**Solution**:
- Decrease CRF value (lower = better)
- Use slower preset
- Increase bitrate (if using bitrate mode)
- Don't scale down too much

### Issue: Audio is out of sync
**Solution**:
- Ensure speed is applied to both video and audio
- Check source video isn't already corrupted
- Try different codec
- Use CRF mode instead of bitrate

### Issue: Watermark is cut off
**Solution**:
- Adjust X/Y position values
- Check watermark size vs. video resolution
- Apply watermark after scaling, not before
- Use smaller watermark image
