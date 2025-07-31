-- Create oracle_emails table if it doesn't exist
CREATE TABLE IF NOT EXISTS oracle_emails (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    message_id VARCHAR UNIQUE,
    thread_id VARCHAR,
    subject TEXT,
    from_email TEXT,
    to_emails TEXT,
    content TEXT,
    date TIMESTAMP WITH TIME ZONE,
    is_sent BOOLEAN DEFAULT FALSE,
    is_received BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_oracle_emails_user_id ON oracle_emails(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_emails_thread_id ON oracle_emails(thread_id);
CREATE INDEX IF NOT EXISTS idx_oracle_emails_date ON oracle_emails(date DESC); 