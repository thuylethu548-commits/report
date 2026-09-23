import re

with open('c:/sunMy/trading_bot/web/templates/admin/settings.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Match the panel-ai-orchestration div content
match = re.search(r'(<!--\s*7 TABS BAR\s*-->.*?)(?=\s*</div>\s*</div>\s*<script src="/static/js/orchestration.js">)', content, re.DOTALL)

if match:
    tabs_content = match.group(1).strip()
    
    ai_template = f"""{{% extends "layouts/admin_base.html" %}}

{{% block extra_css %}}
<link rel="stylesheet" href="/static/css/orchestration.css">
<style>
.orch-stats-strip {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 18px;
}}
@media (max-width: 900px) {{
    .orch-stats-strip {{
        grid-template-columns: repeat(2, 1fr);
    }}
}}
.orch-stat-card {{
    background: var(--bg-card, #ffffff);
    border: 1px solid var(--border, #e2e8f0);
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    display: flex;
    flex-direction: column;
    gap: 4px;
}}
.orch-stat-label {{
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    color: var(--text-muted, #64748b);
}}
.orch-stat-val {{
    font-size: 22px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
}}
.orch-stat-sub {{
    font-size: 11px;
    color: var(--text-sub, #94a3b8);
}}
</style>
{{% endblock %}}

{{% block content %}}
<div class="orch-container">
    
    <!-- HEADER AREA -->
    <div class="orch-header" id="page-main-header">
        <div class="orch-title-wrap">
            <div class="orch-icon-badge" style="background: rgba(168, 85, 247, 0.12); color: #a855f7;">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>
                </svg>
            </div>
            <div>
                <h1 class="orch-title">Trung Tâm Điều Phối AI &amp; Quản Trị 7 Nguồn API</h1>
                <p class="orch-subtitle">
                    Quản lý tập trung 7 nhà cung cấp AI (Vyce, Groq, Gemini, Cloudflare, OpenRouter, 9Router, Local), định tuyến mô hình, hạn mức token và kiểm tra độ trễ.
                </p>
            </div>
        </div>
        <div class="orch-header-actions">
            <a href="/admin/settings" class="orch-doc-btn" style="text-decoration: none; color: #10b981; border-color: rgba(16, 185, 129, 0.4);">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="1" x2="7" y1="14" y2="14"/><line x1="9" x2="15" y1="8" y2="8"/><line x1="17" x2="23" y1="16" y2="16"/></svg>
                <span>⚡ Sang Cài Đặt Sàn Binance ↗</span>
            </a>
            <a href="/admin/performance" class="orch-doc-btn" style="text-decoration: none; color: #0284c7; border-color: rgba(2, 132, 199, 0.4);">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
                <span>📊 Xem Hiệu Suất &amp; Token ↗</span>
            </a>
        </div>
    </div>

    <!-- 4 TOP STATS CARDS -->
    <div class="orch-stats-strip">
        <div class="orch-stat-card">
            <div class="orch-stat-label">TỔNG NHÀ CUNG CẤP</div>
            <div class="orch-stat-val" id="stat-total-providers" style="color: #2563eb;">6+</div>
            <div class="orch-stat-sub">Vyce, Groq, Gemini, Cloudflare, OpenRouter, 9Router</div>
        </div>
        <div class="orch-stat-card">
            <div class="orch-stat-label">MÔ HÌNH HOẠT ĐỘNG</div>
            <div class="orch-stat-val" id="stat-total-models" style="color: #10b981;">164</div>
            <div class="orch-stat-sub">Claude, DeepSeek, Llama-3, Gemini, GPT-5.6</div>
        </div>
        <div class="orch-stat-card">
            <div class="orch-stat-label">ĐỘ TRỄ TRUNG BÌNH</div>
            <div class="orch-stat-val" id="stat-avg-latency" style="color: #a855f7;">245ms</div>
            <div class="orch-stat-sub">Groq 12ms | Gemini 240ms | Vyce 849ms</div>
        </div>
        <div class="orch-stat-card">
            <div class="orch-stat-label">TỶ LỆ KHẢ DỤNG (UPTIME)</div>
            <div class="orch-stat-val" id="stat-uptime" style="color: #10b981;">99.8%</div>
            <div class="orch-stat-sub">Độ tin cậy toàn mạng lưới</div>
        </div>
    </div>

    <!-- 7 TABS CONTAINER (ALWAYS FLEX & 100% VISIBLE) -->
    <div id="panel-ai-orchestration" style="display: flex; flex-direction: column; gap: 20px;">
        {tabs_content}
    </div>

</div>

<script src="/static/js/orchestration.js"></script>
{{% endblock %}}
"""
    with open('c:/sunMy/trading_bot/web/templates/admin/ai_orchestration.html', 'w', encoding='utf-8') as f_out:
        f_out.write(ai_template)
    print("SUCCESS: Generated web/templates/admin/ai_orchestration.html with", len(tabs_content), "chars")
else:
    print("ERROR: Regex did not match!")
