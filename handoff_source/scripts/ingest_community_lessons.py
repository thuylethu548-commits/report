import sqlite3
from datetime import datetime, timezone
import json

def ingest_community_audit_lessons():
    conn = sqlite3.connect('trading_bot.db')
    c = conn.cursor()

    # 1. Lesson 1: Lộ trình 3 giai đoạn & Dòng tiền độc lập
    c.execute("""
        INSERT INTO trading_lessons (timestamp, category, title, details, capital_impact, lesson_learned, operator)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        "SURVIVAL_CASHFLOW_FRAMEWORK",
        "Lộ Trình 3 Giai Đoạn & Nguyên Tắc Dòng Tiền Độc Lập (Survival Cash Flow)",
        "Dữ liệu thực chứng từ cộng đồng trader kỳ cựu: Sai lầm chí mạng của 95% người mới là ảo tưởng bỏ việc văn phòng để trade full-time khi chưa có dòng tiền ổn định. Khi không có nguồn thu ngoài nuôi sống bản thân, áp lực cơm áo gạo tiền làm méo mó tâm lý chịu rủi ro (Risk Distortion), dẫn đến ép lệnh (forced trades) và cháy tài khoản.",
        0.0,
        "Nguyên tắc Sống Sót 3 Giai Đoạn: (1) GĐ Sống Sót: Giữ chắc nguồn thu nhập chính ổn định từ bên ngoài, chỉ trích 10-20% tiền nhàn rỗi để giao dịch; (2) GĐ Rèn Luyện: Khống chế rủi ro mỗi lệnh tối đa 1%, ghi chép nhật ký lệnh nghiêm ngặt để tích lũy dữ liệu; (3) GĐ Định Lượng Hóa: Chuyển toàn bộ quy tắc sang Code & Bot tự động để loại bỏ 100% cảm xúc.",
        "Auditor-Council"
    ))

    # 2. Lesson 2: Lợi thế thống kê Quant (Trading Edge) vs Ảo tưởng Guru
    c.execute("""
        INSERT INTO trading_lessons (timestamp, category, title, details, capital_impact, lesson_learned, operator)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        "QUANT_STATISTICAL_EDGE",
        "Lợi Thế Thống Kê (Trading Edge): Loại Bỏ Ảo Tưởng Guru, Tôn Trọng Dữ Liệu & Backtest",
        "Đúc kết từ chuyên gia Quant (Andrew): Thị trường có bao nhiêu con người thì có bấy nhiêu cái nhìn đỉnh/đáy khác nhau nếu trade bằng mắt thường. Tất cả các mô hình nến hay chỉ báo đều vô nghĩa nếu không có lợi thế thống kê (Statistical Edge) đã được kiểm chứng qua code backtest trên hàng chục nghìn nến.",
        0.0,
        "Không bao giờ tin vào 'chén thánh' hay linh cảm cá nhân. Mọi quyết định giải ngân của Astra Desk phải dựa trên xác suất toán học, kiểm soát Drawdown < 1%, ghi nhật ký chi tiết và dùng bộ lọc thống kê để tinh chỉnh hệ thống liên tục.",
        "Auditor-Council"
    ))

    # 3. Lesson 3: Kỷ luật giải ngân & Tư duy xác suất kinh doanh
    c.execute("""
        INSERT INTO trading_lessons (timestamp, category, title, details, capital_impact, lesson_learned, operator)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        "DISCIPLINED_EXECUTION_MAXIMS",
        "Tư Duy Kinh Doanh Xác Suất: Dám Cắt Dám Chốt, Tuyệt Đối Không Gồng Lỗ",
        "Phân tích tâm lý từ 658 bình luận: Người trade thua lỗ vì xem trading như canh bạc đỏ đen, gồng lệnh âm chờ về bờ và nâng vol khi cay cú. Trader thành công xem trading như hoạt động kinh doanh xác suất, nơi Stop-Loss là chi phí vận hành bắt buộc.",
        0.0,
        "Kỷ luật thép cho tác tử AI: (1) Tuyệt đối không gồng lệnh khi xu hướng đã gãy, chạm SL là đóng ngay; (2) Giới hạn tối đa 2-3 lệnh/ngày để tránh overtrading; (3) Tỷ lệ Risk/Reward tối thiểu 1:2 đến 1:3; (4) Không bao giờ đặt mục tiêu cố định ngày/tháng mà phải tôn trọng chu kỳ thị trường.",
        "Auditor-Council"
    ))

    # Also insert into research_memory for Research Lab
    c.execute("""
        INSERT INTO research_memory (category, title, insight, evidence_json, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "meta_strategy_anchor",
        "Community Real-world Mindset Ingestion (Batch TikTok 658 Comments)",
        "Audit dữ liệu thực chứng từ cộng đồng trader Việt Nam: Xác nhận tính ưu việt tuyệt đối của mô hình Quant & Multi-Agent AI so với Manual Trading. Củng cố 3 rào chắn: Dòng tiền độc lập, Tôn trọng thống kê Backtest, và Kỷ luật ngắt lỗ tự động.",
        json.dumps({
            "source": "TikTok @hoai.xim viral community audit",
            "sample_size": 658,
            "top_consensus": ["Stop-loss is non-negotiable", "Quant backtest beats manual guru", "Zero forced trades"],
            "impact_on_ai_council": "Injected into hard_earned_lessons_to_respect for Grok 4.7 & GPT-6 Astra"
        }),
        datetime.now(timezone.utc).isoformat()
    ))

    conn.commit()
    count = c.execute("SELECT COUNT(*) FROM trading_lessons").fetchone()[0]
    print(f"Ingested successfully! Total trading lessons now: {count}")
    conn.close()

if __name__ == '__main__':
    ingest_community_audit_lessons()
