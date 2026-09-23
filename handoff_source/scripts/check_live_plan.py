import urllib.request
import json
from datetime import datetime, timezone

def fetch_klines(symbol, interval='15m', limit=8):
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, timeout=5)
    raw = json.loads(res.read().decode())
    candles = []
    for c in raw:
        candles.append({
            'time': c[0],
            'open': float(c[1]),
            'high': float(c[2]),
            'low': float(c[3]),
            'close': float(c[4]),
            'vol': float(c[5])
        })
    return candles

for sym in ['BTCUSDT', 'SOLUSDT', 'ETHUSDT']:
    k = fetch_klines(sym, '15m', 6)
    print(f'=== LAST 6 15M CANDLES FOR {sym} ===')
    for c in k:
        dt_str = datetime.fromtimestamp(c['time']/1000, tz=timezone.utc).strftime('%H:%M')
        chg = (c['close'] - c['open']) / c['open'] * 100
        print(f"  {dt_str} UTC: O={c['open']:,.2f} | H={c['high']:,.2f} | L={c['low']:,.2f} | C={c['close']:,.2f} | Chg={chg:+.2f}% | Vol={c['vol']:,.1f}")
