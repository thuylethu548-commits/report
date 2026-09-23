import httpx

token = '***REDACTED***'
r = httpx.get('http://localhost:8386/admin/pixel-floor', cookies={'admin_session_token': token})

cards = [
    'lead_pm', 'risk_council', 'news_scout', 'quant_lab',
    'breakout_hunter', 'volatility_lab', 'execution_oms', 'spot_dca',
    'arbitrage_desk', 'accounting_pm', 'community_affiliate', 'cvar_stress'
]

print(f"Status Code: {r.status_code}")
print(f"Content Length: {len(r.text)} bytes")

print("\n=== 12 DEPARTMENT CARDS ===")
all_cards_ok = True
for c in cards:
    present = f'id="card-{c}"' in r.text
    status = "OK" if present else "MISSING"
    if not present:
        all_cards_ok = False
    print(f"  [{status}] card-{c}")

print("\n=== CORE PANELS ===")
panels = [
    ("Spot Portfolio", "SPOT PORTFOLIO"),
    ("Fleet 10 Agents", "FLEET MANAGER · 10 AGENTS"),
    ("Model Health (7 Nguon)", "TÀI NGUYÊN AI & MODEL (7 NGUỒN)"),
    ("Vyce AI Health", "Vyce AI"),
    ("Groq Health", "Groq"),
    ("Gemini Health", "Gemini"),
    ("9Router Health", "9Router"),
    ("Cloudflare Health", "Cloudflare"),
    ("OpenRouter Health", "OpenRouter"),
    ("ETFBit Health", "ETFBit"),
    ("2.5D Isometric Canvas", "office-stage-canvas"),
    ("Dynamic Modal", "pixelDeptModal"),
]

all_panels_ok = True
for name, tag in panels:
    present = tag in r.text
    status = "OK" if present else "MISSING"
    if not present:
        all_panels_ok = False
    print(f"  [{status}] {name}")

print(f"\nSummary: All Cards OK: {all_cards_ok} | All Panels OK: {all_panels_ok}")
