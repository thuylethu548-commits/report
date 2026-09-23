import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=== AGENT DECK: SCANNING BYBIT DERIVATIVES TICKER & FUNDING RATE ===")

# Query Bybit v5 public tickers for linear contract AKEUSDT
url = "https://api.bybit.com/v5/market/tickers?category=linear&symbol=AKEUSDT"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        result = res.get("result", {})
        ticker_list = result.get("list", [])
        if ticker_list:
            t = ticker_list[0]
            print(f"Symbol: {t.get('symbol')}")
            print(f"Last Price: {t.get('lastPrice')}")
            print(f"Index Price: {t.get('indexPrice')}")
            print(f"Mark Price: {t.get('markPrice')}")
            print(f"24h High: {t.get('highPrice24h')}")
            print(f"24h Low: {t.get('lowPrice24h')}")
            print(f"24h Turnover: ${float(t.get('turnover24h', 0)):,.2f}")
            print(f"Open Interest: {t.get('openInterest')} (Value: ${float(t.get('openInterestValue', 0)):,.2f})")
            
            funding_rate = float(t.get('fundingRate', 0))
            predicted_funding = float(t.get('predictedDeliveryPrice', 0))
            print(f"Current Funding Rate: {funding_rate*100:.4f}%")
            print(f"Next Funding Time: {t.get('nextFundingTime')}")
            
            # Check premium / basis between Mark and Index
            mark = float(t.get('markPrice', 0))
            idx = float(t.get('indexPrice', 0))
            if idx > 0:
                premium = (mark - idx) / idx * 100
                print(f"Basis Premium (Mark vs Index): {premium:+.2f}%")
        else:
            print("No ticker found for AKEUSDT on Bybit linear.")
except Exception as e:
    print(f"Error querying Bybit: {e}")

# Query Bybit Orderbook Depth
ob_url = "https://api.bybit.com/v5/market/orderbook?category=linear&symbol=AKEUSDT&limit=5"
req_ob = urllib.request.Request(ob_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    print("\n=== AGENT MEME: CHECKING BYBIT ORDERBOOK DEPTH (TOP 5) ===")
    with urllib.request.urlopen(req_ob, timeout=10) as resp:
        res_ob = json.loads(resp.read().decode('utf-8'))
        ob = res_ob.get("result", {})
        bids = ob.get("b", [])
        asks = ob.get("a", [])
        
        print("Bids (Mua):")
        for p, sz in bids[:3]:
            val = float(p) * float(sz)
            print(f"  Price: {p} | Size: {float(sz):,.0f} | Value: ${val:,.2f}")
        print("Asks (Bán):")
        for p, sz in asks[:3]:
            val = float(p) * float(sz)
            print(f"  Price: {p} | Size: {float(sz):,.0f} | Value: ${val:,.2f}")
        
        if bids and asks:
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            spread_bps = (best_ask - best_bid) / best_bid * 10000
            print(f"Spread: {spread_bps:.2f} bps ({(best_ask-best_bid)/best_bid*100:.3f}%)")
except Exception as e:
    print(f"Error querying Orderbook: {e}")

print("\n=== BYBIT SCAN COMPLETED ===")
