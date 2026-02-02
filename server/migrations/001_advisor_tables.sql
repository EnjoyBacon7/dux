-- Advisor chat: conversations and messages
-- Tables are also created automatically by init_db() (Base.metadata.create_all).
-- Run this manually only if you need to apply the schema without starting the app.

CREATE TABLE IF NOT EXISTS advisor_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_advisor_conversations_user_id ON advisor_conversations(user_id);

CREATE TABLE IF NOT EXISTS advisor_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES advisor_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_advisor_messages_conversation_id ON advisor_messages(conversation_id);

-- Grant permissions to the application user (run as a superuser, e.g. postgres).
-- Replace dux_user with the username from your DATABASE_URL if different.
GRANT ALL PRIVILEGES ON TABLE advisor_conversations TO dux_user;
GRANT ALL PRIVILEGES ON TABLE advisor_messages TO dux_user;
GRANT USAGE, SELECT ON SEQUENCE advisor_conversations_id_seq TO dux_user;
GRANT USAGE, SELECT ON SEQUENCE advisor_messages_id_seq TO dux_user;
