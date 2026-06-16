# Báo cáo Phân tích Thất bại (Failure Analysis Report)

- **Tổng số cases:** 57
- **Tỉ lệ Fail:** 13/57
- **Điểm LLM-Judge trung bình:** 4.14 / 5.0
- **Hit Rate trung bình:** 0.75

## 2. Phân nhóm lỗi (Failure Clustering)
- **Case:** Tài liệu này được tạo ra nhằm mục đích gì?
  - **Score:** 2.5
  - **Individual:** {'judge_primary': 3, 'judge_secondary': 2}

- **Case:** Loại câu hỏi nào sau đây KHÔNG được đề cập trong ví dụ của tài liệu?
  - **Score:** 1.0
  - **Individual:** {'judge_primary': 1, 'judge_secondary': 1}

- **Case:** Nếu một đơn hàng có mã rõ ràng và thông tin nhận hàng đầy đủ nhưng bị nghi ngờ gian lận, nó có còn là đơn hàng hợp lệ không?
  - **Score:** 1.5
  - **Individual:** {'judge_primary': 2, 'judge_secondary': 1}

- **Case:** Nếu một khách hàng nhận được sản phẩm đúng mô tả, không hư hỏng và đúng thương hiệu, nhưng vẫn yêu cầu hoàn tiền vì không thích màu sắc, điều này có được chấp nhận không?
  - **Score:** 2.0
  - **Individual:** {'judge_primary': 2, 'judge_secondary': 2}

- **Case:** Nếu một khách hàng ở Hà Nội đặt mua một chiếc đàn piano lớn, họ có thể chọn phương thức giao hàng 'express' không? Vì sao?
  - **Score:** 2.0
  - **Individual:** {'judge_primary': 2, 'judge_secondary': 2}

- **Case:** Thời gian giao hàng dự kiến cho đơn hàng nội thành cùng tỉnh/thành phố lớn là bao lâu?
  - **Score:** 1.5
  - **Individual:** {'judge_primary': 2, 'judge_secondary': 1}

- **Case:** Điều kiện nào sau đây KHÔNG cần thiết để đơn hàng đủ điều kiện giao nhanh?
  - **Score:** 1.5
  - **Individual:** {'judge_primary': 2, 'judge_secondary': 1}

- **Case:** Nếu một sản phẩm có trường `return_window_days` được thiết lập là 10, thì thời hạn đổi trả của sản phẩm đó sẽ được tính như thế nào?
  - **Score:** 1.0
  - **Individual:** {'judge_primary': 1, 'judge_secondary': 1}

- **Case:** Một khách hàng mua thực phẩm vào thứ Hai và nhận được xác nhận giao hàng thành công vào sáng thứ Ba. Đến sáng thứ Sáu cùng tuần, họ yêu cầu hoàn tiền. Yêu cầu này có hợp lệ không theo chính sách đổi trả?
  - **Score:** 1.0
  - **Individual:** {'judge_primary': 1, 'judge_secondary': 1}

- **Case:** Một khách hàng mua điện thoại nhưng sau 10 ngày mới phát hiện máy không có tính năng chống nước như mô tả trên trang bán. Tuy nhiên, ngành hàng điện tử chỉ cho phép đổi trả trong vòng 7 ngày nếu 'đổi ý'. Hỏi: khách có thể yêu cầu đổi trả không?
  - **Score:** 1.5
  - **Individual:** {'judge_primary': 2, 'judge_secondary': 1}

- **Case:** Theo chính sách đổi trả, sản phẩm nào sau đây KHÔNG được hỗ trợ trả hàng?
  - **Score:** 1.5
  - **Individual:** {'judge_primary': 2, 'judge_secondary': 1}

- **Case:** Một khách hàng mua phần mềm diệt virus dưới dạng mã kích hoạt điện tử và yêu cầu hoàn tiền sau khi đã nhập mã. Liệu yêu cầu này có được chấp nhận theo chính sách không hỗ trợ trả hàng không? Vì sao?
  - **Score:** 1.0
  - **Individual:** {'judge_primary': 1, 'judge_secondary': 1}

- **Case:** Giả sử một khách hàng gửi trả lại máy xay sinh tố bị vỡ cối do tự ý tháo rời và lắp sai cách, nhưng kèm đầy đủ phụ kiện và hóa đơn. Theo tài liệu, cửa hàng có bắt buộc phải từ chối hoàn tiền không?
  - **Score:** 1.5
  - **Individual:** {'judge_primary': 2, 'judge_secondary': 1}

