-- 003_harden_auth.sql — store only one-way session token hashes.
--
-- The legacy UUID primary key remains temporarily so this migration is safe
-- to apply without rebuilding the shared sessions table. New application code
-- never exposes that generated UUID and authenticates only by token_hash.

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS token_hash STRING;

CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_token_hash
    ON sessions (token_hash)
    WHERE token_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
    ON sessions (expires_at);
