from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from schemas.chatbot import ChatRequest, ChatResponse
import database
from services.ai_client import AIClient
from services.headphone_prompts import get_prompt_for_intent, detect_intent
from services.web_search import WebSearchClient
import json
import re
from crud.brand import create_brand, delete_brand, get_brands, get_brand_by_id, update_brand, create_brands_bulk
from crud.type import create_type, delete_type, get_types, get_type_by_id, update_type, create_types_bulk
from crud.headphone import create_headphone, delete_headphone, get_headphones, get_headphone_by_id, update_headphone, create_headphones_bulk
from crud.chat import create_session, get_session_with_messages, add_message
# Import schemas cho CRUD operations
from schemas.brand import BrandCreate, BrandUpdate
from schemas.type import TypeCreate, TypeUpdate
from schemas.headphone import HeadphoneCreate, HeadphoneUpdate

router = APIRouter(prefix="/chat", tags=["Chatbot"])

def get_db_context(db: Session) -> str:
    """Lấy context từ database để cung cấp cho AI"""
    try:
        brands = get_brands(db)
        types = get_types(db)
        headphones = get_headphones(db)
        
        context = """
THÔNG TIN CỬA HÀNG TAI NGHE:

TỔNG QUAN:"""
        
        context += f"\n- Có {len(brands)} thương hiệu: {', '.join([b.name for b in brands])}"
        context += f"\n- Có {len(types)} loại sản phẩm: {', '.join([t.name for t in types])}"
        context += f"\n- Có {len(headphones)} tai nghe trong kho"
        
        context += """

TAI NGHE HIỆN CÓ:"""
        
        if headphones:
            for h in headphones:
                brand_name = h.brand.name if h.brand else "Không rõ"
                type_name = h.type.name if h.type else "Không rõ" 
                price_str = f"{h.price:,.0f}đ" if h.price else "Liên hệ"
                context += f"\n- {h.name} ({brand_name} - {type_name}): {price_str}"
        else:
            context += "\n- Hiện tại chưa có tai nghe nào"
            
        context += """

HƯỚNG DẪN TƯ VẤN:
- Khi khách hỏi về brands: trả lời chính xác số lượng và tên các thương hiệu tai nghe
- Khi khách hỏi về types: nói về các loại tai nghe có sẵn (bluetooth, wireless, headphones)
- Khi khách hỏi về tai nghe: mô tả chi tiết từng tai nghe trong kho
- Luôn dựa vào dữ liệu thực, không bịa đặt
"""
        
        return context
        
    except Exception as e:
        return f"\nLỗi đọc database: {str(e)}\n💡 Hãy liên hệ quản lý để cập nhật thông tin kho hàng."

@router.get("/db-info")
async def get_database_info(db: Session = Depends(database.get_db)):
    """Lấy thông tin từ database"""
    try:
        brands = get_brands(db)
        types = get_types(db)
        headphones = get_headphones(db)
        
        return {
            "success": True,
            "brands_count": len(brands),
            "brands": [b.name for b in brands],
            "types_count": len(types),
            "types": [t.name for t in types],
            "products_count": len(headphones),
            "products": [{"name": h.name, "price": h.price} for h in headphones]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, request: Request, db: Session = Depends(database.get_db)):
    ai: AIClient = request.app.state.ai_client
    if ai is None:
        raise HTTPException(status_code=503, detail="AI service not available")

    # 🔥 QUẢN LÝ CHAT SESSION
    session_id = req.session_id
    
    # Tạo session mới nếu chưa có
    if not session_id:
        session = create_session(db)
        session_id = session.id
    else:
        # Kiểm tra session có tồn tại không
        session = get_session_with_messages(db, session_id, limit=10)  # Lấy 10 tin nhắn gần nhất
        if not session:
            # Session không tồn tại, tạo mới
            session = create_session(db)
            session_id = session.id
    
    # Lưu tin nhắn của user
    add_message(db, session_id, "user", req.message)
    
    # Helper function để lưu response
    def save_and_return(reply: str):
        """Lưu assistant reply và trả về response"""
        add_message(db, session_id, "assistant", reply)
        return ChatResponse(reply=reply, session_id=session_id)

    intent = detect_intent(req.message)

    # ===========================
    # 🔍 WEB SEARCH FOR REAL PRODUCTS
    # ===========================
    # Detect if user wants to create real/latest products from the market
    search_keywords = [
        r'\b(thật|thực|real|actual|global|latest|mới nhất|hiện tại|2024|2025)\b',
        r'\b(trên thị trường|on market|available)\b',
        r'\b(sản phẩm.*của)\b'
    ]
    should_search = any(re.search(pattern, req.message.lower()) for pattern in search_keywords)
    
    web_search_results = None
    if should_search and intent == "product_management":
        # Extract brand and type from message
        brand_match = re.search(r'\b(samsung|sony|apple|asus|jbl|bose|beats|sennheiser)\b', req.message.lower())
        type_match = re.search(r'\b(bluetooth|wireless|gaming|gaming)\b', req.message.lower())
        
        if brand_match:
            brand = brand_match.group(1).capitalize()
            product_type = type_match.group(1) if type_match else "bluetooth"
            
            # Search for real products
            search_client = WebSearchClient()
            try:
                products = await search_client.search_headphones(brand, product_type, limit=3)
                if products:
                    web_search_results = {
                        "brand": brand,
                        "type": product_type,
                        "products": products
                    }
            except Exception as e:
                print(f"Web search error: {e}")

    # ===========================
    # 🔥 CASE 1 — CRUD MANAGEMENT
    # ===========================
    if intent == "product_management":
        system_prompt = get_prompt_for_intent("product_management")

        # Add web search results to prompt if available
        web_context = ""
        if web_search_results:
            web_context = f"\n\nSẢN PHẨM THỰC TẾ TÌM ĐƯỢC TRÊN THỊ TRƯỜNG ({web_search_results['brand']} {web_search_results['type']}):\n"
            for p in web_search_results['products']:
                price_str = f"{p['price']:,}đ" if p['price'] else "Liên hệ"
                web_context += f"- {p['name']}: {price_str}\n"
            web_context += "\nHÃY SỬ DỤNG CÁC TÊN SẢN PHẨM THẬT NÀY thay vì tên chung chung.\n"

        user_prompt = f"{system_prompt}{web_context}\n\nUser: {req.message}\n\nTRẢ VỀ CHỈ 1 JSON:"

        ai_reply = await ai.generate(user_prompt, max_tokens=500, temperature=0)

        # Clean và parse JSON AI trả về
        try:
            # Loại bỏ markdown code blocks nếu có
            ai_reply_clean = ai_reply.strip()
            if ai_reply_clean.startswith("```"):
                lines = ai_reply_clean.split("\n")
                ai_reply_clean = "\n".join(lines[1:])
            if ai_reply_clean.endswith("```"):
                lines = ai_reply_clean.rsplit("\n", 1)
                ai_reply_clean = lines[0]
            ai_reply_clean = ai_reply_clean.strip()
            
            # 🔥 EXTRACT JSON với balanced braces
            start_idx = ai_reply_clean.find("{")
            if start_idx == -1:
                return ChatResponse(reply=f"Không tìm thấy JSON object trong response:\n{ai_reply}")
            
            # Đếm số lượng { và } để tìm JSON object hoàn chỉnh
            brace_count = 0
            end_idx = -1
            
            for i in range(start_idx, len(ai_reply_clean)):
                char = ai_reply_clean[i]
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if end_idx == -1:
                return ChatResponse(reply=f"JSON không đóng đủ dấu ngoặc:\n{ai_reply}")
            
            json_str = ai_reply_clean[start_idx:end_idx+1]
            
            # 🔥 LÀM SẠCH JSON - Loại bỏ trailing comma và whitespace
            json_str = json_str.strip()
            # Loại bỏ trailing comma trước }
            json_str = json_str.replace(",\n}", "\n}").replace(", }", " }")
            json_str = json_str.replace(",}", "}")
            
            # Parse JSON
            try:
                crud = json.loads(json_str)
            except json.JSONDecodeError as parse_err:
                # Thử làm sạch thêm - loại bỏ comments
                json_str_clean = "\n".join([
                    line for line in json_str.split("\n") 
                    if not line.strip().startswith("//")
                ])
                crud = json.loads(json_str_clean)
            
            # Clean up data - remove auto-generated fields
            if "data" in crud and isinstance(crud["data"], dict):
                crud["data"].pop("id", None)
                crud["data"].pop("slug", None)
            
            if "items" in crud and isinstance(crud["items"], list):
                for item in crud["items"]:
                    if isinstance(item, dict):
                        item.pop("id", None)
                        item.pop("slug", None)
            
            # Validate JSON structure
            if not isinstance(crud, dict):
                return ChatResponse(reply=f"JSON phải là object, không phải {type(crud).__name__}:\n{ai_reply}")
                
        except json.JSONDecodeError as je:
            # In ra JSON string để debug
            debug_info = f"JSON string:\n```\n{json_str if 'json_str' in locals() else 'N/A'}\n```\n\n"
            return ChatResponse(reply=f"JSON không hợp lệ từ AI: {crud if 'crud' in locals() else ai_reply} Lỗi: {str(je)}\n\n{debug_info}")
        except Exception as e:
            return ChatResponse(reply=f"Lỗi parse JSON:\n{ai_reply}\n\nLỗi: {str(e)}")

        action = crud.get("action")
        resource = crud.get("resource")
        item_id = crud.get("id")
        data = crud.get("data")
        items = crud.get("items")  # Cho bulk create
        
        # 🔥 FALLBACK: Nếu action="create_bulk" nhưng dùng "data" thay vì "items"
        if action == "create_bulk" and not items and isinstance(data, list):
            items = data
            data = None

        # Validate data structure cho CREATE/UPDATE
        if action in ["create", "update"]:
            if not isinstance(data, dict):
                return ChatResponse(reply=f"Lỗi: 'data' phải là object {{}}, không phải {type(data).__name__}.\n\n"
                                         f"AI trả về:\n{json.dumps(crud, indent=2, ensure_ascii=False)}\n\n"
                                         f"Nếu bạn muốn tạo nhiều sản phẩm, hãy dùng action 'create_bulk' với 'items':[]")
            if not data:
                return ChatResponse(reply=f"Lỗi: 'data' không được rỗng cho action '{action}'")
        
        # Validate items structure cho CREATE_BULK
        if action == "create_bulk":
            if not isinstance(items, list):
                return ChatResponse(reply=f"Lỗi: 'items' phải là array [], không phải {type(items).__name__}.\n\n"
                                         f"AI trả về:\n{json.dumps(crud, indent=2, ensure_ascii=False)}")
            if not items:
                return ChatResponse(reply=f"Lỗi: 'items' không được rỗng cho action 'create_bulk'")

        try:
            # ---------- CREATE BULK ----------
            if action == "create_bulk":
                if resource == "brand":
                    brand_schemas = [BrandCreate(**item) for item in items]
                    created, errors = create_brands_bulk(db, brand_schemas)
                    
                    result = f"Đã tạo {len(created)} brands:\n"
                    result += "\n".join([f"- {b.name}" for b in created])
                    if errors:
                        result += f"\n\nLỗi ({len(errors)}):\n" + "\n".join([f"- {e}" for e in errors])
                    return ChatResponse(reply=result)

                if resource == "type":
                    type_schemas = [TypeCreate(**item) for item in items]
                    created, errors = create_types_bulk(db, type_schemas)
                    
                    result = f"Đã tạo {len(created)} types:\n"
                    result += "\n".join([f"- {t.name}" for t in created])
                    if errors:
                        result += f"\n\nLỗi ({len(errors)}):\n" + "\n".join([f"- {e}" for e in errors])
                    return ChatResponse(reply=result)

                if resource == "headphone":
                    # Auto-infer missing brand_slug and type_slug from user message
                    for item in items:
                        # Infer type_slug if missing
                        if not item.get("type_slug"):
                            type_keywords = {
                                "bluetooth": r'\b(bluetooth|bt|wireless)\b',
                                "gaming": r'\b(gaming|game|chơi game)\b',
                                "wired": r'\b(wired|có dây)\b',
                                "over-ear": r'\b(over.ear|overear)\b',
                            }
                            for type_name, pattern in type_keywords.items():
                                if re.search(pattern, req.message.lower()):
                                    item["type_slug"] = type_name
                                    break
                        
                        # Infer brand_slug if missing
                        if not item.get("brand_slug"):
                            brand_keywords = r'\b(samsung|sony|apple|asus|jbl|bose|beats|sennheiser)\b'
                            brand_match = re.search(brand_keywords, req.message.lower())
                            if brand_match:
                                item["brand_slug"] = brand_match.group(1)
                        
                        # Validate price
                        if "price" not in item or item.get("price") is None:
                            item["price"] = 500000  # Giá mặc định
                        else:
                            try:
                                item["price"] = int(item["price"])
                            except (ValueError, TypeError):
                                item["price"] = 500000
                    
                    # CRUD sẽ tự động chuyển đổi slug/name thành UUID
                    headphone_schemas = [HeadphoneCreate(**item) for item in items]
                    created, errors = create_headphones_bulk(db, headphone_schemas)
                    
                    result = f"Đã tạo {len(created)} tai nghe:\n"
                    for h in created:
                        brand_info = f" ({h.brand.name})" if h.brand else ""
                        result += f"- {h.name}{brand_info}\n"
                    if errors:
                        result += f"\nLỗi ({len(errors)}):\n" + "\n".join([f"- {e}" for e in errors])
                    return ChatResponse(reply=result.strip())

            # ---------- CREATE ----------
            if action == "create":
                if resource == "brand":
                    brand_schema = BrandCreate(**data)
                    new_b = create_brand(db, brand_schema)
                    return ChatResponse(reply=f"Đã tạo brand: {new_b.name}")

                if resource == "type":
                    type_schema = TypeCreate(**data)
                    new_t = create_type(db, type_schema)
                    return ChatResponse(reply=f"Đã tạo type: {new_t.name}")

                if resource == "headphone":
                    # Validate dữ liệu headphone
                    if "name" not in data:
                        return ChatResponse(reply="Lỗi: Thiếu 'name' (tên tai nghe) trong data")
                    if "price" not in data or data.get("price") is None:
                        return ChatResponse(reply="Lỗi: Thiếu 'price' (giá tai nghe). Vui lòng cung cấp giá tiền (VD: 500000)")
                    
                    # Auto-infer missing brand_slug and type_slug from user message
                    if not data.get("type_slug"):
                        type_keywords = {
                            "bluetooth": r'\b(bluetooth|bt|wireless)\b',
                            "gaming": r'\b(gaming|game|chơi game)\b',
                            "wired": r'\b(wired|có dây)\b',
                            "over-ear": r'\b(over.ear|overear)\b',
                        }
                        for type_name, pattern in type_keywords.items():
                            if re.search(pattern, req.message.lower()):
                                data["type_slug"] = type_name
                                break
                    
                    if not data.get("brand_slug"):
                        brand_keywords = r'\b(samsung|sony|apple|asus|jbl|bose|beats|sennheiser)\b'
                        brand_match = re.search(brand_keywords, req.message.lower())
                        if brand_match:
                            data["brand_slug"] = brand_match.group(1)
                    
                    # Validate price là số
                    try:
                        price = int(data.get("price"))
                        if price < 0:
                            return ChatResponse(reply="Lỗi: Giá không được âm")
                        data["price"] = price
                    except (ValueError, TypeError):
                        return ChatResponse(reply=f"Lỗi: Giá phải là số nguyên, nhận được: {data.get('price')}")
                    
                    # CRUD sẽ tự động chuyển đổi slug/name thành UUID
                    headphone_schema = HeadphoneCreate(**data)
                    new_h = create_headphone(db, headphone_schema)
                    
                    # Thông báo chi tiết
                    brand_info = f" - Thương hiệu: {new_h.brand.name}" if new_h.brand else ""
                    type_info = f" - Loại: {new_h.type.name}" if new_h.type else ""
                    return ChatResponse(reply=f"Đã thêm tai nghe: {new_h.name}{brand_info}{type_info}")

            # ---------- READ ----------
            if action == "read":
                if resource == "brand":
                    if item_id:
                        brand = get_brand_by_id(db, item_id)
                        if brand:
                            return ChatResponse(reply=f"Brand: {brand.name} (ID: {brand.id}, Slug: {brand.slug})")
                        else:
                            return ChatResponse(reply=f"Không tìm thấy brand với ID: {item_id}")
                    else:
                        brands = get_brands(db)
                        if brands:
                            brand_list = "\n".join([f"- {b.name} (ID: {b.id})" for b in brands])
                            return ChatResponse(reply=f"Danh sách thương hiệu ({len(brands)}):\n{brand_list}")
                        else:
                            return ChatResponse(reply="Chưa có thương hiệu nào trong hệ thống.")

                if resource == "type":
                    if item_id:
                        type_obj = get_type_by_id(db, item_id)
                        if type_obj:
                            return ChatResponse(reply=f"Type: {type_obj.name} (ID: {type_obj.id}, Slug: {type_obj.slug})")
                        else:
                            return ChatResponse(reply=f"Không tìm thấy type với ID: {item_id}")
                    else:
                        types = get_types(db)
                        if types:
                            type_list = "\n".join([f"- {t.name} (ID: {t.id})" for t in types])
                            return ChatResponse(reply=f"Danh sách loại tai nghe ({len(types)}):\n{type_list}")
                        else:
                            return ChatResponse(reply="Chưa có loại tai nghe nào trong hệ thống.")

                if resource == "headphone":
                    if item_id:
                        headphone = get_headphone_by_id(db, item_id)
                        if headphone:
                            brand_name = headphone.brand.name if headphone.brand else "Chưa rõ"
                            type_name = headphone.type.name if headphone.type else "Chưa rõ"
                            price_str = f"{headphone.price:,.0f}đ" if headphone.price else "Liên hệ"
                            return ChatResponse(reply=f"Tai nghe: {headphone.name}\nThương hiệu: {brand_name}\nLoại: {type_name}\n💰 Giá: {price_str}\nID: {headphone.id}")
                        else:
                            return ChatResponse(reply=f"Không tìm thấy tai nghe với ID: {item_id}")
                    else:
                        headphones = get_headphones(db)
                        if headphones:
                            hp_list = []
                            for h in headphones:
                                brand_name = h.brand.name if h.brand else "Chưa rõ"
                                price_str = f"{h.price:,.0f}đ" if h.price else "Liên hệ"
                                hp_list.append(f"- {h.name} ({brand_name}) - {price_str}")
                            hp_text = "\n".join(hp_list)
                            return ChatResponse(reply=f"Danh sách tai nghe ({len(headphones)}):\n{hp_text}")
                        else:
                            return ChatResponse(reply="Chưa có tai nghe nào trong kho.")

            # ---------- UPDATE ----------
            if action == "update":
                if not item_id:
                    return ChatResponse(reply="Cần cung cấp ID để cập nhật.")
                
                if resource == "brand":
                    brand_schema = BrandUpdate(**data)
                    updated_brand = update_brand(db, item_id, brand_schema)
                    return ChatResponse(reply=f"Đã cập nhật brand: {updated_brand.name}")

                if resource == "type":
                    type_schema = TypeUpdate(**data)
                    updated_type = update_type(db, item_id, type_schema)
                    return ChatResponse(reply=f"Đã cập nhật type: {updated_type.name}")

                if resource == "headphone":
                    headphone_schema = HeadphoneUpdate(**data)
                    updated_headphone = update_headphone(db, item_id, headphone_schema)
                    return ChatResponse(reply=f"Đã cập nhật tai nghe: {updated_headphone.name}")

            # ---------- DELETE ----------
            if action == "delete":
                if resource == "brand":
                    delete_brand(db, item_id)
                    return ChatResponse(reply=f"Đã xoá brand: {item_id}")

                if resource == "type":
                    delete_type(db, item_id)
                    return ChatResponse(reply=f"Đã xoá type: {item_id}")

                if resource == "headphone":
                    delete_headphone(db, item_id)
                    return ChatResponse(reply=f"Đã xoá tai nghe: {item_id}")

            return ChatResponse(reply="Hành động hoặc resource CRUD không hợp lệ.")
        
        except ValueError as ve:
            return ChatResponse(reply=f"Lỗi validation: {str(ve)}")
        except Exception as e:
            return ChatResponse(reply=f"Lỗi xử lý CRUD: {str(e)}")

    # ===========================
    # 🔥 CASE 2 — NORMAL CHAT / TƯ VẤN
    # ===========================
    db_context = get_db_context(db)
    system_prompt = req.system_prompt or get_prompt_for_intent(intent)

    # 🔥 THÊM CHAT HISTORY CONTEXT
    chat_history = ""
    if session and session.messages:
        history_messages = session.messages[:-1]  # Bỏ tin nhắn cuối
        if history_messages:
            chat_history = "\n\nLỊCH SỬ HỘI THOẠI:\n"
            for msg in history_messages[-6:]:
                role_label = "Khách hàng" if msg.role == "user" else "Trợ lý"
                chat_history += f"{role_label}: {msg.content}\n"
            chat_history += "\n"

    prompt = (
        f"{system_prompt}\n"
        f"{db_context}\n"
        f"{chat_history}"
        f"Khách hàng: {req.message}\n\n"
        f"Trợ lý:"
    )

    ai_reply = await ai.generate(prompt, max_tokens=900, temperature=0.7)

    # Lưu assistant reply
    add_message(db, session_id, "assistant", ai_reply)

    return ChatResponse(reply=ai_reply, session_id=session_id)
