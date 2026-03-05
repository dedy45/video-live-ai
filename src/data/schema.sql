-- AI Live Commerce Platform — Database Schema
-- SQLite initialization script
-- Requirements: 7.1, 8.4, 11.1, 11.9

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    image_path TEXT,
    description TEXT,
    stock INTEGER DEFAULT 0,
    category TEXT DEFAULT 'general',
    margin_percent REAL DEFAULT 0.0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product display metrics
CREATE TABLE IF NOT EXISTS product_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    display_count INTEGER DEFAULT 0,
    total_display_seconds REAL DEFAULT 0.0,
    click_count INTEGER DEFAULT 0,
    cart_count INTEGER DEFAULT 0,
    purchase_count INTEGER DEFAULT 0,
    date TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Chat events log
CREATE TABLE IF NOT EXISTS chat_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,  -- 'tiktok' or 'shopee'
    username TEXT,
    message TEXT,
    priority INTEGER DEFAULT 1,  -- P1-P5
    intent TEXT,  -- purchase_intent, question, humor, general
    trace_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LLM usage tracking
CREATE TABLE IF NOT EXISTS llm_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    task_type TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    latency_ms REAL DEFAULT 0.0,
    cost_usd REAL DEFAULT 0.0,
    success BOOLEAN DEFAULT 1,
    trace_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Affiliate events
CREATE TABLE IF NOT EXISTS affiliate_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    product_id INTEGER,
    event_type TEXT NOT NULL,  -- click, add_to_cart, purchase
    estimated_commission REAL DEFAULT 0.0,
    currency TEXT DEFAULT 'IDR',
    trace_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- System metrics (time-series)
CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    component TEXT,  -- brain, voice, face, etc.
    trace_id TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Safety incidents log
CREATE TABLE IF NOT EXISTS safety_incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_text TEXT,
    replaced_text TEXT,
    trigger_type TEXT,  -- keyword_blacklist, moderation_api
    severity TEXT DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_chat_events_created ON chat_events(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_events_priority ON chat_events(priority);
CREATE INDEX IF NOT EXISTS idx_llm_usage_provider ON llm_usage(provider, created_at);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name, recorded_at);
CREATE INDEX IF NOT EXISTS idx_affiliate_platform ON affiliate_events(platform, created_at);
CREATE INDEX IF NOT EXISTS idx_product_metrics_date ON product_metrics(product_id, date);
