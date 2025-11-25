# Apply Settings Feature - Usage Guide

## Tính năng mới: Apply Settings to All Tasks

### Mục đích
Cho phép bạn thay đổi thiết lập SAU KHI đã load videos, rồi áp dụng thiết lập mới cho tất cả các task.

### Cách sử dụng

#### Workflow cũ (không linh hoạt):
1. Chọn thiết lập trước
2. Load videos
3. Start processing
❌ Không thể thay đổi thiết lập sau khi load

#### Workflow mới (linh hoạt):
1. **Load videos** (với bất kỳ thiết lập nào)
2. **Thay đổi thiết lập** trong UI:
   - Bật/tắt text overlay
   - Thay đổi text, font, màu sắc
   - Điều chỉnh speed, volume
   - Thay đổi codec, quality
   - Cập nhật watermark, subtitle
3. **Bấm "Apply Settings to All Tasks"** (nút màu xanh lá)
4. **Xác nhận** trong dialog
5. **Start processing** với thiết lập mới

### Ví dụ

**Tình huống**: Bạn load 100 videos, sau đó nhận ra cần thêm text overlay.

**Giải pháp**:
1. Load 100 videos (text overlay chưa bật)
2. Bật text overlay, nhập text "© 2024"
3. Chọn font, màu sắc, vị trí
4. Bấm "Apply Settings to All Tasks"
5. Xác nhận → Tất cả 100 videos sẽ có text overlay
6. Start processing

### Lưu ý

- ✅ Có thể apply nhiều lần trước khi start
- ✅ Apply cập nhật TẤT CẢ thiết lập (không chỉ text overlay)
- ❌ Không thể apply khi đang processing (phải stop trước)
- ✅ Có dialog xác nhận trước khi apply
- ✅ Hiển thị thông báo khi apply thành công

### Các thiết lập được cập nhật

Khi bấm "Apply Settings", các thiết lập sau sẽ được cập nhật:

**Processing Parameters**:
- Speed (tốc độ video)
- Volume (âm lượng)
- Trim (cắt video)
- Scale (thay đổi kích thước)
- Crop (cắt khung hình)

**Text Overlay**:
- Enable/disable
- Text content
- Font, size, color
- Position
- Outline, background box

**Watermark**:
- Type (text/image)
- Content/image
- Position

**Codec & Quality**:
- Video codec
- Quality mode (CRF/Bitrate)
- CRF value
- Bitrate
- Preset

**Subtitle**:
- Subtitle file

### Giao diện

Nút "Apply Settings to All Tasks":
- Màu xanh lá (dễ nhận biết)
- Nằm giữa progress bar và nút Start
- Chỉ enabled khi có tasks đã load
- Disabled khi đang processing

### Thông báo

**Khi apply thành công**:
```
Settings Applied
Successfully applied settings to X tasks!
```

**Khi không có tasks**:
```
No Tasks
No tasks loaded. Please load videos first.
```

**Khi đang processing**:
```
Cannot Apply
Stop processing before applying new settings.
```

## Test ngay

1. `python main.py`
2. Load vài videos (không cần bật text overlay)
3. Sau khi load xong, bật text overlay và nhập text
4. Bấm "Apply Settings to All Tasks"
5. Xác nhận
6. Start processing → Text sẽ xuất hiện trên videos!
