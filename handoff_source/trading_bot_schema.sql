-- ASTRA QUANT DATABASE SCHEMA DUMP
-- Generated for bot-trade-bi-okx

CREATE TABLE affiliate_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    referral_code TEXT,
                    event_time TEXT NOT NULL,
                    reward_amount REAL,
                    currency TEXT,
                    status TEXT NOT NULL DEFAULT 'UNVERIFIED',
                    source TEXT NOT NULL DEFAULT 'manual_dashboard',
                    external_ref TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(platform, external_ref)
                );

CREATE TABLE ai_advisory_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    regime TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    trade_allowed INTEGER NOT NULL,
                    size_multiplier REAL NOT NULL,
                    reasoning TEXT,
                    timestamp TEXT NOT NULL
                , confidence REAL DEFAULT 1.0);

CREATE TABLE ai_token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model TEXT NOT NULL,
                    action TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    estimated_cost_usd REAL NOT NULL
                );

CREATE TABLE candles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    UNIQUE(symbol, timestamp)
                );

CREATE TABLE client_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    quantity REAL NOT NULL,
                    notional_value REAL NOT NULL,
                    pnl_usdt REAL DEFAULT 0.0,
                    profit_share_due REAL DEFAULT 0.0,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

CREATE TABLE equity_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    balance_usdt REAL NOT NULL,
                    equity_usdt REAL NOT NULL,
                    open_positions INTEGER NOT NULL,
                    daily_drawdown REAL NOT NULL
                );

CREATE TABLE execution_state (id INTEGER PRIMARY KEY, payload TEXT NOT NULL);

CREATE TABLE signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    price REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    approved INTEGER NOT NULL,
                    rejection_reason TEXT
                );

CREATE TABLE system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    description TEXT,
                    updated_at TEXT NOT NULL
                );

CREATE TABLE trades (
                    order_id TEXT PRIMARY KEY,
                    strategy_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    quantity REAL NOT NULL,
                    fee REAL NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT,
                    pnl_usdt REAL,
                    pnl_percent REAL,
                    is_paper INTEGER NOT NULL,
                    status TEXT NOT NULL
                );

CREATE TABLE trading_lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL,
                    capital_impact REAL,
                    lesson_learned TEXT NOT NULL,
                    operator TEXT DEFAULT 'Astra-Supervisor'
                );

CREATE TABLE trial_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    notional_value REAL NOT NULL DEFAULT 50.0,
                    leverage INTEGER NOT NULL DEFAULT 5,
                    entry_price REAL NOT NULL,
                    current_price REAL,
                    exit_price REAL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    pnl_usdt REAL DEFAULT 0.0,
                    pnl_percent REAL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    claimed_reward REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );

CREATE TABLE user_api_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    api_key TEXT NOT NULL,
                    api_secret TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    label TEXT DEFAULT 'Binance Futures Account',
                    leverage INTEGER NOT NULL DEFAULT 3,
                    max_margin_usdt REAL NOT NULL DEFAULT 50.0,
                    profit_share_pct REAL NOT NULL DEFAULT 0.25,
                    withdrawals_disabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    full_name TEXT,
                    email TEXT,
                    role TEXT NOT NULL DEFAULT 'client',
                    created_at TEXT NOT NULL
                , google_id TEXT, picture TEXT);
