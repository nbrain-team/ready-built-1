-- Create recordings table
CREATE TABLE IF NOT EXISTS recordings (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(36),
    client_name VARCHAR(255),
    context VARCHAR(50) NOT NULL,
    audio_path TEXT NOT NULL,
    duration INTEGER NOT NULL,
    transcript TEXT,
    action_items JSONB,
    recommendations JSONB,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- Create recordings indexes
CREATE INDEX IF NOT EXISTS idx_user_recordings ON recordings(user_id);
CREATE INDEX IF NOT EXISTS idx_client_recordings ON recordings(client_id);
CREATE INDEX IF NOT EXISTS idx_context ON recordings(context);
CREATE INDEX IF NOT EXISTS idx_created_at ON recordings(created_at);

-- Add source column to client_tasks
ALTER TABLE client_tasks 
ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual';

-- Create oracle_emails table
CREATE TABLE IF NOT EXISTS oracle_emails (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    message_id VARCHAR(255),
    thread_id VARCHAR(255),
    subject TEXT,
    from_email VARCHAR(255),
    to_emails TEXT,
    content TEXT,
    date TIMESTAMP,
    is_sent BOOLEAN DEFAULT FALSE,
    is_received BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create oracle_emails indexes
CREATE INDEX IF NOT EXISTS idx_oracle_emails_user ON oracle_emails(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_emails_date ON oracle_emails(date);
CREATE INDEX IF NOT EXISTS idx_oracle_emails_message ON oracle_emails(message_id); 