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
    affiliate_links_json TEXT DEFAULT '{}',
    selling_points_json TEXT DEFAULT '[]',
    commission_rate REAL DEFAULT 0.0,
    objection_handling_json TEXT DEFAULT '{}',
    compliance_notes TEXT DEFAULT '',
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

-- Stream targets managed by dashboard control plane
CREATE TABLE IF NOT EXISTS stream_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    label TEXT NOT NULL,
    rtmp_url TEXT NOT NULL,
    stream_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 0,
    enabled BOOLEAN DEFAULT 1,
    validation_status TEXT DEFAULT 'unvalidated',
    validation_checks_json TEXT DEFAULT '[]',
    last_validated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stream_targets_platform ON stream_targets(platform, created_at);

-- Single-host live session ledger
CREATE TABLE IF NOT EXISTS live_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    status TEXT NOT NULL,
    stream_target_id INTEGER NOT NULL,
    rotation_mode TEXT DEFAULT 'operator_assisted',
    qna_mode TEXT DEFAULT 'enabled',
    pause_reason TEXT DEFAULT '',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stream_target_id) REFERENCES stream_targets(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_live_sessions_single_active
ON live_sessions(status)
WHERE status = 'active';

CREATE TABLE IF NOT EXISTS session_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    queue_order INTEGER DEFAULT 0,
    enabled_for_rotation BOOLEAN DEFAULT 1,
    operator_priority INTEGER DEFAULT 0,
    ai_score REAL DEFAULT 0.0,
    cooldown_until TIMESTAMP,
    last_pitched_at TIMESTAMP,
    times_pitched INTEGER DEFAULT 0,
    last_question_at TIMESTAMP,
    state TEXT DEFAULT 'ready',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    UNIQUE(session_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_session_products_session_queue
ON session_products(session_id, queue_order);

CREATE TABLE IF NOT EXISTS session_state (
    session_id INTEGER PRIMARY KEY,
    current_mode TEXT DEFAULT 'ROTATING',
    current_phase TEXT DEFAULT 'IDLE',
    rotation_paused BOOLEAN DEFAULT 0,
    pause_reason TEXT DEFAULT '',
    current_focus_product_id INTEGER,
    current_focus_session_product_id INTEGER,
    pending_question_json TEXT,
    awaiting_operator BOOLEAN DEFAULT 0,
    active_prompt_revision TEXT DEFAULT '',
    active_provider TEXT DEFAULT '',
    active_model TEXT DEFAULT '',
    stream_status TEXT DEFAULT 'idle',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (current_focus_product_id) REFERENCES products(id),
    FOREIGN KEY (current_focus_session_product_id) REFERENCES session_products(id)
);

CREATE TABLE IF NOT EXISTS operator_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    command_name TEXT NOT NULL,
    payload_json TEXT DEFAULT '{}',
    status TEXT NOT NULL,
    actor TEXT DEFAULT 'operator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_operator_commands_session
ON operator_commands(session_id, created_at);

CREATE TABLE IF NOT EXISTS runtime_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    event_type TEXT NOT NULL,
    payload_json TEXT DEFAULT '{}',
    severity TEXT DEFAULT 'info',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_runtime_events_session
ON runtime_events(session_id, created_at);

-- Prompt registry revisions
CREATE TABLE IF NOT EXISTS prompt_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    version INTEGER NOT NULL,
    status TEXT NOT NULL,
    templates_json TEXT NOT NULL,
    persona_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(slug, version)
);

CREATE INDEX IF NOT EXISTS idx_prompt_revisions_slug_status ON prompt_revisions(slug, status);
