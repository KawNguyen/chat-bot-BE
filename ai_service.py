import os
import json
import re
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from database import get_db

# Ollama import
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Import CRUD functions
from crud.brand import create_brand, get_brands, get_brand_by_slug
from crud.type import create_type, get_types, get_type_by_slug
from crud.headphone import create_headphone, get_headphones, get_headphone_by_slug

# Import schemas
from schemas.brand import BrandCreate
from schemas.type import TypeCreate
from schemas.headphone import HeadphoneCreate

class AIService:
    def __init__(self):
        # Ollama configuration (chỉ dùng Ollama)
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        
        # Kiểm tra Ollama có sẵn không
        self.ollama_available = self._check_ollama_available()
        
        # Xác định LLM type
        self.llm_type = "ollama" if self.ollama_available else "rule_based"
    
    def _check_ollama_available(self) -> bool:
        """Kiểm tra Ollama có chạy không"""
        if not HAS_REQUESTS:
            return False
            
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
        
        
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """Xử lý tin nhắn bằng Ollama hoặc rule-based"""
        try:
            if self.llm_type == "ollama":
                return self._process_with_ollama(message)
            else:
                return self._process_with_rules(message)
        except Exception as e:
            # Fallback về rule-based nếu có lỗi
            print(f"Lỗi {self.llm_type}: {str(e)}, chuyển sang rule-based")
            return self._process_with_rules(message)
    
    def _process_with_ollama(self, message: str) -> Dict[str, Any]:
        """Xử lý tin nhắn bằng Ollama"""
        try:
            # Prompt cho Ollama để phân tích intent
            prompt = f"""Bạn là AI assistant cho cửa hàng tai nghe. Phân tích yêu cầu sau và trả về JSON:

Yêu cầu: "{message}"

Phân tích và trả về JSON với định dạng chính xác:
{{
    "action": "create_brand|create_type|create_headphone|get_brands|get_types|get_headphones|chat",
    "data": {{
        "name": "tên (nếu có)",
        "brand_name": "tên brand (nếu có)", 
        "type_name": "tên type (nếu có)",
        "price": 0
    }}
}}

Các action:
- create_brand: tạo brand/thương hiệu mới
- create_type: tạo type/loại tai nghe mới
- create_headphone: tạo tai nghe mới
- get_brands: xem danh sách brands
- get_types: xem danh sách types  
- get_headphones: xem danh sách tai nghe
- chat: trò chuyện thông thường

Chỉ trả về JSON, không giải thích thêm."""

            # Gọi Ollama API
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Ít sáng tạo để có kết quả chính xác
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate", 
                json=payload, 
                timeout=30
            )
            
            if response.status_code != 200:
                return self._process_with_rules(message)
            
            result = response.json()
            ollama_response = result.get("response", "").strip()
            
            # Parse JSON response từ Ollama
            try:
                # Tìm JSON trong response
                json_start = ollama_response.find('{')
                json_end = ollama_response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = ollama_response[json_start:json_end]
                    parsed = json.loads(json_str)
                    
                    return self._execute_parsed_action(parsed, message)
                else:
                    # Nếu không parse được JSON, dùng rule-based
                    return self._process_with_rules(message)
                    
            except json.JSONDecodeError:
                # Nếu JSON không hợp lệ, dùng rule-based
                return self._process_with_rules(message)
                
        except Exception as e:
            print(f"Ollama error: {str(e)}")
            return self._process_with_rules(message)
    
    def _execute_parsed_action(self, parsed_data: Dict, original_message: str) -> Dict[str, Any]:
        """Thực hiện action từ kết quả parse của LLM"""
        action = parsed_data.get("action", "chat")
        data = parsed_data.get("data", {})
        
        db = next(get_db())
        try:
            if action == "create_brand":
                return self._execute_create_brand(data, db)
            elif action == "create_type":
                return self._execute_create_type(data, db)
            elif action == "create_headphone":
                return self._execute_create_headphone(data, db)
            elif action == "get_brands":
                return self._execute_get_brands(db)
            elif action == "get_types":
                return self._execute_get_types(db)
            elif action == "get_headphones":
                return self._execute_get_headphones(db)
            else:
                return {
                    "success": True,
                    "response": f"Xin chào! Tôi có thể giúp bạn quản lý cửa hàng tai nghe. Bạn có thể yêu cầu tôi tạo brand, type, tai nghe hoặc xem danh sách.",
                    "action": "chat"
                }
        finally:
            db.close()
    
    def _process_with_rules(self, message: str) -> Dict[str, Any]:
        """Xử lý tin nhắn bằng rule-based (fallback)"""
        message_lower = message.lower()
        
        try:
            # Brand creation
            if any(keyword in message_lower for keyword in ["tạo brand", "thêm brand", "tạo thương hiệu"]):
                name_match = re.search(r"(?:tạo brand|thêm brand|tạo thương hiệu)\s+(.+)", message_lower)
                if name_match:
                    name = name_match.group(1).strip()
                    return self._execute_create_brand({"name": name}, next(get_db()))
            
            # Type creation
            elif any(keyword in message_lower for keyword in ["tạo type", "tạo loại", "thêm type"]):
                name_match = re.search(r"(?:tạo type|tạo loại|thêm type)\s+(.+)", message_lower)
                if name_match:
                    name = name_match.group(1).strip()
                    return self._execute_create_type({"name": name}, next(get_db()))
            
            # Headphone creation
            elif "tạo tai nghe" in message_lower:
                details = self._extract_headphone_details_regex(message)
                if all(k in details for k in ['name', 'brand_name', 'type_name']):
                    return self._execute_create_headphone(details, next(get_db()))
            
            # List operations
            elif any(keyword in message_lower for keyword in ["xem brand", "danh sách brand", "hiển thị brand"]):
                return self._execute_get_brands(next(get_db()))
            elif any(keyword in message_lower for keyword in ["xem tai nghe", "danh sách tai nghe", "hiển thị tai nghe"]):
                return self._execute_get_headphones(next(get_db()))
            elif any(keyword in message_lower for keyword in ["xem type", "danh sách type", "hiển thị type"]):
                return self._execute_get_types(next(get_db()))
            
            return {
                "success": True,
                "response": f"🤖 Xin chào! Tôi có thể giúp bạn:\n\n• Tạo brand: 'Tạo brand Apple'\n• Tạo type: 'Tạo type bluetooth'\n• Tạo tai nghe: 'Tạo tai nghe AirPods của Apple loại bluetooth giá 200'\n• Xem danh sách: 'Xem brands', 'Xem tai nghe'\n\nBạn muốn làm gì?",
                "action": "help",
                "mode": "rule-based"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Lỗi: {str(e)}",
                "mode": "rule-based"
            }
    
    def _extract_headphone_details_regex(self, message: str) -> Dict[str, Any]:
        """Trích xuất thông tin tai nghe bằng regex"""
        details = {}
        
        name_match = re.search(r"tai nghe\s+([^của]+)", message, re.IGNORECASE)
        if name_match:
            details["name"] = name_match.group(1).strip()
        
        brand_match = re.search(r"của\s+([^\s]+)", message, re.IGNORECASE)  
        if brand_match:
            details["brand_name"] = brand_match.group(1).strip()
        
        type_match = re.search(r"loại\s+([^giá]+)", message, re.IGNORECASE)
        if type_match:
            details["type_name"] = type_match.group(1).strip()
        
        price_match = re.search(r"giá\s+(\d+)", message, re.IGNORECASE)
        if price_match:
            details["price"] = int(price_match.group(1))
        else:
            details["price"] = 0
            
        return details
    
    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent using simple keywords (fallback method)"""
        message_lower = message.lower()
        
        # Tạo brand
        if any(keyword in message_lower for keyword in ["tạo brand", "thêm brand", "brand mới", "thương hiệu"]):
            # Tìm tên brand
            patterns = [
                r"(?:tạo|thêm) brand\s+(.+)",
                r"brand\s+(.+)",
                r"thương hiệu\s+(.+)"
            ]
            name = None
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    name = match.group(1).strip()
                    break
            
            return {
                "action": "create_brand",
                "entity": "brand",
                "name": name or "Unknown Brand"
            }
        
        # Tạo type
        elif any(keyword in message_lower for keyword in ["tạo type", "thêm type", "loại tai nghe", "type mới"]):
            patterns = [
                r"(?:tạo|thêm) type\s+(.+)",
                r"type\s+(.+)",
                r"loại (?:tai nghe\s+)?(.+)"
            ]
            name = None
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    name = match.group(1).strip()
                    break
            
            return {
                "action": "create_type",
                "entity": "type", 
                "name": name or "Unknown Type"
            }
        
        # Tạo tai nghe
        elif any(keyword in message_lower for keyword in ["tạo tai nghe", "thêm tai nghe", "tai nghe mới"]):
            return {
                "action": "create_headphone",
                "entity": "headphone",
                "name": "New Headphone",
                "details": self._extract_headphone_details(message)
            }
        
        # Xem danh sách
        elif any(keyword in message_lower for keyword in ["xem", "hiển thị", "danh sách", "có những"]):
            if any(keyword in message_lower for keyword in ["brand", "thương hiệu"]):
                return {"action": "list_brands", "entity": "brand"}
            elif any(keyword in message_lower for keyword in ["type", "loại"]):
                return {"action": "list_types", "entity": "type"}
            elif any(keyword in message_lower for keyword in ["tai nghe", "headphone"]):
                return {"action": "list_headphones", "entity": "headphone"}
        
        # Mặc định
        return {"action": "unknown", "entity": "unknown"}
    
    def _extract_headphone_details(self, message: str) -> Dict[str, Any]:
        """Extract headphone details from message using regex"""
        details = {}
        
        # Tên tai nghe
        name_patterns = [
            r"tai nghe\s+([^của^giá^loại]+)",
            r"(?:tạo|thêm)\s+tai nghe\s+([^của^giá^loại]+)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                details["name"] = match.group(1).strip()
                break
        
        # Brand
        brand_patterns = [
            r"của\s+([^\s^loại^giá]+)",
            r"brand\s+([^\s^loại^giá]+)"
        ]
        for pattern in brand_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                details["brand_name"] = match.group(1).strip()
                break
        
        # Type
        type_patterns = [
            r"loại\s+([^giá^của]+)",
            r"type\s+([^giá^của]+)"
        ]
        for pattern in type_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                details["type_name"] = match.group(1).strip()
                break
        
        # Price
        price_patterns = [
            r"giá\s+(\d+)",
            r"(\d+)\s*(?:đô|đồng|usd|\$)"
        ]
        for pattern in price_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                details["price"] = int(match.group(1))
                break
        
        return details
    
    def _execute_action(self, intent: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """Execute action based on intent (rule-based fallback)"""
        db = next(get_db())
        try:
            action = intent.get("action")
            
            if action == "create_brand":
                return self._create_brand_action(intent, db)
            elif action == "create_type":
                return self._create_type_action(intent, db)
            elif action == "create_headphone":
                return self._create_headphone_action(intent, db, original_message)
            elif action == "list_brands":
                return self._list_brands_action(db)
            elif action == "list_types":
                return self._list_types_action(db)
            elif action == "list_headphones":
                return self._list_headphones_action(db)
            else:
                return {
                    "action": "unknown",
                    "response": "🤖 Xin lỗi, tôi chưa hiểu yêu cầu của bạn. Bạn có thể thử:\n- Tạo brand [tên]\n- Tạo type [tên]\n- Tạo tai nghe [tên] của [brand] loại [type] giá [số]\n- Xem brands/types/tai nghe"
                }
        finally:
            db.close()
    
    def _create_brand_action(self, intent: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Create brand action (rule-based)"""
        name = intent.get("name", "").strip()
        if not name or name == "Unknown Brand":
            return {"action": "create_brand", "response": "❌ Tên brand không được để trống"}
        
        try:
            brand_create = BrandCreate(name=name)
            brand = create_brand(db, brand_create)
            return {
                "action": "create_brand",
                "response": f"✅ Đã tạo brand '{brand.name}' thành công!",
                "data": {"id": brand.id, "name": brand.name, "slug": brand.slug}
            }
        except ValueError as e:
            return {"action": "create_brand", "response": f"❌ Lỗi: {str(e)}"}
    
    def _create_type_action(self, intent: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Create type action (rule-based)"""
        name = intent.get("name", "").strip()
        if not name or name == "Unknown Type":
            return {"action": "create_type", "response": "❌ Tên type không được để trống"}
        
        try:
            type_create = TypeCreate(name=name)
            type_obj = create_type(db, type_create)
            return {
                "action": "create_type",
                "response": f"✅ Đã tạo type '{type_obj.name}' thành công!",
                "data": {"id": type_obj.id, "name": type_obj.name, "slug": type_obj.slug}
            }
        except ValueError as e:
            return {"action": "create_type", "response": f"❌ Lỗi: {str(e)}"}
    
    def _create_headphone_action(self, intent: Dict[str, Any], db: Session, original_message: str) -> Dict[str, Any]:
        """Create headphone action (rule-based)"""
        details = intent.get("details", {})
        
        # Find or create brand
        brand_name = details.get("brand_name")
        if brand_name:
            brand = get_brand_by_slug(db, brand_name.lower().replace(" ", "-"))
            if not brand:
                brand_create = BrandCreate(name=brand_name)
                brand = create_brand(db, brand_create)
            brand_id = brand.id
        else:
            return {"action": "create_headphone", "response": "❌ Không tìm thấy thông tin brand"}
        
        # Find or create type
        type_name = details.get("type_name")
        if type_name:
            type_obj = get_type_by_slug(db, type_name.lower().replace(" ", "-"))
            if not type_obj:
                type_create = TypeCreate(name=type_name)
                type_obj = create_type(db, type_create)
            type_id = type_obj.id
        else:
            return {"action": "create_headphone", "response": "❌ Không tìm thấy thông tin type"}
        
        # Create headphone
        headphone_name = details.get("name", "New Headphone")
        price = details.get("price", 0)
        
        try:
            headphone_create = HeadphoneCreate(name=headphone_name, brand_id=brand_id, type_id=type_id, price=price)
            headphone = create_headphone(db, headphone_create)
            
            return {
                "action": "create_headphone",
                "response": f"✅ Đã tạo tai nghe '{headphone.name}' của {brand.name} loại {type_obj.name} giá {price:,}đ thành công!",
                "data": {"id": headphone.id, "name": headphone.name, "slug": headphone.slug, "brand": brand.name, "type": type_obj.name, "price": headphone.price}
            }
        except Exception as e:
            return {"action": "create_headphone", "response": f"❌ Lỗi: {str(e)}"}
    
    def _list_brands_action(self, db: Session) -> Dict[str, Any]:
        """List all brands (rule-based)"""
        brands = get_brands(db)
        if not brands:
            return {"action": "list_brands", "response": "📝 Chưa có brand nào trong hệ thống"}
        
        response = "📝 **Danh sách brands:**\n"
        for i, brand in enumerate(brands, 1):
            response += f"{i}. {brand.name}\n"
        
        return {"action": "list_brands", "response": response, "data": [{"id": b.id, "name": b.name, "slug": b.slug} for b in brands]}
    
    def _list_types_action(self, db: Session) -> Dict[str, Any]:
        """List all types (rule-based)"""
        types = get_types(db)
        if not types:
            return {"action": "list_types", "response": "📝 Chưa có type nào trong hệ thống"}
        
        response = "📝 **Danh sách types:**\n"
        for i, type_obj in enumerate(types, 1):
            response += f"{i}. {type_obj.name}\n"
        
        return {"action": "list_types", "response": response, "data": [{"id": t.id, "name": t.name, "slug": t.slug} for t in types]}
    
    def _list_headphones_action(self, db: Session) -> Dict[str, Any]:
        """List all headphones (rule-based)"""
        headphones = get_headphones(db)
        if not headphones:
            return {"action": "list_headphones", "response": "🎧 Chưa có tai nghe nào trong hệ thống"}
        
        response = "🎧 **Danh sách tai nghe:**\n"
        for i, headphone in enumerate(headphones, 1):
            brand_name = headphone.brand.name if headphone.brand else "Unknown"
            type_name = headphone.type.name if headphone.type else "Unknown"
            response += f"{i}. {headphone.name} - {brand_name} ({type_name}) - {headphone.price:,}đ\n"
        
        return {"action": "list_headphones", "response": response}
    
    def _handle_function_calls(self, tool_calls, original_message: str) -> Dict[str, Any]:
        """Xử lý function calls từ OpenAI"""
        db = next(get_db())
        results = []
        
        try:
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "create_brand":
                    result = self._execute_create_brand(function_args, db)
                elif function_name == "create_type":
                    result = self._execute_create_type(function_args, db)
                elif function_name == "create_headphone":
                    result = self._execute_create_headphone(function_args, db)
                elif function_name == "get_brands":
                    result = self._execute_get_brands(db)
                elif function_name == "get_types":
                    result = self._execute_get_types(db)
                elif function_name == "get_headphones":
                    result = self._execute_get_headphones(db)
                else:
                    result = {"success": False, "response": f"Function {function_name} không được hỗ trợ"}
                
                results.append(result)
            
            # Tạo response tổng hợp
            if len(results) == 1:
                return results[0]
            else:
                success_results = [r for r in results if r.get("success")]
                if success_results:
                    combined_response = "\n".join([r["response"] for r in success_results])
                    return {
                        "success": True,
                        "response": combined_response,
                        "action": "multiple_actions"
                    }
                else:
                    return {
                        "success": False,
                        "response": "Không thể thực hiện được yêu cầu nào",
                        "action": "error"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "response": f"Lỗi khi thực hiện function: {str(e)}",
                "error": str(e)
            }
        finally:
            db.close()
    
    def _execute_create_brand(self, args: Dict, db: Session) -> Dict[str, Any]:
        """Thực hiện tạo brand"""
        try:
            name = args.get("name", "").strip()
            if not name:
                return {"success": False, "response": "Tên brand không được để trống"}
            
            brand_create = BrandCreate(name=name)
            brand = create_brand(db, brand_create)
            return {
                "success": True,
                "response": f"✅ Đã tạo brand '{brand.name}' thành công!",
                "action": "create_brand",
                "data": {"id": brand.id, "name": brand.name, "slug": brand.slug}
            }
        except ValueError as e:
            return {"success": False, "response": f"❌ Lỗi: {str(e)}", "action": "create_brand"}
    
    def _execute_create_type(self, args: Dict, db: Session) -> Dict[str, Any]:
        """Thực hiện tạo type"""
        try:
            name = args.get("name", "").strip()
            if not name:
                return {"success": False, "response": "Tên type không được để trống"}
            
            type_create = TypeCreate(name=name)
            type_obj = create_type(db, type_create)
            return {
                "success": True,
                "response": f"✅ Đã tạo type '{type_obj.name}' thành công!",
                "action": "create_type",
                "data": {"id": type_obj.id, "name": type_obj.name, "slug": type_obj.slug}
            }
        except ValueError as e:
            return {"success": False, "response": f"❌ Lỗi: {str(e)}", "action": "create_type"}
    
    def _execute_create_headphone(self, args: Dict, db: Session) -> Dict[str, Any]:
        """Thực hiện tạo headphone"""
        try:
            name = args.get("name", "").strip()
            brand_name = args.get("brand_name", "").strip()
            type_name = args.get("type_name", "").strip()
            price = args.get("price", 0)
            
            if not all([name, brand_name, type_name]):
                return {"success": False, "response": "Thiếu thông tin: name, brand_name, type_name"}
            
            # Tìm hoặc tạo brand
            brand = get_brand_by_slug(db, brand_name.lower().replace(" ", "-"))
            if not brand:
                brand_create = BrandCreate(name=brand_name)
                brand = create_brand(db, brand_create)
            
            # Tìm hoặc tạo type
            type_obj = get_type_by_slug(db, type_name.lower().replace(" ", "-"))
            if not type_obj:
                type_create = TypeCreate(name=type_name)
                type_obj = create_type(db, type_create)
            
            # Tạo headphone
            headphone_create = HeadphoneCreate(
                name=name,
                brand_id=brand.id,
                type_id=type_obj.id,
                price=price
            )
            headphone = create_headphone(db, headphone_create)
            
            return {
                "success": True,
                "response": f"✅ Đã tạo tai nghe '{headphone.name}' của {brand.name} loại {type_obj.name} giá {price:,}đ thành công!",
                "action": "create_headphone",
                "data": {
                    "id": headphone.id,
                    "name": headphone.name,
                    "brand": brand.name,
                    "type": type_obj.name,
                    "price": headphone.price
                }
            }
        except Exception as e:
            return {"success": False, "response": f"❌ Lỗi: {str(e)}", "action": "create_headphone"}
    
    def _execute_get_brands(self, db: Session) -> Dict[str, Any]:
        """Thực hiện xem danh sách brands"""
        brands = get_brands(db)
        if not brands:
            return {"success": True, "response": "📝 Chưa có brand nào trong hệ thống", "action": "get_brands"}
        
        response = "📝 **Danh sách brands:**\n"
        for i, brand in enumerate(brands, 1):
            response += f"{i}. {brand.name}\n"
        
        return {
            "success": True,
            "response": response,
            "action": "get_brands",
            "data": [{"id": b.id, "name": b.name, "slug": b.slug} for b in brands]
        }
    
    def _execute_get_types(self, db: Session) -> Dict[str, Any]:
        """Thực hiện xem danh sách types"""
        types = get_types(db)
        if not types:
            return {"success": True, "response": "📝 Chưa có type nào trong hệ thống", "action": "get_types"}
        
        response = "📝 **Danh sách types:**\n"
        for i, type_obj in enumerate(types, 1):
            response += f"{i}. {type_obj.name}\n"
        
        return {
            "success": True,
            "response": response,
            "action": "get_types",
            "data": [{"id": t.id, "name": t.name, "slug": t.slug} for t in types]
        }
    
    def _execute_get_headphones(self, db: Session) -> Dict[str, Any]:
        """Thực hiện xem danh sách headphones"""
        headphones = get_headphones(db)
        if not headphones:
            return {"success": True, "response": "🎧 Chưa có tai nghe nào trong hệ thống", "action": "get_headphones"}
        
        response = "🎧 **Danh sách tai nghe:**\n"
        for i, headphone in enumerate(headphones, 1):
            brand_name = headphone.brand.name if headphone.brand else "Unknown"
            type_name = headphone.type.name if headphone.type else "Unknown"
            response += f"{i}. {headphone.name} - {brand_name} ({type_name}) - {headphone.price:,}đ\n"
        
        return {
            "success": True,
            "response": response,
            "action": "get_headphones"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Kiểm tra tình trạng AI service"""
        if self.llm_type == "ollama":
            return {
                "status": "healthy",
                "message": f"🚀 AI Service sử dụng Ollama ({self.ollama_model})",
                "llm_type": "ollama",
                "ollama_url": self.ollama_url,
                "ollama_model": self.ollama_model,
                "ollama_available": self.ollama_available,
                "fallback_enabled": True,
                "cost": "FREE 🎉"
            }
        else:
            return {
                "status": "rule_based",
                "message": "🤖 AI Service sử dụng Rule-based (Ollama không khả dụng)",
                "llm_type": "rule_based", 
                "ollama_url": self.ollama_url,
                "ollama_model": self.ollama_model,
                "ollama_available": False,
                "fallback_enabled": True,
                "cost": "FREE 🎉",
                "suggestion": "Cài đặt Ollama để có AI thông minh hơn: https://ollama.ai"
            }

# Global instance
ai_service = None

def get_ai_service() -> AIService:
    """Get AI service instance"""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service