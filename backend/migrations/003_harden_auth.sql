-- 003_harden_auth.sql — store only one-way session token hashes.
--
-- Legacy sessions used the UUID `token` column directly.
-- New application code stores only SHA-256 hashes in `token_hash`.
--
-- Existing legacy sessions cannot be converted because the original
-- opaque token is not recoverable. They are therefore invalidated during
-- this migration and users must sign in again.

ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS token_hash STRING;

-- Remove legacy sessions that have no hash.
DELETE FROM sessions WHERE token_hash IS NULL;

-- All remaining sessions must use the hardened token representation.
ALTER TABLE sessions
    ALTER COLUMN token_hash SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_token_hash
    ON sessions (token_hash);

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
    ON sessions (expires_at);