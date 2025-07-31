-- Create agent_ideas table
CREATE TABLE IF NOT EXISTS agent_ideas (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    summary TEXT NOT NULL,
    steps JSON NOT NULL,
    agent_stack JSON NOT NULL,
    client_requirements JSON NOT NULL,
    conversation_history JSON,
    status VARCHAR DEFAULT 'draft',
    agent_type VARCHAR,
    implementation_estimate JSON,
    security_considerations JSON,
    future_enhancements JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    user_id VARCHAR REFERENCES users(id)
);

-- Create indexes
CREATE INDEX idx_agent_ideas_created_at ON agent_ideas(created_at DESC);
CREATE INDEX idx_agent_ideas_user_id ON agent_ideas(user_id);
CREATE INDEX idx_agent_ideas_status ON agent_ideas(status);
CREATE INDEX idx_agent_ideas_agent_type ON agent_ideas(agent_type);

-- Create updated_at trigger (PostgreSQL)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agent_ideas_updated_at BEFORE UPDATE
    ON agent_ideas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 