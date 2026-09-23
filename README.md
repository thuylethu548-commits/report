# ASTRA QUANT DESK — BỘ BÁO CÁO TOÀN DIỆN & BÀN GIAO KIẾN TRÚC
### *(Comprehensive Technical Audit & Architecture Handoff Bundle)*

Kho lưu trữ này chứa toàn bộ các tài liệu báo cáo kỹ thuật, kiểm toán kiến trúc, lược đồ cơ sở dữ liệu, quy trình khớp lệnh và gói mã nguồn bàn giao của hệ thống **ASTRA QUANT DESK & THIÊN CƠ CÁC (Phiên bản 3.0.0)**.

---

## 📑 Danh Mục Báo Cáo Kỹ Thuật (Architecture & Audit Bundle)

| TT | Tài Liệu | Mô Tả Tóm Tắt |
| :---: | :--- | :--- |
| **00** | [00_EXECUTIVE_SUMMARY.md](00_EXECUTIVE_SUMMARY.md) | Tổng quan hệ thống, stack công nghệ, runtime, phân định LIVE vs thực nghiệm. |
| **01** | [01_PROJECT_TREE.md](01_PROJECT_TREE.md) | Cây thư mục dự án 4 cấp chi tiết kèm chú thích 1 dòng cho từng tệp quan trọng. |
| **02** | [02_ARCHITECTURE.md](02_ARCHITECTURE.md) | Bảng phân công chi tiết 23 subsystem (File, Class, Function, Inputs, Outputs, quyền can thiệp lệnh). |
| **03** | [03_AGENT_SYSTEM.md](03_AGENT_SYSTEM.md) | Bóc tách sự thật kỹ thuật của 12 tác tử, xác minh mã nguồn thực tế của Grok 4.7, GPT-6-Astra, Claude, DeepSeek, Groq. |
| **04** | [04_TRADING_PIPELINE.md](04_TRADING_PIPELINE.md) | Truy vết vòng đời lệnh 20 bước và xác minh chi tiết 18 yếu tố rủi ro/khớp lệnh sàn. |
| **05** | [05_DATABASE.md](05_DATABASE.md) | Lược đồ schema 23 bảng SQLite, kiểu dữ liệu, khóa chính, mục đích và xác định Source of Truth. |
| **06** | [06_API_AND_INTEGRATIONS.md](06_API_AND_INTEGRATIONS.md) | Bảng định tuyến mô hình AI (Model Router Table), tích hợp bên ngoài và danh mục 88 REST API nội bộ. |
| **07** | [07_FRONTEND_PAGES.md](07_FRONTEND_PAGES.md) | Đặc tả toàn bộ các trang giao diện của Admin Desk (Port 8386) và Client Portal (Port 3005). |
| **08** | [08_DEPLOYMENT.md](08_DEPLOYMENT.md) | Hạ tầng VPS, quy hoạch cổng, bảng tiến trình PM2, danh mục tên biến môi trường và chính sách sao lưu. |
| **09** | [09_TESTS_AND_HEALTH.md](09_TESTS_AND_HEALTH.md) | Kiểm toán 34 tệp unit test, ma trận độ phủ tính năng và 4 khoảng trống kiểm thử nghiêm trọng. |
| **10** | [10_RISKS_AND_TECH_DEBT.md](10_RISKS_AND_TECH_DEBT.md) | Đánh giá nợ công nghệ thẳng thắn theo 4 cấp độ (Critical, High, Medium, Low). |
| **11** | [11_REAL_VS_MOCK_DATA.md](11_REAL_VS_MOCK_DATA.md) | Ma trận phân định rạch ròi giữa số liệu LIVE/DB, số liệu TÍNH TOÁN và số liệu GIẢ LẬP/PLACEHOLDER. |
| **12** | [12_CURRENT_RUNTIME_STATE.md](12_CURRENT_RUNTIME_STATE.md) | Ảnh chụp trạng thái vận hành thời gian thực (Read-Only) của bot và vị thế đang mở trên Binance. |
| **JSON** | [architecture_manifest.json](architecture_manifest.json) | Tệp kê khai JSON máy đọc được tóm lược toàn diện kiến trúc hệ thống. |
| **TXT** | [source_manifest.txt](source_manifest.txt) | Danh mục 431 tệp nguồn được đóng gói kèm kích thước và mã băm SHA-256. |
| **ZIP** | [ASTRA_PROJECT_HANDOFF.zip](ASTRA_PROJECT_HANDOFF.zip) | Gói nén mã nguồn sạch (~1.82 MB, đã quét và REDACT toàn bộ secret). |

---

## 📊 Báo Cáo Tuần Tra Hằng Ngày (Daily Audit Reports)
* [Báo Cáo Ngày 2026-09-22](daily_reports/daily_report_2026-09-22.md)
* [Báo Cáo Ngày 2026-09-23](daily_reports/daily_report_2026-09-23.md)

---

## 🔒 Cam Kết An Toàn & Bảo Mật
* Mọi khóa API Key, Secret, Token, Password đã được quét và khử (REDACTED) thành `***REDACTED***`.
* Toàn bộ dữ liệu được trích xuất ở chế độ Read-Only, không làm gián đoạn các dịch vụ đang vận hành trên máy chủ.
