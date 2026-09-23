"""Read-only Binance USD-M testnet preflight. Never imports application settings."""
import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse

import ccxt.async_support as ccxt
from dotenv import dotenv_values


def load_credentials(path):
    path = Path(path).resolve()
    if path.name != '.env.testnet':
        raise ValueError('Use a dedicated file named .env.testnet; production .env is rejected')
    if not path.is_file():
        raise ValueError('Missing .env.testnet file')
    config = dotenv_values(path, interpolate=False)
    if config.get('TRADING_MODE') != 'testnet' or config.get('BINANCE_USE_TESTNET', '').lower() != 'true':
        raise ValueError('Explicit TRADING_MODE=testnet and BINANCE_USE_TESTNET=true required')
    if config.get('MARKET_TYPE') != 'futures':
        raise ValueError('MARKET_TYPE=futures required')
    if config.get('AUTO_TRADE_ENABLED', '').lower() != 'false':
        raise ValueError('AUTO_TRADE_ENABLED=false required for preflight')
    key, secret = config.get('BINANCE_API_KEY'), config.get('BINANCE_API_SECRET')
    if not key or not secret or key.startswith('mock') or secret.startswith('mock'):
        raise ValueError('Populate dedicated testnet API credentials locally')
    return key, secret


def check_testnet_routes(exchange):
    hosts = set()
    for route in ('fapiPublic', 'fapiPrivate', 'fapiPrivateV2', 'fapiPrivateV3'):
        url = exchange.urls['api'].get(route)
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname != 'testnet.binancefuture.com':
            raise ValueError('Exchange adapter points outside the approved futures testnet host')
        hosts.add(parsed.hostname)
    if not hosts:
        raise ValueError('No futures testnet routes')
    return sorted(hosts)


async def preflight(path):
    key, secret = load_credentials(path)
    exchange = ccxt.binance({'apiKey': key, 'secret': secret, 'enableRateLimit': True,
        'options': {'defaultType': 'future', 'fetchMarkets': {'types': ['linear']}}})
    try:
        exchange.set_sandbox_mode(True)
        hosts = check_testnet_routes(exchange)
        # Raw GET-only routes avoid unrelated spot endpoints and submit no order/config change.
        info = await exchange.fapiPublicGetExchangeInfo()
        mode = await exchange.fapiPrivateGetPositionSideDual()
        account = await exchange.fapiPrivateV2GetAccount()
        position_count = sum(float(p.get('positionAmt') or 0) != 0 for p in account.get('positions', []))
        one_way = mode.get('dualSidePosition') in (False, 'false')
        return {'status': 'READY_FOR_SUPERVISED_TESTS' if one_way and position_count == 0 else 'BLOCKED',
                'hosts': hosts, 'one_way': one_way, 'open_positions': position_count,
                'market_count': len(info.get('symbols', [])), 'orders_submitted': 0,
                'note': 'Connectivity preflight only; does not certify stop or execution behavior'}
    finally:
        await exchange.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env-file', default='.env.testnet')
    args = parser.parse_args()
    try:
        result = asyncio.run(preflight(args.env_file))
    except ValueError as exc:
        result = {'status': 'BLOCKED', 'reason': str(exc), 'orders_submitted': 0}
    except Exception as exc:
        # Exchange exception strings may contain signed request URLs. Print only the class.
        result = {'status': 'BLOCKED', 'reason': type(exc).__name__, 'orders_submitted': 0}
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'READY_FOR_SUPERVISED_TESTS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
