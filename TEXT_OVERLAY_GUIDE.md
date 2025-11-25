# Hướng dẫn sử dụng Text Overlay

## ⚠️ Quan trọng: Thứ tự các bước

### ❌ SAI - Text không xuất hiện:
1. Load videos
2. Bật text overlay
3. Start processing
→ Text settings không được lưu vào tasks!

### ✅ ĐÚNG - Text xuất hiện:
1. **Bật text overlay TRƯỚC** ✓
2. **Nhập text**
3. **Chọn font, màu sắc, vị trí**
4. **SAU ĐÓ mới load videos**
5. Start processing
→ Text settings được lưu vào tasks!

## 📝 Workflow chi tiết

### Bước 1: Cấu hình Text Overlay
```
1. Scroll xuống panel "Text Overlay" (bên phải)
2. ✓ Check "Enable Text Overlay"
3. Nhập text: "Xin chào" hoặc "TEST"
4. Chọn font (hoặc để mặc định)
5. Chọn font size: 48
6. Chọn màu: Trắng
7. Chọn vị trí: Bottom-Left hoặc Custom
```

### Bước 2: Load Videos
```
1. Click "Load Files" hoặc "Load Folder"
2. Chọn videos
3. Xem console - phải thấy:
   "Text overlay enabled in UI: True"
   "Text in UI: 'Xin chào'"
```

### Bước 3: Start Processing
```
1. Click "Start Processing"
2. Xem console - phải thấy:
   "DEBUG: Text overlay is active!"
   "Generated filter: drawtext=..."
```

## 🔄 Nếu muốn thay đổi settings SAU KHI load

### Cách 1: Load lại
1. Click "Clear All"
2. Thay đổi text overlay settings
3. Load videos lại
4. Start processing

### Cách 2: Dùng "Apply Settings to All Tasks"
1. Thay đổi text overlay settings
2. Click "Apply Settings to All Tasks" (nút xanh lá)
3. Confirm
4. Start processing

## 🛑 Stop / Pause

### Pause:
- Click "Pause" → Dừng tạm thời
- Click "Resume" → Tiếp tục

### Stop:
- Click "Stop" → Dừng hẳn
- Confirm dialog
- Tasks đang xử lý sẽ bị reset về Pending

## ✅ Kiểm tra Text Overlay đã bật chưa

Xem console khi load videos:
```
DEBUG: Task creation for video.mp4
  Text overlay enabled in UI: True    ← Phải là True
  Text in UI: 'Xin chào'              ← Phải có text
  Captured settings - Enabled: True   ← Phải là True
```

Nếu thấy `False` → Text overlay chưa bật!

## 🎯 Test nhanh

```bash
# 1. Restart app
python main.py

# 2. TRƯỚC KHI load videos:
#    - ✓ Enable Text Overlay
#    - Text: "TEST"
#    - Font: Default
#    - Size: 48
#    - Color: White

# 3. Load videos

# 4. Xem console:
#    Text overlay enabled in UI: True  ← Phải thấy dòng này

# 5. Start processing

# 6. Kiểm tra output video
```

## 📌 Lưu ý

- ✅ Text overlay settings chỉ được lưu khi **LOAD** videos
- ✅ Phải bật **TRƯỚC** khi load
- ✅ Hoặc dùng "Apply Settings" để cập nhật sau
- ❌ Không thể thay đổi settings trong khi processing
