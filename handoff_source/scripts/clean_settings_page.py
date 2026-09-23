with open('c:/sunMy/trading_bot/web/templates/admin/settings.html.bak_dual_pages', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract from '<div id="panel-trading-setup"' up to '<!-- ====================================================================\n         PANEL B: TRUNG TÂM ĐIỀU PHỐI AI'
import re
match = re.search(r'(<div class="card" style="box-shadow: 0 4px 20px rgba\(0,0,0,0\.04\).*?)(?=\s*<!--\s*={5,}\s*PANEL B:)', content, re.DOTALL)

if match:
    form_html = match.group(1).strip()
    
    clean_settings = f"""{{% extends "layouts/admin_base.html" %}}

{{% block extra_css %}}
<link rel="stylesheet" href="/static/css/orchestration.css">
{{% endblock %}}

{{% block content %}}
<div class="orch-container">
    
    <!-- HEADER AREA -->
    <div class="orch-header" id="page-main-header">
        <div class="orch-title-wrap">
            <div class="orch-icon-badge" style="background: rgba(16, 185, 129, 0.12); color: #10b981;">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="1" x2="7" y1="14" y2="14"/><line x1="9" x2="15" y1="8" y2="8"/><line x1="17" x2="23" y1="16" y2="16"/>
                </svg>
            </div>
            <div>
                <h1 class="orch-title">Cài Đặt Giao Dịch Binance &amp; Quản Trị Rủi Ro</h1>
                <p class="orch-subtitle">
                    Tùy chỉnh tham số giao dịch Binance Futures / Spot, đòn bẩy, SL/TP ATR, khống chế Drawdown và kết nối Telegram.
                </p>
            </div>
        </div>
        <div class="orch-header-actions">
            <a href="/admin/ai-orchestration" class="orch-ai-btn" style="text-decoration: none;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
                <div class="orch-ai-btn-text">
                    <span class="orch-ai-btn-title">Điều Phối 7 Nguồn AI ↗</span>
                    <span class="orch-ai-btn-sub">Vyce, Groq, Gemini, Cloudflare, 9Router...</span>
                </div>
            </a>
            <a href="/admin/performance" class="orch-doc-btn" style="text-decoration: none; color: #0284c7; border-color: rgba(2, 132, 199, 0.4);">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
                <span>Hiệu Suất AI ↗</span>
            </a>
        </div>
    </div>

    <!-- BANNER CHUYỂN HƯỚNG NHANH SANG TRUNG TÂM ĐIỀU PHỐI AI & HIỆU SUẤT -->
    <div style="background: linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(168, 85, 247, 0.08) 100%); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 12px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="width: 44px; height: 44px; border-radius: 10px; background: rgba(168, 85, 247, 0.15); display: flex; align-items: center; justify-content: center; color: #a855f7; flex-shrink: 0;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>
                </svg>
            </div>
            <div>
                <div style="font-size: 14px; font-weight: 800; color: var(--text-main); display: flex; align-items: center; gap: 8px;">
                    <span>Trung Tâm Điều Phối AI &amp; 7 Nguồn API Đã Được Tách Thành Trang Riêng Biệt</span>
                    <span class="badge badge-purple" style="font-size: 9px; padding: 2px 7px;">7 NGUỒN MỚI</span>
                </div>
                <div style="font-size: 12px; color: var(--text-sub); margin-top: 2px;">
                    Cấu hình Vyce, Groq, Gemini, Cloudflare, OpenRouter, 9Router, định tuyến mô hình, hạn mức token và độ trễ ping thực tế.
                </div>
            </div>
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <a href="/admin/ai-orchestration" class="btn btn-primary" style="padding: 8px 16px; font-size: 12.5px; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; background: #7c3aed; border-color: #6d28d9;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
                <span>Mở Điều Phối AI (7 Nguồn) ↗</span>
            </a>
            <a href="/admin/performance" class="btn" style="padding: 8px 16px; font-size: 12.5px; text-decoration: none; display: inline-flex; align-items: center; gap: 6px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
                <span>Xem Hiệu Suất &amp; Token ↗</span>
            </a>
        </div>
    </div>

    <!-- CÀI ĐẶT GIAO DỊCH & SÀN BINANCE -->
    <div id="panel-trading-setup" style="display: block;">
        {form_html}
    </div>

</div>
{{% endblock %}}
"""
    with open('c:/sunMy/trading_bot/web/templates/admin/settings.html', 'w', encoding='utf-8') as f_out:
        f_out.write(clean_settings)
    print("SUCCESS: Updated settings.html! Length:", len(clean_settings))
else:
    print("ERROR: Could not find form_html in settings.html.bak_dual_pages")
