import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

CONTRACT = "0x2c3a8Ee94dDD97244a93Bc48298f97d2C412F7Db"
print(f"=== AGENT HASH: SCANNING ON-CHAIN DATA FOR TOKEN {CONTRACT} ===")

# 1. Query DexScreener API
url = f"https://api.dexscreener.com/latest/dex/tokens/{CONTRACT}"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        pairs = data.get("pairs") or []
        print(f"Total Dex Pools found: {len(pairs)}")
        for idx, p in enumerate(pairs[:5]):
            dex = p.get("dexId")
            chain = p.get("chainId")
            base = p.get("baseToken", {}).get("symbol")
            quote = p.get("quoteToken", {}).get("symbol")
            price_usd = p.get("priceUsd")
            liquidity = p.get("liquidity", {}).get("usd")
            vol24 = p.get("volume", {}).get("h24")
            fdv = p.get("fdv")
            print(f"\n--- Pool {idx+1}: {dex.upper()} on {chain.upper()} ({base}/{quote}) ---")
            print(f"  Price USD: ${price_usd}")
            print(f"  Liquidity USD: ${liquidity:,.2f}" if liquidity else "  Liquidity USD: N/A")
            print(f"  Volume 24h: ${vol24:,.2f}" if vol24 else "  Volume 24h: N/A")
            print(f"  FDV: ${fdv:,.2f}" if fdv else "  FDV: N/A")
            print(f"  Pair Address: {p.get('pairAddress')}")
except Exception as e:
    print(f"Error querying DexScreener: {e}")

# 2. Query GoPlus Security API for token security (honeypot, tax, blacklist)
goplus_url = f"https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses={CONTRACT}"
req_gp = urllib.request.Request(goplus_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    print(f"\n=== AGENT PROF: AUDITING SMART CONTRACT SECURITY (GOPLUS LABS) ===")
    with urllib.request.urlopen(req_gp, timeout=10) as resp:
        sec_data = json.loads(resp.read().decode('utf-8'))
        result = sec_data.get("result", {}).get(CONTRACT.lower(), {})
        if result:
            print(f"  Is Honeypot: {result.get('is_honeypot')}")
            print(f"  Buy Tax: {result.get('buy_tax', '0')}%")
            print(f"  Sell Tax: {result.get('sell_tax', '0')}%")
            print(f"  Cannot Sell All: {result.get('cannot_sell_all')}")
            print(f"  Is Blacklist: {result.get('is_blacklisted')}")
            print(f"  Is Open Source: {result.get('is_open_source')}")
            print(f"  Creator Address: {result.get('creator_address')}")
            print(f"  Owner Address: {result.get('owner_address')}")
            print(f"  Total Supply: {result.get('total_supply')}")
            holders = result.get('holders', [])
            print(f"  Top Holders count: {len(holders)}")
            for h in holders[:3]:
                print(f"    - Holder {h.get('address')[:10]}...: {float(h.get('percent', 0))*100:.2f}% (Is Contract: {h.get('is_contract')})")
        else:
            print("No security audit record found on GoPlus.")
except Exception as e:
    print(f"Error querying GoPlus: {e}")

print("\n=== SCAN COMPLETED ===")
