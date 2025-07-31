-- RAG (Retrieval-Augmented Generation) Tables Migration
-- Add tables for Generic RAG Platform integration into nBrain

-- Data Sources table
CREATE TABLE IF NOT EXISTS rag_data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data Entries table
CREATE TABLE IF NOT EXISTS rag_data_entries (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES rag_data_sources(id) ON DELETE CASCADE,
    entity_id VARCHAR(200) NOT NULL,
    timestamp TIMESTAMP,
    data JSONB,
    entry_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_rag_data_entries_source_id ON rag_data_entries(source_id);
CREATE INDEX IF NOT EXISTS idx_rag_data_entries_entity_id ON rag_data_entries(entity_id);
CREATE INDEX IF NOT EXISTS idx_rag_data_entries_timestamp ON rag_data_entries(timestamp);
CREATE INDEX IF NOT EXISTS idx_rag_data_entries_data ON rag_data_entries USING GIN(data);

-- RAG Chat History table
CREATE TABLE IF NOT EXISTS rag_chat_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    session_id VARCHAR(100) NOT NULL,
    query TEXT NOT NULL,
    response TEXT,
    context_data JSONB,
    data_sources_used JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for chat history
CREATE INDEX IF NOT EXISTS idx_rag_chat_history_user_id ON rag_chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_chat_history_session_id ON rag_chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_rag_chat_history_created_at ON rag_chat_history(created_at);

-- RAG Configuration table
CREATE TABLE IF NOT EXISTS rag_configurations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    config_type VARCHAR(50) NOT NULL,
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for configurations
CREATE INDEX IF NOT EXISTS idx_rag_configurations_user_id ON rag_configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_configurations_config_type ON rag_configurations(config_type);
CREATE INDEX IF NOT EXISTS idx_rag_configurations_is_active ON rag_configurations(is_active);

-- Add update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_rag_data_sources_updated_at BEFORE UPDATE ON rag_data_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rag_configurations_updated_at BEFORE UPDATE ON rag_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 