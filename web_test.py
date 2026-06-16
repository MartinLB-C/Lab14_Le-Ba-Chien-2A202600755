import sys
import os
import json
import asyncio
import pandas as pd
from pathlib import Path
import streamlit as st

# Configure page
st.set_page_config(page_title="Evaluation Factory & Shopping Assistant", page_icon="🏭", layout="wide")

# Custom CSS for Premium Design
st.markdown("""
<style>
    .reportview-container {
        background: #0E1117;
    }
    .metric-card {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        text-align: center;
        border-top: 4px solid #4a90e2;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #e2e8f0;
    }
    .metric-label {
        font-size: 14px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button {
        background-color: #4a90e2;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #357abd;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.4);
    }
    .failure-card {
        background-color: #2d1b1e;
        border-left: 4px solid #e74c3c;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏭 Evaluation Factory & Agent Benchmark Dashboard")
st.markdown("Hệ thống đánh giá tự động đa mô hình (Multi-Judge) và Trợ lý RAG Day 09.")

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 RAG Playground", "🧪 SDG Data Generation", "📊 Benchmark & Analytics"])

# ----------------- TAB 1: RAG Playground -----------------
with tab1:
    st.header("Trợ lý mua sắm trực tuyến (Interactive Test)")
    
    @st.cache_resource
    def get_shopping_assistant():
        day09_dir = Path(__file__).resolve().parent / "Day09_Le-Ba-Chien-2A202600755"
        src_dir = day09_dir / "src"
        if str(src_dir) not in sys.path:
            sys.path.append(str(src_dir))
        from app.graph import ShoppingAssistant
        return ShoppingAssistant()

    try:
        assistant = get_shopping_assistant()
    except Exception as e:
        st.error(f"Lỗi khởi tạo Assistant: {e}")
        assistant = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "trace" in msg and msg["trace"]:
                with st.expander("🛠️ Chi tiết Trace & Routing"):
                    st.json(msg["trace"])

    if assistant:
        user_input = st.chat_input("Nhập câu hỏi test RAG (VD: Đơn hàng 1971 bao giờ giao?)")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            
            with st.chat_message("assistant"):
                with st.spinner("🤖 Agent đang xử lý..."):
                    try:
                        res = assistant.ask(user_input, rebuild_index=False)
                        answer = res.get("final_answer", "Không có câu trả lời.")
                        trace = res.get("trace", [])
                        
                        st.markdown(answer)
                        with st.expander("🛠️ Chi tiết Trace & Routing"):
                            st.json(trace)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "trace": trace
                        })
                    except Exception as e:
                        st.error(f"Lỗi hệ thống: {e}")

# ----------------- TAB 2: SDG Generation -----------------
with tab2:
    st.header("Synthetic Data Generation (SDG)")
    st.markdown("Tự động sinh bộ dữ liệu đánh giá 50+ cases từ tài liệu chính sách (`policy_mock_vi.md`).")
    
    if st.button("🚀 Sinh dữ liệu Golden Set"):
        with st.spinner("Đang sinh dữ liệu từ RAG context... Việc này có thể mất vài phút."):
            import data.synthetic_gen as sgen
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(sgen.main())
                st.success("✅ Đã sinh thành công dữ liệu và lưu vào `data/golden_set.jsonl`")
            except Exception as e:
                st.error(f"Lỗi: {e}")
                
    if os.path.exists("data/golden_set.jsonl"):
        st.subheader("Dữ liệu hiện tại")
        with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        st.info(f"Có tổng cộng {len(lines)} test cases trong bộ Golden Set.")
        
        if len(lines) > 0:
            df_preview = pd.DataFrame([json.loads(l) for l in lines[:10]])
            st.dataframe(df_preview, use_container_width=True)

# ----------------- TAB 3: Benchmark & Analytics -----------------
with tab3:
    st.header("🚀 Benchmark Runner & Failure Analysis")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("▶️ Run Evaluation"):
            with st.spinner("Đang chạy Benchmark Factory..."):
                import main as bench_main
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(bench_main.main())
                    st.success("✅ Đánh giá hoàn tất!")
                except Exception as e:
                    st.error(f"Lỗi Benchmark: {e}")
    
    st.markdown("---")
    
    if os.path.exists("reports/summary.json"):
        with open("reports/summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
            metrics = summary.get("metrics", {})
        
        st.subheader("📊 Metrics Overview")
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{metrics.get("avg_score", 0):.2f}/5.0</div><div class="metric-label">Judge Score</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{metrics.get("hit_rate", 0)*100:.1f}%</div><div class="metric-label">Hit Rate</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{metrics.get("mrr", 0):.2f}</div><div class="metric-label">MRR</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{metrics.get("agreement_rate", 0)*100:.1f}%</div><div class="metric-label">Judge Agreement</div></div>', unsafe_allow_html=True)
            
        st.markdown("---")
        st.subheader("🕵️ Failure Clustering & Analysis")
        
        if os.path.exists("reports/benchmark_results.json"):
            with open("reports/benchmark_results.json", "r", encoding="utf-8") as f:
                results = json.load(f)
                
            failures = [r for r in results if r.get("status") == "fail"]
            st.warning(f"Có {len(failures)} test cases bị đánh giá thất bại (Score < 3.0)")
            
            for fcase in failures:
                st.markdown(f"""
                <div class="failure-card">
                    <h4>Câu hỏi: {fcase.get("test_case")}</h4>
                    <p><b>Agent Answer:</b> {fcase.get("agent_response")}</p>
                    <p><b>Judge Score:</b> {fcase.get("judge", {}).get("final_score")}</p>
                    <p><b>Individual Scores:</b> {fcase.get("judge", {}).get("individual_scores")}</p>
                    <p><b>Latency:</b> {fcase.get("latency", 0):.2f}s</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Chưa có báo cáo đánh giá. Hãy nhấp 'Run Evaluation'.")
