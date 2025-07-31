-- Create recordings table for storing meeting recordings
CREATE TABLE IF NOT EXISTS recordings (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(36),
    client_name VARCHAR(255),
    context VARCHAR(50) NOT NULL, -- 'client' or 'oracle'
    audio_path TEXT NOT NULL,
    duration INTEGER NOT NULL, -- in seconds
    transcript TEXT,
    action_items JSON,
    recommendations JSON,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    INDEX idx_user_recordings (user_id),
    INDEX idx_client_recordings (client_id),
    INDEX idx_context (context),
    INDEX idx_created_at (created_at)
);

-- Add source column to client_tasks if it doesn't exist
ALTER TABLE client_tasks 
ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual' COMMENT 'Source of the task: manual, recording, ai, etc.'; 