import sys
import os
from pathlib import Path

# Thêm thư mục src vào sys.path để import được app.graph khi chạy streamlit tại thư mục gốc
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

import json
import streamlit as st
from app.graph import ShoppingAssistant

# Set page config
st.set_page_config(page_title="Shopping Assistant", page_icon="🛒", layout="wide")

st.title("🛒 Shopping Assistant - Agent System")
st.markdown("Trợ lý mua sắm thông minh hỗ trợ giải đáp chính sách, tra cứu khách hàng và đơn hàng tự động dựa trên LangGraph.")

# Khởi tạo backend (chỉ chạy 1 lần)
@st.cache_resource
def get_assistant():
    return ShoppingAssistant()

assistant = get_assistant()

# Đọc file test.json
@st.cache_data
def load_test_questions():
    test_path = project_root / "data" / "test.json"
    if test_path.exists():
        with open(test_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [item["question"] for item in data]
    return []

test_questions = load_test_questions()

# ====================
# SIDEBAR
# ====================
st.sidebar.header("📋 Danh sách câu hỏi Test")
st.sidebar.markdown("Bạn có thể chọn nhanh các câu hỏi từ kịch bản test có sẵn:")

selected_question = st.sidebar.selectbox("Chọn câu hỏi mẫu", ["-- Tự nhập câu hỏi --"] + test_questions)

trigger_send = st.sidebar.button("👉 Gửi câu hỏi được chọn")

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Xóa lịch sử hội thoại"):
    st.session_state.messages = []
    st.rerun()

# ====================
# CHAT INTERFACE
# ====================
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "trace" in msg and msg["trace"]:
            with st.expander("🛠️ Xem chi tiết quá trình suy luận (Trace)"):
                st.json(msg["trace"])

user_input = st.chat_input("Nhập câu hỏi của bạn vào đây...")

# Ưu tiên nếu user bấm nút gửi từ Sidebar
if trigger_send and selected_question != "-- Tự nhập câu hỏi --":
    user_input = selected_question

if user_input:
    # Lưu câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # Gọi AI backend
    with st.chat_message("assistant"):
        with st.spinner("🤖 Agent đang suy nghĩ và tra cứu..."):
            try:
                res = assistant.ask(user_input, rebuild_index=False)
                answer = res.get("final_answer", "Xin lỗi, đã xảy ra lỗi trong quá trình tổng hợp câu trả lời.")
                trace = res.get("trace", [])
                
                st.markdown(answer)
                with st.expander("🛠️ Xem chi tiết quá trình suy luận (Trace)"):
                    st.json(trace)
                    
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "trace": trace
                })
            except Exception as e:
                st.error(f"Đã xảy ra lỗi hệ thống: {str(e)}")
