# 🚀 Hướng dẫn cài đặt và sử dụng Ollama

## 📥 Bước 1: Cài đặt Ollama

### Windows:

```bash
# Cách 1: Tải từ website (khuyến nghị)
# Truy cập: https://ollama.ai/download
# Tải file .exe và chạy

# Cách 2: Dùng winget
winget install Ollama.Ollama
```

### Kiểm tra cài đặt:

```bash
ollama --version
```

## 🤖 Bước 2: Tải AI Models

### Models khuyến nghị (chọn 1):

#### Llama 3.2 (Mới nhất - khuyến nghị):

```bash
ollama pull llama3.2        # ~2GB - nhanh, thông minh
```

#### Llama 2 (Ổn định):

```bash
ollama pull llama2          # ~4GB - ổn định, chậm hơn
```

#### Mistral (Nhẹ):

```bash
ollama pull mistral         # ~4GB - cân bằng tốc độ/chất lượng
```

#### CodeLlama (Chuyên code):

```bash
ollama pull codellama       # ~7GB - giỏi về code
```

## ⚙️ Bước 3: Cấu hình dự án

### Tạo file .env:

```bash
cp .env.example .env
```

### Nội dung file .env:

```env
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Database
DATABASE_URL=sqlite:///./chatbot.db

# FastAPI
DEBUG=True
```

## 🔧 Bước 4: Chạy hệ thống

### Khởi động Ollama (tự động với Windows service):

```bash
# Ollama thường tự khởi động
# Nếu cần khởi động thủ công:
ollama serve
```

### Khởi động FastAPI:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## ✅ Bước 5: Kiểm tra hoạt động

### Test Ollama:

```bash
# Terminal test:
ollama run llama3.2
# Gõ: "Hello" -> Enter
# Gõ: "/bye" để thoát
```

### Test API:

```bash
# Truy cập: http://127.0.0.1:8000/ai/health
# Sẽ thấy: "AI Service sử dụng Ollama"
```

### Test Chat:

```bash
POST http://127.0.0.1:8000/ai/chat
{
    "message": "Tạo brand Apple"
}
```

## 🎯 Các câu lệnh AI hiểu:

### Tạo Brand:

- "Tạo brand Apple"
- "Thêm thương hiệu Sony"
- "Tôi muốn tạo brand Samsung"

### Tạo Type:

- "Tạo type bluetooth"
- "Thêm loại wireless"
- "Tạo type gaming"

### Tạo Headphone:

- "Tạo tai nghe AirPods của Apple loại bluetooth giá 200"
- "Thêm tai nghe WH-1000XM4 của Sony loại wireless giá 300"

### Xem danh sách:

- "Xem brands"
- "Hiển thị tai nghe"
- "Danh sách type"

## 🛠️ Xử lý sự cố:

### Ollama không chạy:

```bash
# Windows: Restart Ollama service
# Hoặc chạy thủ công:
ollama serve
```

### Model không tải được:

```bash
# Kiểm tra dung lượng đĩa
# Thử model nhỏ hơn:
ollama pull llama3.2:1b    # Model 1B parameters (nhỏ hơn)
```

### API lỗi:

- Kiểm tra Ollama đang chạy: `ollama list`
- Kiểm tra health: `http://127.0.0.1:8000/ai/health`
- Fallback tự động về rule-based nếu Ollama lỗi

## 📊 So sánh Models:

| Model       | Size | RAM cần | Tốc độ     | Chất lượng |
| ----------- | ---- | ------- | ---------- | ---------- |
| llama3.2:1b | ~1GB | 4GB     | ⭐⭐⭐⭐⭐ | ⭐⭐⭐     |
| llama3.2    | ~2GB | 8GB     | ⭐⭐⭐⭐   | ⭐⭐⭐⭐   |
| llama2      | ~4GB | 8GB     | ⭐⭐⭐     | ⭐⭐⭐⭐   |
| mistral     | ~4GB | 8GB     | ⭐⭐⭐⭐   | ⭐⭐⭐⭐   |
| codellama   | ~7GB | 16GB    | ⭐⭐       | ⭐⭐⭐⭐⭐ |

## 🎉 Lợi ích:

- ✅ **Hoàn toàn miễn phí**
- ✅ **Chạy offline**
- ✅ **Không giới hạn requests**
- ✅ **Bảo mật tuyệt đối**
- ✅ **Tốc độ tốt**
- ✅ **Fallback tự động** về rule-based

**Bạn đã có AI thông minh hoàn toàn miễn phí! 🚀**
