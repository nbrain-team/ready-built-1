-- Migration: Add Social Media Automator tables
-- This adds support for video processing and social media campaign management

-- Create clients table
CREATE TABLE IF NOT EXISTS social_media_automator_clients (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    industry VARCHAR(100),
    description TEXT,
    brand_voice TEXT,
    target_audience TEXT,
    brand_colors JSONB DEFAULT '[]',
    logo_url VARCHAR(500),
    social_accounts JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id VARCHAR(36) PRIMARY KEY,
    client_id VARCHAR(36) NOT NULL REFERENCES social_media_automator_clients(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    original_video_url VARCHAR(500) NOT NULL,
    duration_weeks INTEGER NOT NULL,
    platforms TEXT[] NOT NULL,
    status VARCHAR(20) DEFAULT 'processing',
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create video clips table
CREATE TABLE IF NOT EXISTS video_clips (
    id VARCHAR(36) PRIMARY KEY,
    campaign_id VARCHAR(36) NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    duration FLOAT NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    video_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    platform_versions JSONB DEFAULT '{}',
    suggested_caption TEXT,
    suggested_hashtags TEXT[],
    content_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create social posts table
CREATE TABLE IF NOT EXISTS social_posts (
    id VARCHAR(36) PRIMARY KEY,
    client_id VARCHAR(36) NOT NULL REFERENCES social_media_automator_clients(id) ON DELETE CASCADE,
    campaign_id VARCHAR(36) REFERENCES campaigns(id),
    video_clip_id VARCHAR(36) REFERENCES video_clips(id),
    content TEXT NOT NULL,
    platforms TEXT[] NOT NULL,
    media_urls TEXT[] DEFAULT '{}',
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    published_at TIMESTAMP WITH TIME ZONE,
    platform_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX idx_social_media_automator_clients_user_id ON social_media_automator_clients(user_id);
CREATE INDEX idx_campaigns_client_id ON campaigns(client_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_video_clips_campaign_id ON video_clips(campaign_id);
CREATE INDEX idx_social_posts_client_id ON social_posts(client_id);
CREATE INDEX idx_social_posts_campaign_id ON social_posts(campaign_id);
CREATE INDEX idx_social_posts_scheduled_time ON social_posts(scheduled_time);
CREATE INDEX idx_social_posts_status ON social_posts(status); 