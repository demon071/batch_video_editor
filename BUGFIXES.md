# Bug Fixes Applied

## Issues Fixed

### 1. VideoTask Hashability Error
**Error**: `TypeError: unhashable type: 'VideoTask'`

**Cause**: VideoTask dataclass was being used as dictionary key in task_table.py but wasn't hashable by default.

**Fix**: Added `eq=False` to dataclass decorator and implemented custom `__hash__()` and `__eq__()` methods based on object identity.

**Files Modified**:
- `models/video_task.py`

### 2. JSON Parsing Error in Video Info
**Error**: `the JSON object must be str, bytes or bytearray, not NoneType`

**Cause**: ffprobe subprocess could return empty or None stdout, causing JSON parsing to fail.

**Fix**: Added checks for empty stdout before JSON parsing, improved error handling, and safely parsed FPS fraction strings.

**Files Modified**:
- `utils/system_check.py`

### 3. Unicode Decoding Error
**Error**: `UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f in position 4167`

**Cause**: subprocess calls with `text=True` used Windows default encoding (cp1252/charmap) which couldn't handle UTF-8 characters from FFmpeg output.

**Fix**: Added explicit `encoding='utf-8'` and `errors='ignore'` parameters to all subprocess.run() calls.

**Files Modified**:
- `utils/system_check.py` (all subprocess calls)

### 4. Qt High DPI Scaling Warning
**Warning**: `Attribute Qt::AA_EnableHighDpiScaling must be set before QCoreApplication is created`

**Cause**: High DPI attributes were set after QApplication creation.

**Fix**: Moved setAttribute calls before QApplication instantiation.

**Files Modified**:
- `main.py`

### 5. Separate Console Window Issues
**Issue**: Attempting to create separate CMD window for FFmpeg output caused encoding issues and complexity.

**Fix**: Disabled separate console window feature. Users can monitor progress through the UI table and progress bars instead. This simplifies the code and avoids encoding issues.

**Files Modified**:
- `core/worker.py`

## Testing Results

After all fixes applied:
- ✅ Application launches successfully
- ✅ No Unicode errors
- ✅ No hashability errors  
- ✅ FFmpeg detection works
- ✅ GPU detection works
- ✅ UI displays correctly
- ✅ No runtime errors in background threads

## Current Status

**Application is now stable and ready for use!**

Users can:
1. Launch the application: `python main.py`
2. Select input/output folders
3. Load video files
4. Configure processing parameters
5. Start batch processing
6. Monitor progress in the UI

All core functionality is working correctly.
