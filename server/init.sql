-- Initialize askto_memory database schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table: Core user identity
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number_hash VARCHAR(64) UNIQUE NOT NULL,
    phone_last_four VARCHAR(4),
    name VARCHAR(255),
    location VARCHAR(255),
    work_status VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profiles table: Extracted behavioral data
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    spending_patterns JSONB DEFAULT '{}',
    food_habits JSONB DEFAULT '{}',
    financial_goals JSONB DEFAULT '{}',
    current_cards JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    pain_points JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Sessions table: Track conversation sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_type VARCHAR(50) NOT NULL CHECK (session_type IN ('discovery', 'pitch', 'objection')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    summary TEXT,
    token_count INTEGER DEFAULT 0,
    outcome VARCHAR(50)
);

-- Conversation turns table: Full conversation history
CREATE TABLE conversation_turns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    turn_index INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    extracted_entities JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Computed insights table: Pre-computed sales-relevant insights
CREATE TABLE computed_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    insight_type VARCHAR(100) NOT NULL,
    insight_key VARCHAR(100) NOT NULL,
    insight_value TEXT NOT NULL,
    numeric_value DECIMAL,
    confidence DECIMAL DEFAULT 1.0,
    derived_from_session_id UUID REFERENCES sessions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, insight_type, insight_key)
);

-- Indexes for performance
CREATE INDEX idx_users_phone_hash ON users(phone_number_hash);
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_type ON sessions(session_type);
CREATE INDEX idx_conversation_turns_session_id ON conversation_turns(session_id);
CREATE INDEX idx_computed_insights_user_id ON computed_insights(user_id);
CREATE INDEX idx_computed_insights_type ON computed_insights(insight_type);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_computed_insights_updated_at
    BEFORE UPDATE ON computed_insights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
