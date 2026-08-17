-- 004_multitenancy.sql
-- T12 - Multi-tenancy Isolation & Index Tuning
--
-- This migration updates the primary keys of the tenant-scoped tables
-- to start with `company_id`. This creates "hash-sharded" style
-- tenant isolation, ensuring all data for a specific company is stored
-- together on the same physical nodes, eliminating full-cluster scatter-gather queries.

-- 1. memories: Make the PK tenant-prefixed
ALTER TABLE memories ALTER PRIMARY KEY USING COLUMNS (company_id, id);

-- 2. tasks: Drop the existing foreign key to campaigns before we can alter campaigns PK
-- CockroachDB auto-generates names for inline foreign keys.
-- We try the two most common auto-generated names.
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS fk_campaign_id_ref_campaigns;
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_campaign_id_fkey;

-- 3. campaigns: Make the PK tenant-prefixed
ALTER TABLE campaigns ALTER PRIMARY KEY USING COLUMNS (company_id, id);

-- 4. tasks: Make the PK tenant-prefixed
ALTER TABLE tasks ALTER PRIMARY KEY USING COLUMNS (company_id, id);

-- 5. tasks: Re-add the foreign key to campaigns, now using both company_id and campaign_id
-- This inherently enforces that a task must belong to the same company as its campaign.
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_campaign
FOREIGN KEY (company_id, campaign_id) REFERENCES campaigns (company_id, id) ON DELETE CASCADE;
