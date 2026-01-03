-- Agent Navigator User Schema
-- Schema: agent_navigator
-- Database: Supabase PostgreSQL (supabase-db:5432)

-- Create schema with idempotent check
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'agent_navigator') THEN
        CREATE SCHEMA agent_navigator;
    END IF;
END
$$;

-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Favorites table
CREATE TABLE IF NOT EXISTS agent_navigator.favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, agent_id)
);

-- Index for fast lookups by user
CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON agent_navigator.favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_agent_id ON agent_navigator.favorites(agent_id);

-- View history table
CREATE TABLE IF NOT EXISTS agent_navigator.view_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    viewed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, agent_id)
);

-- Index for recent views query
CREATE INDEX IF NOT EXISTS idx_view_history_user_id ON agent_navigator.view_history(user_id, viewed_at DESC);

-- Auto-update function for view history
CREATE OR REPLACE FUNCTION agent_navigator.update_viewed_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.viewed_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update viewed_at on conflict
DROP TRIGGER IF EXISTS update_view_history_viewed_at ON agent_navigator.view_history;
CREATE TRIGGER update_view_history_viewed_at
    BEFORE UPDATE ON agent_navigator.view_history
    FOR EACH ROW
    EXECUTE FUNCTION agent_navigator.update_viewed_at();

-- Permissions (Supabase style)
GRANT USAGE ON SCHEMA agent_navigator TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA agent_navigator TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA agent_navigator TO postgres, anon, authenticated, service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA agent_navigator TO postgres, anon, authenticated, service_role;

-- Helper function: get favorites with agent details
CREATE OR REPLACE FUNCTION agent_navigator.get_user_favorites(p_user_id VARCHAR)
RETURNS TABLE (
    id UUID,
    user_id VARCHAR,
    agent_id VARCHAR,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT f.id, f.user_id, f.agent_id, f.created_at
    FROM agent_navigator.favorites f
    WHERE f.user_id = p_user_id
    ORDER BY f.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Helper function: get view history
CREATE OR REPLACE FUNCTION agent_navigator.get_user_history(p_user_id VARCHAR, p_limit INT DEFAULT 20)
RETURNS TABLE (
    id UUID,
    user_id VARCHAR,
    agent_id VARCHAR,
    viewed_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT h.id, h.user_id, h.agent_id, h.viewed_at
    FROM agent_navigator.view_history h
    WHERE h.user_id = p_user_id
    ORDER BY h.viewed_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Helper function: toggle favorite (returns 'added', 'removed', or existing status)
CREATE OR REPLACE FUNCTION agent_navigator.toggle_favorite(p_user_id VARCHAR, p_agent_id VARCHAR)
RETURNS TABLE (action VARCHAR, agent_id VARCHAR, created_at TIMESTAMPTZ) AS $$
DECLARE
    _existing RECORD;
BEGIN
    -- Check if exists
    SELECT * INTO _existing
    FROM agent_navigator.favorites
    WHERE user_id = p_user_id AND agent_id = p_agent_id
    FOR UPDATE;

    IF FOUND THEN
        -- Remove existing
        DELETE FROM agent_navigator.favorites
        WHERE user_id = p_user_id AND agent_id = p_agent_id;
        RETURN QUERY SELECT 'removed'::VARCHAR, p_agent_id, _existing.created_at;
    ELSE
        -- Add new
        INSERT INTO agent_navigator.favorites (user_id, agent_id)
        VALUES (p_user_id, p_agent_id)
        RETURNING 'added'::VARCHAR, agent_id, created_at;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Helper function: record view (upsert)
CREATE OR REPLACE FUNCTION agent_navigator.record_view(p_user_id VARCHAR, p_agent_id VARCHAR)
RETURNS TABLE (viewed_at TIMESTAMPTZ) AS $$
BEGIN
    INSERT INTO agent_navigator.view_history (user_id, agent_id)
    VALUES (p_user_id, p_agent_id)
    ON CONFLICT (user_id, agent_id) DO UPDATE
    SET viewed_at = NOW()
    RETURNING viewed_at;
END;
$$ LANGUAGE plpgsql;
