import pytest
import pandas as pd
from strategies.spot_dca_strategy import SpotDCAStrategy
from config.settings import settings

def test_btc_pyramid_dca_anchor_buy():
    strat = SpotDCAStrategy(total_capital_usdt=500.0)
    df = pd.DataFrame({"close": [86000.0] * 25})
    holding = {"amount": 0.0, "avg_price": 0.0}
    
    # Tier 1 Anchor Buy
    sig = strat.evaluate_signal("BTC/USDT", df, holding)
    assert sig["action"] == "BUY"
    assert sig["usdt_amount"] == 150.0  # 30% of 500
    assert "BTC_TIER_1_ANCHOR" in sig["reason"]

def test_btc_pyramid_dca_tier2_dip():
    strat = SpotDCAStrategy(total_capital_usdt=500.0)
    df1 = pd.DataFrame({"close": [86000.0] * 25})
    holding = {"amount": 0.0, "avg_price": 0.0}
    strat.evaluate_signal("BTC/USDT", df1, holding) # Anchor filled at 86000
    
    # Price dips to 83000 (below 83800 support)
    df2 = pd.DataFrame({"close": [83000.0] * 25})
    holding2 = {"amount": 0.00174, "avg_price": 86000.0}
    sig2 = strat.evaluate_signal("BTC/USDT", df2, holding2)
    assert sig2["action"] == "BUY"
    assert sig2["usdt_amount"] == 200.0  # 40% of 500
    assert "BTC_TIER_2_SUPPORT_DIP" in sig2["reason"]

def test_btc_pyramid_take_profit_ladder():
    strat = SpotDCAStrategy(total_capital_usdt=500.0)
    strat.btc_tier1_filled = True
    strat.btc_tier1_price = 85000.0
    
    # Price reaches 90500 >= 90000
    df_tp1 = pd.DataFrame({"close": [90500.0] * 25})
    holding = {"amount": 0.004, "avg_price": 85000.0}
    sig_tp1 = strat.evaluate_signal("BTC/USDT", df_tp1, holding)
    assert sig_tp1["action"] == "SELL"
    assert sig_tp1["percent"] == 33.0
    assert "BTC_TP1_LADDER" in sig_tp1["reason"]
