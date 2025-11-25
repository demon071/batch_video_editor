# Hướng dẫn Debug FFmpeg Crash

## Vấn đề hiện tại
Error message: "FFmpeg crashed during processing" - quá chung chung, không có chi tiết.

## Đã cải thiện
✅ Worker bây giờ capture stderr từ FFmpeg
✅ Hiển thị 10 dòng cuối của FFmpeg output trong error message
✅ Error details sẽ hiển thị trong dialog "Show Error Details"

## Cách debug

### 1. Xem console output
Trong terminal đang chạy `python main.py`, tìm:
```
================================================================================
FFmpeg Command:
================================================================================
ffmpeg -i "path/to/input.mp4" ...
================================================================================
```

Copy command này và chạy thử trực tiếp trong terminal để xem lỗi chi tiết.

### 2. Các lỗi thường gặp với text overlay

**A. Font path issue:**
```
Error: Cannot load font 'C:/Windows/Fonts/...'
```
**Giải pháp:**
- Không chọn font (để FFmpeg dùng default)
- Hoặc thử font khác (Arial, Verdana)

**B. Text encoding issue:**
```
Error: Invalid UTF-8 sequence
```
**Giải pháp:**
- Dùng text ASCII đơn giản: "TEST"
- Tránh emoji, ký tự đặc biệt

**C. Filter syntax error:**
```
Error: Invalid filter 'drawtext'
```
**Giải pháp:**
- Kiểm tra FFmpeg version: `ffmpeg -version`
- Cần FFmpeg với libfreetype support

**D. File path với ký tự đặc biệt:**
Tên file của bạn: `161⧸30块小清新红色格子裙太太太好看了 6475c37400000000130374b4.mp4`

Có ký tự đặc biệt: `⧸` (division slash) và tiếng Trung

**Giải pháp:**
1. Đổi tên file đơn giản hơn
2. Hoặc copy file sang folder khác với tên đơn giản
3. Test với file có tên ASCII trước

### 3. Test đơn giản

**Bước 1:** Tắt text overlay
- Uncheck "Enable Text Overlay"
- Load lại videos
- Start processing
- Xem có lỗi không?

**Bước 2:** Nếu không lỗi → Vấn đề ở text overlay
- Bật text overlay
- Dùng text đơn giản: "TEST"
- Không chọn font (để trống)
- Thử lại

**Bước 3:** Nếu vẫn lỗi → Vấn đề ở file path
- Copy video sang folder đơn giản: `C:\test\`
- Đổi tên: `video1.mp4`
- Thử lại

### 4. Chạy FFmpeg command trực tiếp

Copy command từ console, ví dụ:
```bash
ffmpeg -i "D:\path\to\input.mp4" -vf "drawtext=text='TEST':fontsize=48:fontcolor=0xFFFFFF:x=10:y=10" -c:v libx264 -crf 23 -preset medium -c:a copy -y "D:\path\to\output.mp4"
```

Chạy trong terminal để xem lỗi chi tiết từ FFmpeg.

## Sau khi cập nhật code

1. **Restart app**: `python main.py`
2. **Thử lại processing**
3. **Right-click task lỗi → "Show Error Details"**
4. **Xem error message chi tiết hơn** (có FFmpeg output)

## Cần thêm thông tin

Để tôi giúp debug chính xác hơn, hãy share:
1. Console output (toàn bộ)
2. FFmpeg command được generate
3. Error message mới (sau khi restart app)
