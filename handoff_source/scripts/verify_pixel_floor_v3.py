import httpx, sys
sys.stdout.reconfigure(encoding='utf-8')

token = '***REDACTED***'

# 1. Test Telemetry API
r_api = httpx.get('http://localhost:8386/api/v1/telemetry/pixel-floor')
print(f"API Status: {r_api.status_code}")
data = r_api.json()
print(f"  Total Departments: {data.get('total_departments')}")
print(f"  Verified Online: {data.get('verified_online_count')}")
print(f"  Wings: {list(data.get('wings', {}).keys())}")
print(f"  Telegram Debate Feed Items: {len(data.get('telegram_debate_feed', []))}")
if data.get('telegram_debate_feed'):
    sample = data['telegram_debate_feed'][0]
    print(f"    Sample Debate: {sample.get('badge')} | {sample.get('symbol')} | {sample.get('speech')}")

# Check Rik's emotion
rik = data.get('departments', {}).get('risk_council', {})
print(f"  Rik CRO Mood: {rik.get('npc_mood')} | Quote: {rik.get('persona_quote')}")

# 2. Test Admin HTML Page
r_html = httpx.get('http://localhost:8386/admin/pixel-floor', cookies={'admin_session_token': token})
print(f"\nHTML Status: {r_html.status_code}")
print(f"HTML Content Length: {len(r_html.text)} bytes")

checks = [
    ("Campus Wings Bar", "campus-wings-bar" in r_html.text),
    ("Tab Filter: Executive", "filterCampusWing('executive'" in r_html.text),
    ("Tab Filter: Trading", "filterCampusWing('trading'" in r_html.text),
    ("Tab Filter: Research", "filterCampusWing('research'" in r_html.text),
    ("Tab Filter: Operations", "filterCampusWing('operations'" in r_html.text),
    ("Sleek Cards Class", "dept-sleek-card" in r_html.text),
    ("Telegram Debate Feed", "telegram-debate-feed-list" in r_html.text),
    ("4 Distinct Rooms Canvas", "4 PHÂN KHU RIÊNG BIỆT" in r_html.text),
    ("Spot Portfolio", "SPOT PORTFOLIO · DCA SWING ENGINE" in r_html.text),
    ("Model Health 7 Nguon", "TÀI NGUYÊN AI & MODEL (7 NGUỒN TRỰC CHIẾN)" in r_html.text),
]

all_ok = True
for name, ok in checks:
    status = "OK" if ok else "FAIL"
    if not ok: all_ok = False
    print(f"  [{status}] {name}")

cards = [
    'lead_pm', 'risk_council', 'news_scout', 'quant_lab',
    'breakout_hunter', 'volatility_lab', 'execution_oms', 'spot_dca',
    'arbitrage_desk', 'accounting_pm', 'community_affiliate', 'cvar_stress'
]
cards_ok = all(f'id="card-{c}"' in r_html.text for c in cards)
print(f"\n12 Sleek Cards Present: {cards_ok}")
print(f"Overall Verification V3.0: {'PASSED' if (all_ok and cards_ok) else 'FAILED'}")
