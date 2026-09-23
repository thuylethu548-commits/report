#!/usr/bin/env python3
"""
ASTRA QUANT — GOOGLE DRIVE 5TB & GOOGLE SHEETS LIVE SYNC ENGINE
--------------------------------------------------------------
Maintains real-time CSV spreadsheets in G:/My Drive/Astra_Quant_Sheets/
Formatted with UTF-8 BOM so Google Drive, Google Sheets, and Excel
display Vietnamese accents, numbers, and currency symbols flawlessly.
"""

import os
import csv
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger("GDriveSheetsSync")

# Detect mounted Google Drive (G:/My Drive)
PRIMARY_GDRIVE_DIR = Path("G:/My Drive/Astra_Quant_Sheets")
FALLBACK_LOCAL_DIR = Path("data/gdrive_sheets")


def get_sheets_dir() -> Path:
    """Returns the primary GDrive directory if mounted, else fallback local directory."""
    try:
        if Path("G:/My Drive").exists():
            PRIMARY_GDRIVE_DIR.mkdir(parents=True, exist_ok=True)
            return PRIMARY_GDRIVE_DIR
    except Exception as e:
        logger.warning(f"Could not access G:/My Drive: {e}")
    
    FALLBACK_LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    return FALLBACK_LOCAL_DIR


def ensure_csv_header(file_path: Path, header_columns: list):
    """Ensures file exists with UTF-8 BOM and header row for Google Sheets compatibility."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header_columns)


def sync_council_debate_to_sheets(debate: Dict[str, Any]) -> str:
    """
    Appends an AI Council debate session (Boss query + 3-Round Debate + Newbie Advice)
    into Astra_AI_Council_Debates.csv in Google Drive.
    """
    sheets_dir = get_sheets_dir()
    file_path = sheets_dir / "Astra_AI_Council_Debates.csv"
    
    headers = [
        "Thời Gian (UTC)",
        "Thời Gian (VN)",
        "Câu Hỏi Của Boss / Thượng Đế",
        "Cặp Tài Sản",
        "Giá Hiện Tại (USDT)",
        "Phe Bò (Momentum)",
        "Phe Gấu (SuperGrok 4.7)",
        "Trọng Tài Tối Cao (GPT-6 Astra & Claude)",
        "Phán Quyết",
        "Khuyến Nghị Newbie",
        "Có Nên Tăng Volume?",
        "Điểm Rủi Ro (1-5)",
        "Độ Tự Tin (%)",
        "Vùng Vào (Entry)",
        "Cắt Lỗ (SL)",
        "Chốt Lời (TP)",
        "Lời Dặn Quản Trị Rủi Ro"
    ]
    ensure_csv_header(file_path, headers)

    now_utc = datetime.now(timezone.utc)
    now_vn_str = now_utc.strftime("%d/%m/%Y %H:%M:%S")
    now_utc_str = now_utc.isoformat()

    row = [
        now_utc_str,
        now_vn_str,
        debate.get("query", "Tư vấn thị trường"),
        debate.get("symbol", "BTC/USDT"),
        str(debate.get("current_price", "")),
        debate.get("bull_thesis", ""),
        debate.get("bear_critique", ""),
        debate.get("arbiter_ruling", ""),
        debate.get("verdict", "HOLD"),
        debate.get("newbie_advice", ""),
        "CÓ THỂ TĂNG VOLUME" if debate.get("can_increase_volume") else "KHÔNG NÊN TĂNG VOL (RỦI RO)",
        str(debate.get("risk_score", 3)),
        f"{float(debate.get('confidence', 0.8))*100:.0f}%",
        str(debate.get("suggested_entry", "")),
        str(debate.get("stop_loss", "")),
        str(debate.get("take_profit", "")),
        debate.get("risk_warning", "")
    ]

    try:
        with open(file_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        logger.info(f"✅ Synced AI Council debate to Google Drive Sheet: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.warning(f"⚠️ Failed to sync debate to Google Sheets: {e}")
        return ""


def sync_trade_to_sheets(trade: Dict[str, Any]) -> str:
    """
    Appends a closed trade to Astra_Live_Trades_Ledger.csv in Google Drive.
    """
    sheets_dir = get_sheets_dir()
    file_path = sheets_dir / "Astra_Live_Trades_Ledger.csv"

    headers = [
        "Thời Gian Đóng",
        "Mã Lệnh",
        "Cặp Giao Dịch",
        "Vị Thế (BUY/SELL)",
        "Chế Độ (LIVE/PAPER)",
        "Giá Vào",
        "Giá Ra",
        "Số Lượng",
        "Lợi Nhuận (USDT)",
        "Phần Trăm PnL (%)",
        "Chiến Lược",
        "Đòn Bẩy",
        "Lý Do Thoát Lệnh"
    ]
    ensure_csv_header(file_path, headers)

    row = [
        trade.get("closed_at") or trade.get("exit_time") or datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S"),
        str(trade.get("order_id", trade.get("id", ""))),
        trade.get("symbol", "BTC/USDT"),
        trade.get("side", "BUY"),
        trade.get("mode", "LIVE"),
        str(trade.get("entry_price", "")),
        str(trade.get("exit_price", "")),
        str(trade.get("quantity", trade.get("amount", ""))),
        f"{float(trade.get('pnl_usdt', 0.0)):.2f}",
        f"{float(trade.get('pnl_percent', 0.0)):.2f}%",
        trade.get("strategy_name", trade.get("strategy", "EMA_Trend")),
        str(trade.get("leverage", 10)),
        trade.get("exit_reason", "TP/SL Dynamic")
    ]

    try:
        with open(file_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        logger.info(f"✅ Synced trade record to Google Drive Sheet: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.warning(f"⚠️ Failed to sync trade to Google Sheets: {e}")
        return ""


def sync_market_directive_to_sheets(directive: Dict[str, Any]) -> str:
    """
    Appends a daily strategic macro directive to Astra_Market_Directives_Daily.csv.
    """
    sheets_dir = get_sheets_dir()
    file_path = sheets_dir / "Astra_Market_Directives_Daily.csv"

    headers = [
        "Thời Gian",
        "Nhịp Vĩ Mô",
        "Chỉ Huy Tình Báo",
        "Chỉ Thị Đội 1 (Astra)",
        "Khuyến Nghị Két Vốn 450U",
        "Lời Khuyên Quản Trị Vốn",
        "Mệnh Lệnh Tác Chiến",
        "Kế Hoạch Dự Trữ An Toàn"
    ]
    ensure_csv_header(file_path, headers)

    now_vn_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S")
    row = [
        now_vn_str,
        directive.get("regime", "MACRO_ACCUMULATION"),
        directive.get("officer", "SuperGrok 4.7 (9Router)"),
        directive.get("venue_mandate", "FUTURES_ACTIVE"),
        directive.get("boss_capital_verdict", "HOLD_450U_VAULT"),
        directive.get("capital_advice_vi", ""),
        directive.get("summary_vi", ""),
        directive.get("reserve_status", "Két 450U ngoài sàn an toàn 100%")
    ]

    try:
        with open(file_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        logger.info(f"✅ Synced macro directive to Google Drive Sheet: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.warning(f"⚠️ Failed to sync directive to Google Sheets: {e}")
        return ""


def sync_client_ledger_to_sheets(clients: list) -> str:
    """
    Overwrites/Refreshes the client copy-trade and commission summary in Astra_Client_CopyTrade_Ledger.csv.
    """
    sheets_dir = get_sheets_dir()
    file_path = sheets_dir / "Astra_Client_CopyTrade_Ledger.csv"

    headers = [
        "User ID",
        "Họ Tên Khách Hàng",
        "Username",
        "Email",
        "IP Đăng Ký",
        "IP Đăng Nhập Cuối",
        "Cảnh Báo Đổi IP",
        "Mức Độ Rủi Ro",
        "Vốn Ký Quỹ AUM (USDT)",
        "Đòn Bẩy",
        "Tổng Lợi Nhuận Khách (USDT)",
        "Hoa Hồng Sếp Nhận (25%)",
        "Số Lệnh Khớp",
        "Ghi Chú Phân Loại"
    ]

    try:
        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for c in clients:
                ip_changed = "CÓ (Đổi dải mạng)" if c.get("registration_ip") != c.get("last_login_ip") else "KHÔNG (Trùng khớp)"
                writer.writerow([
                    f"#{c.get('user_id', 0):02d}",
                    c.get("full_name", ""),
                    "@" + c.get("username", ""),
                    c.get("email", ""),
                    c.get("registration_ip", ""),
                    c.get("last_login_ip", ""),
                    ip_changed,
                    c.get("risk_flag", "NORMAL"),
                    f"{float(c.get('max_margin_usdt', 0.0)):,.2f}",
                    f"{c.get('leverage', 5)}x",
                    f"{float(c.get('client_pnl', 0.0)):,.2f}",
                    f"{float(c.get('desk_commission', 0.0)):,.2f}",
                    c.get("total_trades", 0),
                    c.get("notes", "")
                ])
        logger.info(f"✅ Synced all clients ledger to Google Drive Sheet: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.warning(f"⚠️ Failed to sync client ledger to Google Sheets: {e}")
        return ""


if __name__ == "__main__":
    # Test initialization
    s_dir = get_sheets_dir()
    print(f"Google Drive Sheets Directory: {s_dir}")
    sync_council_debate_to_sheets({
        "query": "BTC đang ở $82,400 có nên vào thêm volume không?",
        "symbol": "BTC/USDT",
        "current_price": 82450.0,
        "bull_thesis": "Đà tăng EMA50/200 khung 1h vững, RSI 58 còn nhiều dư địa.",
        "bear_critique": "Kháng cự $83,000 có tường bán lớn, rủi ro quét râu thanh lý trước phiên Mỹ.",
        "arbiter_ruling": "Xu hướng tăng chủ đạo nhưng điểm vào quá sát cản. Khuyên vào 10% thăm dò.",
        "verdict": "VÀO_THĂM_DÒ_NHẸ",
        "newbie_advice": "Boss là newbie không nên all-in hay tăng volume lớn ngay cản. Chỉ nên test 10-15 USDT, đặt SL $81,200.",
        "can_increase_volume": False,
        "risk_score": 3,
        "confidence": 0.85,
        "suggested_entry": 82100.0,
        "stop_loss": 81200.0,
        "take_profit": 84500.0,
        "risk_warning": "Tuyệt đối không tăng volume đòn bẩy > 10x lúc này!"
    })
    print("✅ Initialized Google Drive Sheets successfully.")
