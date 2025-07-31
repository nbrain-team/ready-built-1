-- Create Read.ai Integration Tables
-- Run this migration to add Read.ai webhook support

-- Read.ai Integration Settings
CREATE TABLE IF NOT EXISTS readai_integrations (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    webhook_secret VARCHAR(255),
    integration_status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    last_webhook_at TIMESTAMP WITH TIME ZONE
);

-- Create index for user lookups
CREATE INDEX idx_readai_integrations_user_id ON readai_integrations(user_id);

-- Read.ai Meeting Records
CREATE TABLE IF NOT EXISTS readai_meetings (
    id VARCHAR(255) PRIMARY KEY,
    integration_id VARCHAR(255) NOT NULL REFERENCES readai_integrations(id) ON DELETE CASCADE,
    readai_meeting_id VARCHAR(255) UNIQUE NOT NULL,
    meeting_title VARCHAR(500) NOT NULL,
    meeting_url TEXT,
    meeting_platform VARCHAR(100),
    
    -- Participants
    participants JSONB,
    host_email VARCHAR(255),
    
    -- Timing
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_minutes FLOAT,
    
    -- Content
    transcript TEXT,
    summary TEXT,
    key_points JSONB,
    action_items JSONB,
    
    -- Analysis
    sentiment_score FLOAT,
    engagement_score FLOAT,
    
    -- Associations
    client_id VARCHAR(255) REFERENCES clients(id) ON DELETE SET NULL,
    
    -- Oracle Integration
    synced_to_oracle BOOLEAN DEFAULT FALSE,
    oracle_action_items_created INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    webhook_received_at TIMESTAMP WITH TIME ZONE,
    raw_webhook_data JSONB
);

-- Create indexes for efficient queries
CREATE INDEX idx_readai_meetings_integration_id ON readai_meetings(integration_id);
CREATE INDEX idx_readai_meetings_client_id ON readai_meetings(client_id);
CREATE INDEX idx_readai_meetings_start_time ON readai_meetings(start_time DESC);
CREATE INDEX idx_readai_meetings_readai_id ON readai_meetings(readai_meeting_id);

-- Add to Oracle data sources to show Read.ai as a connected source
INSERT INTO oracle_data_sources (id, user_id, source_type, status, created_at)
SELECT 
    gen_random_uuid()::text,
    u.id,
    'meeting',
    'connected',
    CURRENT_TIMESTAMP
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM oracle_data_sources 
    WHERE user_id = u.id AND source_type = 'meeting'
); 