# Web Search Setup cho Chatbot

## Tính năng mới

Chatbot giờ có thể tìm kiếm sản phẩm tai nghe THẬT trên thị trường khi user yêu cầu.

## Cách hoạt động

### 1. Tự động phát hiện

Khi user nói các từ khóa như:

- "tạo sản phẩm **thật** của Samsung"
- "thêm tai nghe **mới nhất** của Sony"
- "tạo bluetooth **2024** của Apple"
- "sản phẩm **trên thị trường** của JBL"

→ Hệ thống tự động tìm kiếm sản phẩm thật

### 2. Hai chế độ hoạt động

#### A. Với Tavily API (Khuyến nghị - Search thật trên web)

- Đăng ký miễn phí tại: https://tavily.com (1000 requests/tháng)
- Thêm API key vào file `.env`:

```env
TAVILY_API_KEY=tvly-your-api-key-here
```

#### B. Fallback Mode (Không cần API)

- Nếu không có `TAVILY_API_KEY`, hệ thống dùng database có sẵn
- Database chứa ~50+ sản phẩm phổ biến của các hãng (cập nhật 2024-2025):
  - Samsung: Galaxy Buds 3 Pro, Buds 2 Pro, Buds FE
  - Sony: WH-1000XM5, WF-1000XM5, LinkBuds S
  - Apple: AirPods Pro 2 USB-C, AirPods 3, AirPods Max
  - Asus: ROG Delta S Wireless, ROG Cetra TWS
  - JBL: Tour Pro 2, Live Pro 2, Quantum 910
  - Bose: QuietComfort Ultra, QC Earbuds II
  - Beats: Studio Pro, Fit Pro
  - Sennheiser: Momentum 4, Momentum TWS 3

### 3. Ví dụ sử dụng

**User:** "tạo bluetooth thật của Samsung"

**Không có web search (cũ):**

```json
{
  "name": "Samsung Bluetooth Headphone",
  "brand_slug": "samsung",
  "type_slug": "bluetooth",
  "price": 500000
}
```

❌ Tên chung chung, không thực tế

**Có web search (mới):**

```json
{
  "items": [
    {
      "name": "Samsung Galaxy Buds 3 Pro",
      "brand_slug": "samsung",
      "type_slug": "bluetooth",
      "price": 5490000
    },
    {
      "name": "Samsung Galaxy Buds 2 Pro",
      "brand_slug": "samsung",
      "type_slug": "bluetooth",
      "price": 4490000
    }
  ]
}
```

✅ Tên sản phẩm thật, giá thật

## Cài đặt (Tùy chọn)

### Option 1: Sử dụng Tavily API (Khuyến nghị)

```bash
# 1. Đăng ký tại https://tavily.com
# 2. Lấy API key
# 3. Thêm vào .env
echo "TAVILY_API_KEY=tvly-xxxxx" >> .env
```

### Option 2: Chỉ dùng Fallback (Không cần setup gì)

Hệ thống tự động dùng database có sẵn nếu không có API key

## Test

```bash
# Khởi động server
uvicorn main:app --reload

# Test với curl
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "tạo bluetooth thật của Samsung"
  }'
```

**Response mong đợi:**

```
Đã tạo 2 tai nghe:
- Samsung Galaxy Buds 3 Pro (Samsung)
- Samsung Galaxy Buds 2 Pro (Samsung)
```

## Brands được hỗ trợ

- Samsung
- Sony
- Apple
- Asus
- JBL
- Bose
- Beats
- Sennheiser

## Types được hỗ trợ

- Bluetooth / Wireless
- Gaming
- Over-ear
- True Wireless (TWS)

## Cập nhật database sản phẩm

File: `services/web_search.py`

Để thêm sản phẩm mới vào fallback database:

```python
products_db = {
    "samsung": {
        "bluetooth": [
            {"name": "Samsung Galaxy Buds 3 Pro", "price": 5490000, "description": "..."},
            # Thêm sản phẩm mới ở đây
        ]
    }
}
```

## Troubleshooting

**Lỗi: "Tavily API failed"**
→ Kiểm tra API key trong `.env` hoặc để hệ thống dùng fallback mode

**Sản phẩm không được tìm thấy**
→ Thử các từ khóa: "thật", "mới nhất", "2024", "trên thị trường"

**AI vẫn tạo tên chung chung**
→ Kiểm tra prompt trong `services/headphone_prompts.py` đã được cập nhật chưa
