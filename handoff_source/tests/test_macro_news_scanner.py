import pytest
from data.macro_news_scanner import MacroNewsScanner


def test_macro_scanner_analyzes_war_threat():
    scanner = MacroNewsScanner()
    headlines = [
        {"title": "Escalation in Middle East: Missile Strike Reported Near Border", "link": "http://example.com/1"},
        {"title": "Bitcoin Trades Sideways Above $60k", "link": "http://example.com/2"}
    ]
    res = scanner.analyze_headlines(headlines)
    assert res["state"] == "WAR_RISK_DEFENSIVE"
    assert res["emergency_defense"] is True
    assert len(res["active_threats"]) == 1
    assert "CHIẾN SỰ" in res["summary"]


def test_macro_scanner_analyzes_financial_shock():
    scanner = MacroNewsScanner()
    headlines = [
        {"title": "Major Exchange Facing Liquidity Crisis and Default Rumors", "link": "http://example.com/1"},
        {"title": "Ethereum Gas Fees Drop", "link": "http://example.com/2"}
    ]
    res = scanner.analyze_headlines(headlines)
    assert res["state"] == "FINANCIAL_SHOCK_DEFENSIVE"
    assert res["emergency_defense"] is True
    assert len(res["active_threats"]) == 1
    assert "BÃO VĨ MÔ" in res["summary"]


def test_macro_scanner_analyzes_bullish_catalysts():
    scanner = MacroNewsScanner()
    headlines = [
        {"title": "Fed Signals Rate Cut in Upcoming Meeting", "link": "http://example.com/1"},
        {"title": "Institutional Adoption Soars as ETF Inflow Hits $1 Billion", "link": "http://example.com/2"}
    ]
    res = scanner.analyze_headlines(headlines)
    assert res["state"] == "BULL_MACRO"
    assert res["emergency_defense"] is False
    assert len(res["bullish_signals"]) == 2


def test_macro_scanner_analyzes_normal_conditions():
    scanner = MacroNewsScanner()
    headlines = [
        {"title": "Crypto Developers Meet in Singapore for Annual Hackathon", "link": "http://example.com/1"},
        {"title": "New Layer 2 Network Launches Testnet", "link": "http://example.com/2"}
    ]
    res = scanner.analyze_headlines(headlines)
    assert res["state"] == "NORMAL"
    assert res["emergency_defense"] is False
    assert len(res["active_threats"]) == 0


@pytest.mark.asyncio
async def test_macro_scanner_fng_fallback():
    scanner = MacroNewsScanner(fng_url="http://invalid.unreachable.url/api")
    fng = await scanner.fetch_fear_and_greed()
    assert "value" in fng
    assert fng["value"] == 50
    assert fng["classification"] == "Neutral"
