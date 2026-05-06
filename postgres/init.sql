CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    message_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    username VARCHAR(80) NOT NULL,
    content TEXT NOT NULL CHECK (length(trim(content)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE messages ADD COLUMN IF NOT EXISTS message_id UUID;
UPDATE messages SET message_id = gen_random_uuid() WHERE message_id IS NULL;
ALTER TABLE messages ALTER COLUMN message_id SET DEFAULT gen_random_uuid();
ALTER TABLE messages ALTER COLUMN message_id SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_message_id ON messages (message_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (created_at);
CREATE INDEX IF NOT EXISTS idx_messages_username ON messages (username);

CREATE TABLE IF NOT EXISTS chat_events (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    event_type VARCHAR(80) NOT NULL,
    username VARCHAR(80) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE chat_events ADD COLUMN IF NOT EXISTS event_id UUID;
CREATE UNIQUE INDEX IF NOT EXISTS idx_chat_events_event_id ON chat_events (event_id);
CREATE INDEX IF NOT EXISTS idx_chat_events_created_at ON chat_events (created_at);
CREATE INDEX IF NOT EXISTS idx_chat_events_type_created_at ON chat_events (event_type, created_at);

CREATE TABLE IF NOT EXISTS chat_hourly_stats (
    id BIGSERIAL PRIMARY KEY,
    hour TIMESTAMPTZ NOT NULL UNIQUE,
    total_messages INTEGER NOT NULL DEFAULT 0,
    total_joins INTEGER NOT NULL DEFAULT 0,
    total_leaves INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_hourly_stats_hour ON chat_hourly_stats (hour);

CREATE TABLE IF NOT EXISTS moderation_alerts (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL,
    message_id UUID,
    username VARCHAR(80) NOT NULL,
    reason VARCHAR(80) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    content_preview TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (event_id, reason)
);

CREATE INDEX IF NOT EXISTS idx_moderation_alerts_created_at ON moderation_alerts (created_at);
CREATE INDEX IF NOT EXISTS idx_moderation_alerts_reason_created_at ON moderation_alerts (reason, created_at);
CREATE INDEX IF NOT EXISTS idx_moderation_alerts_username_created_at ON moderation_alerts (username, created_at);
