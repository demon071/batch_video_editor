# Test FFmpeg Command - Hướng dẫn

## Vấn đề file path với emoji

File của bạn có emoji và ký tự đặc biệt:
```
毛衣🧶分享｜好爱这件藏蓝色的毛衣🛒 6904dcd50000000007037237.mp4
```

Emoji `🧶` và `🛒` có thể gây vấn đề với FFmpeg trên Windows.

## Test thủ công

### 1. Test file path đơn giản

Copy file sang folder test:
```bash
mkdir C:\test
copy "D:\WORK\CODE\allCode\downloadpro\dist\xiaohongshu_user_5d2ae90e0000000012036544\毛衣🧶分享｜好爱这件藏蓝色的毛衣🛒 6904dcd50000000007037237.mp4" "C:\test\video1.mp4"
```

### 2. Test FFmpeg command đơn giản (KHÔNG có text overlay)

```bash
ffmpeg -i "C:\test\video1.mp4" -c:v libx264 -crf 23 -preset medium -c:a copy -y "C:\test\output1.mp4"
```

Nếu thành công → File path OK, vấn đề ở text overlay

### 3. Test với text overlay đơn giản

```bash
ffmpeg -i "C:\test\video1.mp4" -vf "drawtext=text='TEST':x=10:y=10:fontsize=48:fontcolor=white:borderw=2:bordercolor=black" -c:v libx264 -crf 23 -preset medium -c:a copy -y "C:\test\output2.mp4"
```

Nếu thành công → Text overlay OK

### 4. Test với text tiếng Việt

```bash
ffmpeg -i "C:\test\video1.mp4" -vf "drawtext=text='xin chao':x=10:y=10:fontsize=48:fontcolor=white:borderw=2:bordercolor=black" -c:v libx264 -crf 23 -preset medium -c:a copy -y "C:\test\output3.mp4"
```

### 5. Test với text có dấu

```bash
ffmpeg -i "C:\test\video1.mp4" -vf "drawtext=text='Xin chào':x=10:y=10:fontsize=48:fontcolor=white:borderw=2:bordercolor=black" -c:v libx264 -crf 23 -preset medium -c:a copy -y "C:\test\output4.mp4"
```

## Trong app

### Workflow đúng:

1. **Tạo folder test đơn giản**: `C:\test\input` và `C:\test\output`
2. **Copy videos** vào `C:\test\input` (có thể đổi tên đơn giản)
3. **Restart app**: `python main.py`
4. **Chọn folders**:
   - Input: `C:\test\input`
   - Output: `C:\test\output`
5. **Bật text overlay**:
   - ✓ Check "Enable Text Overlay"
   - Text: "TEST" (đơn giản trước)
   - Không chọn font
6. **Load Files**
7. **Start Processing**

### Debug output cần xem:

```
DEBUG: Task creation for video1.mp4
  Text overlay enabled in UI: True
  Text in UI: 'TEST'
  Captured settings - Enabled: True
  Captured settings - Text: 'TEST'

DEBUG: Text overlay is active!
  Text: TEST...
  Font: System Default
  Font path: None
  Generated filter: drawtext=text='TEST':fontsize=48:fontcolor=0xFFFFFF:x=10:y=10:bordercolor=0x000000:borderw=2

================================================================================
FFmpeg Command:
================================================================================
ffmpeg -i C:\test\input\video1.mp4 -vf drawtext=text='TEST':fontsize=48:fontcolor=0xFFFFFF:x=10:y=10:bordercolor=0x000000:borderw=2 -c:v libx264 -crf 23 -preset medium -c:a copy -progress pipe:1 -y C:\test\output\video1_processed.mp4
================================================================================
```

## Nếu vẫn lỗi

1. **Copy FFmpeg command** từ console
2. **Chạy trực tiếp** trong terminal
3. **Xem lỗi chi tiết** từ FFmpeg
4. **Share lỗi** với tôi

## Lưu ý quan trọng

- ✅ QProcess tự động quote arguments
- ✅ Text escaping đã được cải thiện
- ❌ Emoji trong file path có thể gây vấn đề
- ❌ Ký tự đặc biệt trong text cần escape đúng

## Quick fix

Nếu muốn test nhanh:
1. Dùng file có tên ASCII: `video1.mp4`
2. Dùng text ASCII: `TEST`
3. Output folder đơn giản: `C:\test\output`
