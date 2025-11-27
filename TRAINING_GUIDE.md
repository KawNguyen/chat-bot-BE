# Hướng Dẫn Train Model Cho Cửa Hàng Đồng Hồ

## 🎯 Phương Pháp 1: Prompt Engineering (KHUYÊN DÙNG)

**Ưu điểm:** Nhanh, dễ, không cần training
**Thời gian:** 5 phút

### Đã triển khai:

System prompts chuyên biệt cho cửa hàng đồng hồ
Phát hiện ý định tự động (tư vấn/quản lý)  
Context sản phẩm động
Endpoint `/chat/watch-advisor` chuyên biệt

### Sử dụng:

```bash
curl -X POST http://127.0.0.1:8000/chat/watch-advisor \
-H "Content-Type: application/json" \
-d '{"message": "Tôi muốn mua đồng hồ nam giá 5 triệu"}'
```

## 🔧 Phương Pháp 2: Fine-tuning Mistral (Nâng cao)

### Bước 1: Chuẩn bị dữ liệu

```python
# File: prepare_training_data.py
import json

# Chuyển đổi dữ liệu training thành format Mistral
training_data = []
for item in WATCH_TRAINING_DATA:
    formatted = {
        "messages": [
            {"role": "system", "content": WATCH_STORE_SYSTEM_PROMPT},
            {"role": "user", "content": item["input"]},
            {"role": "assistant", "content": item["output"]}
        ]
    }
    training_data.append(formatted)

# Lưu file JSONL
with open("watch_training.jsonl", "w", encoding="utf-8") as f:
    for item in training_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
```

### Bước 2: Fine-tuning với HuggingFace

```python
# pip install transformers datasets peft accelerate
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import Dataset
import torch

# Load model và tokenizer
model_name = "mistralai/Mistral-7B-Instruct-v0.3"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16)

# Setup LoRA (Low-Rank Adaptation)
from peft import LoraConfig, get_peft_model, TaskType

lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    inference_mode=False,
    r=8,
    lora_alpha=32,
    lora_dropout=0.1
)

model = get_peft_model(model, lora_config)

# Training arguments
training_args = TrainingArguments(
    output_dir="./watch-mistral-finetuned",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=2,
    warmup_steps=10,
    logging_steps=1,
    save_strategy="epoch",
    evaluation_strategy="no",
    learning_rate=2e-4,
    fp16=True,
)

# Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
)

trainer.train()
```

### Bước 3: Sử dụng model đã train

```python
# Load fine-tuned model
from peft import PeftModel

base_model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3")
model = PeftModel.from_pretrained(base_model, "./watch-mistral-finetuned")
```

## 🚀 Phương Pháp 3: RAG (Retrieval-Augmented Generation)

### Cài đặt vector database

```python
# pip install chromadb sentence-transformers
import chromadb
from sentence_transformers import SentenceTransformer

# Tạo vector database với thông tin sản phẩm
client = chromadb.Client()
collection = client.create_collection(name="watches")

# Embed sản phẩm
embedder = SentenceTransformer('all-MiniLM-L6-v2')

products = [
    "Rolex Submariner: Đồng hồ lặn cao cấp, chống nước 300m, giá 250 triệu",
    "Omega Speedmaster: Đồng hồ phi hành gia, chronograph, giá 150 triệu",
    "Citizen Eco-Drive: Đồng hồ năng lượng mặt trời, giá 5 triệu"
]

for i, product in enumerate(products):
    embedding = embedder.encode(product)
    collection.add(
        embeddings=[embedding],
        documents=[product],
        ids=[str(i)]
    )
```

### Tích hợp RAG vào AI client

```python
# Trong ai_client.py
async def generate_with_context(self, prompt: str, context_docs: list = None):
    if context_docs:
        context = "\n".join([f"- {doc}" for doc in context_docs])
        enhanced_prompt = f"Context sản phẩm:\n{context}\n\nKhách hàng: {prompt}\n\nTrả lời:"
    else:
        enhanced_prompt = prompt

    return await self.generate(enhanced_prompt)
```

## 📊 So sánh các phương pháp

| Phương pháp        | Độ khó     | Thời gian | Hiệu quả   | Chi phí  |
| ------------------ | ---------- | --------- | ---------- | -------- |
| Prompt Engineering | ⭐         | 5 phút    | ⭐⭐⭐⭐   | Miễn phí |
| Fine-tuning        | ⭐⭐⭐⭐⭐ | 2-4 giờ   | ⭐⭐⭐⭐⭐ | GPU cao  |
| RAG                | ⭐⭐⭐     | 30 phút   | ⭐⭐⭐⭐   | Thấp     |

## 🎉 Kết luận

**Khuyên dùng:** Bắt đầu với Prompt Engineering (đã triển khai), sau đó thêm RAG nếu cần context phức tạp hơn.

Fine-tuning chỉ cần thiết khi:

- Có >1000 câu hỏi training chất lượng cao
- Cần phong cách trả lời rất đặc biệt
- Có ngân sách GPU training

## 🔧 Sử dụng ngay

Server hiện tại đã có:

- `/chat/` - Chat thông minh với detect intent
- `/chat/watch-advisor` - Tư vấn chuyên biệt đồng hồ
- `/chat/crud` - Quản lý sản phẩm

Hãy test thử và feedback để tôi cải thiện!
