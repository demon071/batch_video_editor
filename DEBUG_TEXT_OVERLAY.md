# Debug Instructions for Text Overlay

## How to Debug

1. **Run the application**:
   ```bash
   python main.py
   ```

2. **Enable text overlay**:
   - Check "Enable Text Overlay" in the right panel
   - Enter some text (e.g., "Test Text")
   - Select a font
   - Choose a position

3. **Load a video and start processing**

4. **Check the console output** for debug information:
   - Look for "FFmpeg Command:" section
   - Look for "DEBUG: Text overlay is active!" message
   - Check the generated filter string

## What to Look For

### If text overlay is working:
```
DEBUG: Text overlay is active!
  Text: Test Text...
  Font: Arial
  Font path: C:\Windows\Fonts\arial.ttf
  Generated filter: drawtext=text='Test Text':fontfile=C\:/Windows/Fonts/arial.ttf:fontsize=48:fontcolor=0xFFFFFF:x=10:y=10:bordercolor=0x000000:borderw=2
```

### If text overlay is NOT working:

**Case 1: Text settings not in task**
```
DEBUG: No text settings in task
```
→ **Problem**: Text settings not being passed to VideoTask
→ **Fix**: Check main_window.py line 363

**Case 2: Text settings exist but not active**
```
DEBUG: Text settings exist but not active
  Enabled: False
  Text: ''
```
→ **Problem**: Text overlay checkbox not checked OR text field is empty
→ **Fix**: Make sure checkbox is checked and text is entered

**Case 3: Filter generation returns None**
```
DEBUG: Text overlay is active!
  ...
  WARNING: Filter generation returned None!
```
→ **Problem**: Text is empty after stripping whitespace
→ **Fix**: Check text content

### FFmpeg Command Check

The complete FFmpeg command should include `-vf` with the drawtext filter:
```
ffmpeg -i input.mp4 -vf "drawtext=text='Test':fontfile=C\:/Windows/Fonts/arial.ttf:..." output.mp4
```

If you see the command but text still doesn't appear:
1. Copy the FFmpeg command from console
2. Run it manually in terminal
3. Check for FFmpeg errors

## Common Issues

1. **Font path with spaces**: Should be escaped properly
2. **Special characters in text**: Should be escaped with backslashes
3. **Color format**: Should be `0xRRGGBB` not `#RRGGBB`
4. **Position out of bounds**: Text might be outside video frame

## Test Command

Try this minimal FFmpeg command manually:
```bash
ffmpeg -i input.mp4 -vf "drawtext=text='TEST':fontsize=48:fontcolor=white:x=10:y=10" output.mp4
```

If this works, the issue is in our filter generation.
If this doesn't work, FFmpeg or font configuration issue.
