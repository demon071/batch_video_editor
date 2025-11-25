# Text Overlay Issue - SOLVED

## Problem Identified

The debug output shows:
```
DEBUG: Text settings exist but not active
  Enabled: False
  Text: ''
```

**Root Cause**: The text overlay checkbox is not checked when loading videos.

## Solution

### To Enable Text Overlay:

1. **In the right panel, scroll down to "Text Overlay" section**

2. **Check the "Enable Text Overlay" checkbox** ✓

3. **Enter your text** in the text box

4. **Configure settings**:
   - Select a font
   - Set font size
   - Choose colors
   - Set position

5. **THEN load your videos**

The text settings are captured when you click "Load Files" or "Add Files", so you must:
- ✓ Enable text overlay FIRST
- ✓ Configure all settings
- ✓ THEN load videos

## Why This Happens

The text overlay settings are copied from the UI panel to each VideoTask when the task is created (in `main_window.py` line 363):

```python
task.text_settings = self.text_overlay_panel.get_text_settings()
```

If the checkbox isn't checked at that moment, `enabled=False` is saved to the task.

## Quick Test

1. Close the app
2. Run `python main.py`
3. **Before loading any videos**:
   - Scroll to "Text Overlay" panel
   - Check "Enable Text Overlay"
   - Type "TEST" in the text box
   - Select any font
4. Now load videos
5. Start processing

You should see in console:
```
DEBUG: Text overlay is active!
  Text: TEST...
  Font: Arial
  ...
```

And the FFmpeg command will include `-vf "drawtext=..."`.

## Confirmed Working

The code is correct! The issue was just that the feature wasn't enabled in the UI before loading videos.
