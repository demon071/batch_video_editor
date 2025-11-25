# Quick Test Instructions

## Please do this test:

1. **Close the app completely** (if running)

2. **Start fresh**: `python main.py`

3. **BEFORE loading any videos**:
   - Scroll to "Text Overlay" section in right panel
   - ✓ Check "Enable Text Overlay" checkbox
   - Type "TEST" in the text box (make sure you actually type something!)
   - Select any font from the dropdown

4. **Now load a video** (click "Load Files" button)

5. **Check the console output** - you should see:
   ```
   DEBUG: Task creation for yourfile.mp4
     Text overlay enabled in UI: True
     Text in UI: 'TEST'
     Captured settings - Enabled: True
     Captured settings - Text: 'TEST'
   ```

6. **Start processing**

7. **Check console again** - you should see:
   ```
   DEBUG: Text overlay is active!
     Text: TEST...
     Font: Arial
     Generated filter: drawtext=text='TEST':fontfile=...
   
   FFmpeg Command:
   ...should include -vf "drawtext=..."...
   ```

## If you still see "Enabled: False":

The checkbox state isn't being read correctly. This could be because:
1. The checkbox isn't actually checked (try clicking it multiple times)
2. There's a Qt event timing issue
3. The text box is empty (must have text!)

## Share the console output

Please copy and paste the complete console output here so I can see exactly what's happening!
