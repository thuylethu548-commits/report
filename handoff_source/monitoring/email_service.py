import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config.settings import settings

logger = logging.getLogger("EmailService")


class EmailService:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.user = user or settings.SMTP_USER
        self.password = password or settings.SMTP_PASSWORD
        self.enabled = bool(self.user and self.password and getattr(settings, "ENABLE_EMAIL_ALERTS", True))

    def _send_sync(self, to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
        """Synchronous SMTP worker to be called inside asyncio.to_thread."""
        if not self.enabled:
            logger.info("Email service is disabled or credentials missing. Skipping.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"ASTRA QUANT DESK <{self.user}>"
        msg["To"] = to_email

        # Attach text version if provided
        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
        # Attach HTML version
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=12) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.user, self.password)
                server.send_message(msg)
            logger.info(f"Email sent successfully to {to_email} | Subject: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_email(self, to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
        """Asynchronously dispatches an email via thread pool."""
        return await asyncio.to_thread(self._send_sync, to_email, subject, html_body, text_body)

    async def send_welcome_email(self, to_email: str, full_name: str, username: str) -> bool:
        """Sends a high-tech branded welcome email to a new client."""
        display_name = full_name or username
        subject = f"✦ Chào mừng {display_name} gia nhập Astra Quant Desk"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #0b1120;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #e2e8f0;
        }}
        .container {{
            max-width: 600px;
            margin: 30px auto;
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        }}
        .header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            padding: 36px 30px;
            text-align: center;
            border-bottom: 1px solid #334155;
        }}
        .logo-title {{
            font-size: 26px;
            font-weight: 900;
            letter-spacing: 2px;
            color: #38bdf8;
            margin: 0;
        }}
        .subtitle {{
            font-size: 12px;
            color: #94a3b8;
            letter-spacing: 2.5px;
            font-weight: 700;
            margin-top: 6px;
            text-transform: uppercase;
        }}
        .content {{
            padding: 32px 30px;
            line-height: 1.6;
        }}
        .h2 {{
            font-size: 20px;
            color: #f8fafc;
            margin-top: 0;
            margin-bottom: 16px;
        }}
        .card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 18px 20px;
            margin: 20px 0;
        }}
        .btn {{
            display: inline-block;
            background: linear-gradient(135deg, #0ea5e9 0%, #10b981 100%);
            color: #ffffff !important;
            text-decoration: none;
            font-weight: 700;
            font-size: 14px;
            padding: 14px 28px;
            border-radius: 8px;
            margin-top: 15px;
            box-shadow: 0 4px 14px rgba(14, 165, 233, 0.4);
        }}
        .security-badge {{
            display: flex;
            align-items: center;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            color: #6ee7b7;
            font-size: 12.5px;
            margin-top: 20px;
        }}
        .footer {{
            padding: 20px 30px;
            text-align: center;
            font-size: 12px;
            color: #64748b;
            border-top: 1px solid #1e293b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="logo-title">ASTRA QUANT</h1>
            <div class="subtitle">AUTONOMOUS AI TRADING LABS</div>
        </div>
        <div class="content">
            <h2 class="h2">Xin chào {display_name},</h2>
            <p>Tài khoản của bạn đã được khởi tạo thành công trên hệ thống <b>Astra Quant Desk</b>.</p>
            
            <div class="card">
                <div style="font-size: 13px; color: #94a3b8; margin-bottom: 6px;">THÔNG TIN TÀI KHOẢN:</div>
                <div style="font-size: 15px; font-weight: 600; color: #f8fafc;">• Username: <span style="color: #38bdf8;">{username}</span></div>
                <div style="font-size: 15px; font-weight: 600; color: #f8fafc;">• Email: <span style="color: #38bdf8;">{to_email}</span></div>
                <div style="font-size: 15px; font-weight: 600; color: #f8fafc;">• Chế độ: <span style="color: #10b981;">Non-Custodial Copy Trading</span></div>
            </div>

            <div class="security-badge">
                🛡️ <b>Cam kết bảo mật Non-Custodial:</b> Tài sản của bạn luôn nằm an toàn 100% trong tài khoản Binance cá nhân. Hệ thống chỉ yêu cầu quyền Đọc & Giao dịch Futures, tuyệt đối KHÔNG cấp quyền Rút tiền.
            </div>

            <div style="text-align: center; margin-top: 25px;">
                <a href="https://trader.hoanvi.com/portal/dashboard" class="btn" target="_blank">Truy Cập Cổng Khách Hàng →</a>
            </div>
        </div>
        <div class="footer">
            © 2026 Astra Quant Labs. Mọi quyền được bảo lưu.<br>
            Hệ sinh thái giao dịch định lượng đa tác tử bảo toàn vốn.
        </div>
    </div>
</body>
</html>
"""
        return await self.send_email(to_email, subject, html_body)

    async def send_trade_alert_email(
        self,
        to_email: str,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        pnl: Optional[float] = None
    ) -> bool:
        """Sends an instant trade execution or position closure alert email."""
        action_title = "Khớp Lệnh Mới" if pnl is None else "Chốt Lời / Cắt Lỗ Vị Thế"
        subject = f"⚡ [{symbol}] {action_title} ({side.upper()})"
        
        pnl_html = ""
        if pnl is not None:
            color = "#10b981" if pnl >= 0 else "#f43f5e"
            sign = "+" if pnl > 0 else ""
            pnl_html = f"""
            <div style="font-size: 18px; font-weight: 800; color: {color}; margin-top: 10px;">
                PnL Thực Tế: {sign}{pnl:.4f} USDT
            </div>
            """

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 20px; background-color: #0b1120; font-family: sans-serif; color: #e2e8f0;">
    <div style="max-width: 520px; margin: auto; background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 24px;">
        <h3 style="color: #38bdf8; margin-top: 0;">⚡ ASTRA QUANT COCKPIT ALERT</h3>
        <p style="font-size: 15px; margin-bottom: 15px;">Thông báo cập nhật lệnh giao dịch tự động trên tài khoản của bạn:</p>
        <div style="background: #1e293b; border-radius: 8px; padding: 15px;">
            <div style="margin-bottom: 8px;"><b>Cặp Giao Dịch:</b> <span style="color: #38bdf8;">{symbol}</span></div>
            <div style="margin-bottom: 8px;"><b>Vị Thế:</b> <span style="font-weight: 700;">{side.upper()}</span></div>
            <div style="margin-bottom: 8px;"><b>Mức Giá:</b> ${price:,.2f}</div>
            <div style="margin-bottom: 8px;"><b>Khối Lượng:</b> {quantity}</div>
            {pnl_html}
        </div>
        <div style="margin-top: 20px; font-size: 12px; color: #64748b; text-align: center;">
            Theo dõi chi tiết tại <a href="https://trader.hoanvi.com/portal/dashboard" style="color: #38bdf8;">trader.hoanvi.com</a>
        </div>
    </div>
</body>
</html>
"""
        return await self.send_email(to_email, subject, html_body)


email_service = EmailService()
