# BÁO CÁO KẾT QUẢ THỰC HÀNH LAB 14 - AI EVALUATION & BENCHMARKING
**Họ và tên:** Lê Bá Chiến
**ID:** 2A202600755

---

## 1. Điểm Nhóm (Hệ thống Evaluation)

### 1.1 Retrieval Evaluation & Dataset
- **Quy mô Dataset:** Khởi tạo thành công bộ Golden Dataset với tổng cộng **57 test cases**, sinh tự động (SDG) từ chính sách cửa hàng và dữ liệu RAG context.
- **Chỉ số Retrieval (Truy xuất):**
  - **Hit Rate:** Đạt **75.44%**.
  - **MRR (Mean Reciprocal Rank):** Đã tích hợp logic tính toán vị trí văn bản.
- **Mối liên hệ giữa Retrieval Quality & Answer Quality:**
  Chất lượng của câu trả lời phụ thuộc rất lớn vào Retrieval. Khi Hit Rate cao, Context đưa vào LLM càng chính xác, từ đó giảm rủi ro Hallucination (ảo giác) và tăng tính xác thực (Accuracy). Nếu Retrieval thất bại (Hit Rate = 0), Model sẽ bị ép phải trả lời "bịa" hoặc từ chối trả lời (Fail to answer).

### 1.2 Multi-Judge Consensus
- **Mô hình sử dụng:** Hệ thống được tích hợp 2 LLMs để đánh giá chéo:
  - **Primary Judge:** `qwen3-max` (Custom Provider)
  - **Secondary Judge:** `gemini-3.1-flash-lite` (Google API)
- **Độ đồng thuận (Agreement Rate):** Đạt **93.0%**, chứng tỏ 2 models giám khảo có chung góc nhìn và tiêu chuẩn chấm điểm.

### 1.3 Regression Testing & Performance
- **Tốc độ xử lý (Async):** Áp dụng thư viện `asyncio`, chạy song song 57 test cases và gọi cùng lúc 2 model, hoàn thành toàn bộ Pipeline cực nhanh, tối ưu tài nguyên mạng và thời gian chờ.
- **Regression Result:**
  - **V1 (Baseline):** Score 3.00
  - **V2 (Agent Optimized):** Score 4.14
  - **Delta:** +1.14 điểm
  - **Release Gate:** Logic của hệ thống đã tự động **APPROVE** (Chấp nhận cập nhật) do phiên bản V2 tốt hơn hẳn phiên bản cũ.

### 1.4 Failure Analysis (Phân tích lỗi)
Báo cáo `failure_analysis.md` ghi nhận các trường hợp Fail. Dựa trên bộ quy tắc "5 Whys", nguyên nhân cốt lõi bao gồm:
1. Thông tin trong hệ thống chưa đủ bao quát hoặc đoạn Chunk bị cắt ngang ngữ nghĩa, dẫn đến thuật toán nhúng (Embedding) không bắt được Context phù hợp.
2. Với các câu hỏi nhiễu hoặc Red Teaming, RAG trả về rỗng nhưng LLM lại quá cố gắng trả lời dẫn đến điểm đánh giá thấp từ Judge.

---

## 2. Điểm Cá nhân (Technical & Problem Solving)

### 2.1 Problem Solving (Giải quyết sự cố)
Trong quá trình phát triển hệ thống phức tạp, tôi đã trực tiếp xử lý các bài toán hệ thống:
1. **Lỗi Async Event Loop của Streamlit:** Khắc phục sự cố `RuntimeError: Event loop is closed` làm sập nền tảng Streamlit. Chuyển đổi thành công sang `asyncio.run()` để quản lý vòng đời Async độc lập mà không ảnh hưởng luồng chính của UI.
2. **Lỗi Multi-Judge (Async Queue & API Not Found):**
   - Thay vì dùng `run_in_executor` dễ gây kẹt luồng, đã tối ưu lại thành hàm bất đồng bộ gốc của LangChain là `.ainvoke()` giúp hệ thống đa luồng mượt mà.
   - Sửa lỗi xung đột cấu hình Provider khi Gemini bị ép nhận model `qwen`, chủ động thiết lập model thứ cấp nhẹ là `gemini-3.1-flash-lite`.
   - Bổ sung chức năng Parse kết quả trả về của LLM dạng cấu trúc List of Block giúp regex không bị sụp.

### 2.2 Technical Depth
- **MRR (Mean Reciprocal Rank):** Là chỉ số đánh giá thứ hạng của kết quả đúng đầu tiên mà hệ thống truy xuất được. MRR càng cao chứng tỏ đoạn văn bản đúng xuất hiện ngay ở Top 1, giúp tiết kiệm chi phí Token khi đưa vào Prompt LLM.
- **Cohen's Kappa:** Chỉ số thống kê đo lường sự đồng thuận giữa 2 giám khảo (loại trừ trường hợp trùng hợp ngẫu nhiên). Ở đây hệ thống áp dụng Agreement Rate (93%) tương đương với mức độ nhất quán rất cao giữa Qwen và Gemini.
- **Position Bias:** Hiện tượng các LLM thường có xu hướng chỉ để ý tới những đoạn văn bản nằm ở phần đầu (hoặc cuối) của Prompt và bỏ qua phần giữa (Lost in the middle). Vì thế MRR cao mới giúp giảm thiểu Position Bias.
- **Trade-off giữa Chi phí và Chất lượng:** 
  Dùng model kích thước lớn (như GPT-4o hay Qwen-Max) làm Judge sẽ đánh giá rất chuẩn xác nhưng chi phí API cao và tốn thời gian. Việc dùng 1 model lớn (Primary) kết hợp 1 model nhỏ, tốc độ cao (Secondary - Gemini Flash) là một chiến lược cân bằng hoàn hảo giữa hiệu năng, độ chính xác và chi phí.

---
**Tài liệu đính kèm khi nộp:**
- Link Github Repository dự án
- Thư mục báo cáo: `reports/summary.json` và `reports/benchmark_results.json`
- Phân tích lỗi: `analysis/failure_analysis.md`

**Kết quả kiểm tra (Terminal Output):**
```text
🔍 Đang kiểm tra định dạng bài nộp...
✅ Tìm thấy: reports/summary.json
✅ Tìm thấy: reports/benchmark_results.json
✅ Tìm thấy: analysis/failure_analysis.md

--- Thống kê nhanh ---
Tổng số cases: 57
Điểm trung bình: 4.14
✅ Đã tìm thấy Retrieval Metrics (Hit Rate: 75.4%)
✅ Đã tìm thấy Multi-Judge Metrics (Agreement Rate: 93.0%)
✅ Đã tìm thấy thông tin phiên bản Agent (Regression Mode)

🚀 Bài lab đã sẵn sàng để chấm điểm!
```