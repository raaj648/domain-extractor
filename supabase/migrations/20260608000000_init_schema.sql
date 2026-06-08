-- Create settings table
CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed initial settings keys
INSERT INTO settings (key, value) VALUES
('telegram', '{"bot_token": "", "chat_id": "", "notify_on_discovery": true, "notify_on_delete_day": true, "notify_on_available": true, "notify_on_errors": true}'::jsonb),
('cookies', '{"sessionid": "", "expireddomains_session": ""}'::jsonb),
('github', '{"repo_owner": "", "repo_name": "", "pat_token": ""}'::jsonb)
ON CONFLICT (key) DO NOTHING;

-- Create targets table
CREATE TABLE IF NOT EXISTS targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_scraped_at TIMESTAMPTZ
);

-- Create tracked_domains table
CREATE TABLE IF NOT EXISTS tracked_domains (
    domain VARCHAR(255) PRIMARY KEY,
    tld VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending_delete', -- pending_delete, available, registered, ignored, purchased
    delete_date DATE,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    last_checked_at TIMESTAMPTZ,
    source_target_id UUID REFERENCES targets(id) ON DELETE SET NULL,
    metrics JSONB DEFAULT '{}'::jsonb, -- backlinks, alexa, age, majestic_tf, moz_da, etc.
    notified_found BOOLEAN DEFAULT FALSE,
    notified_delete_day BOOLEAN DEFAULT FALSE,
    notified_available BOOLEAN DEFAULT FALSE
);

-- Create scrape_jobs table
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'running', -- running, success, failed
    domains_found INTEGER DEFAULT 0,
    domains_inserted INTEGER DEFAULT 0,
    logs TEXT,
    error_message TEXT
);

-- Create cron_runs table
CREATE TABLE IF NOT EXISTS cron_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_time TIMESTAMPTZ DEFAULT NOW(),
    duration_ms INTEGER,
    domains_checked JSONB DEFAULT '[]'::jsonb,
    domains_available INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'success', -- success, failed
    error_message TEXT
);
