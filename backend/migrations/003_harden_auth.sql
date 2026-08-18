-- 003_harden_auth.sql — store only one-way session token hashes.
--
-- The legacy UUID primary key remains temporarily so this migration is safe
-- to apply without rebuilding the shared sessions table. New application code
-- never exposes that generated UUID and authenticates only by token_hash.

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS token_hash STRING;

-- Legacy rows contain only the old UUID token and cannot be authenticated by
-- the hardened application. Delete them explicitly so deployment has one
-- predictable transition: existing users sign in again, and every remaining
-- session uses a one-way token hash.
DELETE FROM sessions WHERE token_hash IS NULL;

ALTER TABLE sessions ALTER COLUMN token_hash SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_token_hash
    ON sessions (token_hash);

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
    ON sessions (expires_at);
