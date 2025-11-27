# Script để cập nhật chatbot.py với chat history
import re

file_path = r"d:\downloads\DOANNGON\chatBot\routers\chatbot.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find the section to replace
old_section = '''    # ===========================
    # 🔥 CASE 2 — NORMAL CHAT / TƯ VẤN
    # ===========================
    db_context = get_db_context(db)
    system_prompt = req.system_prompt or get_prompt_for_intent(intent)

    prompt = (
        f"{system_prompt}\\n"
        f"{db_context}\\n\\n"
        f"Khách hàng: {req.message}\\n\\n"
        f"Trợ lý:"
    )

    ai_reply = await ai.generate(prompt, max_tokens=900, temperature=0.7)

    return ChatResponse(reply=ai_reply)'''

new_section = '''    # ===========================
    # 🔥 CASE 2 — NORMAL CHAT / TƯ VẤN
    # ===========================
    db_context = get_db_context(db)
    system_prompt = req.system_prompt or get_prompt_for_intent(intent)

    # 🔥 THÊM CHAT HISTORY CONTEXT
    chat_history = ""
    if session and session.messages:
        history_messages = session.messages[:-1]  # Bỏ tin nhắn cuối (tin nhắn hiện tại)
        if history_messages:
            chat_history = "\\n\\nLỊCH SỬ HỘI THOẠI:\\n"
            for msg in history_messages[-6:]:  # Lấy 6 tin nhắn gần nhất
                role_label = "Khách hàng" if msg.role == "user" else "Trợ lý"
                chat_history += f"{role_label}: {msg.content}\\n"
            chat_history += "\\n"

    prompt = (
        f"{system_prompt}\\n"
        f"{db_context}\\n"
        f"{chat_history}"
        f"Khách hàng: {req.message}\\n\\n"
        f"Trợ lý:"
    )

    ai_reply = await ai.generate(prompt, max_tokens=900, temperature=0.7)

    # Lưu assistant reply
    add_message(db, session_id, "assistant", ai_reply)

    return ChatResponse(reply=ai_reply, session_id=session_id)'''

content = content.replace(old_section, new_section)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Đã cập nhật chatbot.py với chat history!")
