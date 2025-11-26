# Video Splitting Feature - Usage Guide

## Overview

The video splitting feature allows you to split videos into multiple parts using FFmpeg's stream copy for fast, lossless splitting. You can also automatically apply other effects (speed, crop, text, etc.) to the split parts.

## Features

✅ **Two Split Modes**:
- **By Count**: Split video into N equal parts (e.g., 3 parts)
- **By Duration**: Split video every X minutes/seconds (e.g., every 5 minutes)

✅ **Stream Copy**: No re-encoding - extremely fast and maintains original quality

✅ **Split-Then-Process**: Automatically apply effects to split parts

✅ **Auto-Cleanup**: Intermediate split files are automatically deleted after processing

## How to Use

### 1. Enable Video Splitting

1. Open the **Video Splitting** panel in the settings area
2. Check **"Enable Video Splitting"**

### 2. Choose Split Mode

#### Option A: Split by Count
- Select **"By Count (N equal parts)"** from the dropdown
- Set **Number of Parts** (2-100)

#### Option B: Split by Duration
- Select **"By Duration (every X seconds)"** from the dropdown
- Set **Duration per Part** using minutes and seconds spinners

### 3. Configure Processing (Optional)

#### Process Split Parts
- Check **"Process split parts with current settings"**
- This will apply all other enabled settings (Speed, Crop, Text Overlay, etc.) to each split part.
- **Note**: Intermediate split files will be deleted automatically.

### 4. Output Pattern

The default pattern is: `{name}_part{num:03d}{ext}`

### 5. Load Videos and Process

1. Load your videos as usual
2. Click **"Apply Settings to All Tasks"**
3. Click **"Start Processing"**

## Workflows

### Workflow A: Simple Split (Fast)
- **Goal**: Just split video, no other effects.
- **Settings**: Enable Split, Uncheck "Process split parts".
- **Result**: `video_part001.mp4`, `video_part002.mp4`... (Original quality)

### Workflow B: Split and Speed Up
- **Goal**: Split video into 3 parts, then speed up each part by 2x.
- **Settings**: 
  - Enable Split (By Count: 3)
  - Check "Process split parts"
  - Set Speed to 2.0
- **Result**: `video_part001_processed.mp4` (2x speed), `video_part002_processed.mp4` (2x speed)...

## Troubleshooting

### Issue: Split parts have wrong duration
**Solution**: Enable "Keyframe Accurate" to minimize variance.

### Issue: Processing takes too long
**Solution**: "Process split parts" requires re-encoding. If you only need to split, uncheck this option.

---

**Need Help?** Check the main README.md or create an issue on GitHub.
