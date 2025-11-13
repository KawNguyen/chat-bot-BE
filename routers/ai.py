from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ai_service import get_ai_service
import os

router = APIRouter(prefix="/ai", tags=["AI Chat"])

class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    success: bool
    error: Optional[str] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(chat_message: ChatMessage):
    """
    Giao tiếp với AI để tạo brand, type, headphone thông qua natural language
    
    Hỗ trợ OpenAI GPT với Function Calling để hiểu ngôn ngữ tự nhiên.
    
    Ví dụ:
    - "Tạo brand Apple"
    - "Tạo loại tai nghe bluetooth"
    - "Tạo tai nghe AirPods Pro của Apple loại bluetooth giá 200 đô"
    - "Xem danh sách brands"
    - "Hiển thị tất cả tai nghe"
    - "Tôi muốn thêm một tai nghe gaming của Razer"
    """
    try:
        # Get AI service và xử lý message
        ai_service = get_ai_service()
        result = ai_service.process_message(chat_message.message)
        
        if result.get("success", False):
            return ChatResponse(
                response=result.get("response", ""),
                success=True
            )
        else:
            return ChatResponse(
                response=result.get("response", "Có lỗi xảy ra"),
                success=False,
                error=result.get("error")
            )
        
    except Exception as e:
        return ChatResponse(
            response=f"Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu: {str(e)}",
            success=False,
            error=str(e)
        )

@router.get("/")
async def ai_info():
    """Thông tin về AI capabilities"""
    return {
        "message": "AI Chat Service sử dụng OpenAI GPT cho quản lý cửa hàng tai nghe",
        "model": "gpt-3.5-turbo with Function Calling",
        "capabilities": [
            "Hiểu ngôn ngữ tự nhiên tiếng Việt",
            "Tạo brand mới", 
            "Tạo type tai nghe mới",
            "Tạo headphone mới",
            "Xem danh sách brands",
            "Xem danh sách types", 
            "Xem danh sách headphones",
            "Tự động tạo brand/type nếu chưa có",
            "Hiểu nhiều cách diễn đạt khác nhau"
        ],
        "examples": [
            "Tạo brand Apple",
            "Thêm loại tai nghe bluetooth",
            "Tạo tai nghe AirPods Pro của Apple loại bluetooth giá 200",
            "Tôi muốn thêm brand Sony",
            "Xem tất cả brands",
            "Hiển thị danh sách tai nghe",
            "Tạo một tai nghe gaming của Razer giá 150 đô",
            "Có những brand nào?"
        ],
        "endpoint": "/ai/chat",
        "api_key_required": bool(os.getenv("OPENAI_API_KEY")),
        "intelligent_parsing": True
    }

@router.get("/health")
async def ai_health_check():
    """Kiểm tra trạng thái AI service"""
    try:
        api_key_configured = bool(os.getenv("OPENAI_API_KEY"))
        
        if not api_key_configured:
            return {
                "status": "error",
                "message": "OpenAI API key chưa được cấu hình",
                "api_key_configured": False
            }
        
        # Test AI service
        ai_service = get_ai_service()
        health_result = ai_service.health_check()
        
        return health_result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi AI service: {str(e)}",
            "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))
        }