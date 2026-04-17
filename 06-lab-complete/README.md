# VinBank AI Agent — Production Deployment Report 🚀

Dự án này đánh dấu việc hoàn thiện một hệ thống AI Agent đạt chuẩn **Production-Ready**, được thiết kế để hoạt động ổn định, bảo mật và tiết kiệm chi phí khi triển khai trên các môi trường Cloud như **Railway**.

---

## 🛠️ Những Thành Phần Đã Triển Khai

Trong dự án này, tui đã xây dựng và tích hợp thành công các thành phần cốt lõi sau:

### 1. Hệ Thống Bảo Vệ Đa Lớp (Defense Pipeline)
Thay vì gọi LLM trực tiếp, mọi yêu cầu đều phải đi qua một Pipeline bảo mật bao gồm:
*   **Input Guardrail:** Tự động phát hiện và ngăn chặn các kỹ thuật **Prompt Injection** (ví dụ: yêu cầu bot quên chỉ dẫn cũ hoặc tiết lộ mã hệ thống).
*   **Output Guardrail (PII Filtering):** Quét câu trả lời của AI để ẩn các thông tin nhạy cảm như Số điện thoại, Email, giúp bảo vệ quyền riêng tư của khách hàng.

### 2. Quản Trị Vận Hành (Ops & Scaling)
Để đưa lên Railway một cách chuyên nghiệp, dự án đã áp dụng các kỹ thuật:
*   **Redis Rate Limiting:** Sử dụng Redis để quản lý lưu lượng truy cập. Ngăn chặn các cuộc tấn công SPAM hoặc DoS làm treo hệ thống.
*   **Token-based Cost Guard:** Cơ chế "cầu chì" thông minh giúp kiểm soát ví tiền OpenAI. Hệ thống tự động ngắt kết nối khi chi phí trong ngày chạm ngưỡng **$1.0**, tránh rủi ro mất tiền ngoài ý muốn.
*   **Structured Logging:** Lưu log dưới dạng JSON chuẩn, giúp dễ dàng theo dõi lỗi và hành vi của người dùng trên Dashboard của Railway.

### 3. Trải Nghiệm Người Dùng (Frontend UI)
Giao diện không chỉ đẹp mà còn mang tính ứng dụng cao:
*   **Real-time Metrics:** Hiển thị độ trễ (Latency), tổng số yêu cầu và chi tiêu thực tế.
*   **Security Audit Log:** Cho phép "soi" chi tiết từng lớp bảo vệ đã xử lý yêu cầu như thế nào, giúp tăng tính minh bạch của hệ thống.

---

## 🌟 Điểm Nổi Bật Của Hệ Thống

*   **Đạt chuẩn Production Ready:** Vượt qua toàn bộ các bài kiểm tra về Dockerfile (Multi-stage), Healthcheck, Liveness/Readiness probe, và Graceful Shutdown.
*   **Tối Ưu Cloud (Railway-Native):** Cấu hình `railway.toml` và Docker được tinh chỉnh để tận dụng tối đa hạ tầng của Railway, cho phép triển khai chỉ trong vài phút.
*   **Tiết Kiệm & An Toàn:** Cơ chế chặn budget cứng ($1/ngày) là điểm nhấn quan trọng giúp nhà phát triển yên tâm khi public chatbot ra môi trường internet.
*   **Xử Lý Tiếng Việt Chuẩn:** Hệ thống streaming và parse JSON được tinh chỉnh để hiển thị font tiếng Việt mượt mà, không lỗi Unicode.

---

## 🚀 Hướng Dẫn Chạy & Cấu Hình

### Chạy Local (Docker)
Sử dụng Docker Compose để chạy cả App và Redis:
```bash
docker compose up --build
```

### Triển Khai Railway
Hệ thống đã sẵn sàng 100%. Các biến cần cấu hình trên Railway:
*   `OPENAI_API_KEY`: Key từ OpenAI.
*   `AGENT_API_KEY`: Chìa khóa bảo mật cho Agent (ví dụ: `your-secret-key-123`).
*   `REDIS_URL`: URL kết nối tới dịch vụ Redis trên Railway.

---
*Dự án hoàn thiện bởi **Nguyễn Đôn Đức** — Một giải pháp AI Agent an toàn và tin cậy cho VinBank.*
