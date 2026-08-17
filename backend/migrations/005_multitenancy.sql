-- 005_multitenancy.sql
-- T12 - Multi-tenancy Isolation & Index Tuning
--
-- Make tenant-scoped primary keys begin with company_id and enforce
-- that tasks can only reference campaigns belonging to the same company.

-- 1. memories: Make the PK tenant-prefixed
ALTER TABLE memories
ALTER PRIMARY KEY USING COLUMNS (company_id, id);

-- 2. tasks: Drop existing campaign FKs before altering
-- the campaigns primary key.
ALTER TABLE tasks
DROP CONSTRAINT IF EXISTS fk_campaign_id_ref_campaigns;

ALTER TABLE tasks
DROP CONSTRAINT IF EXISTS tasks_campaign_id_fkey;

ALTER TABLE tasks
DROP CONSTRAINT IF EXISTS fk_tasks_campaign;

ALTER TABLE tasks
DROP CONSTRAINT IF EXISTS fk_tasks_campaign_legacy;

ALTER TABLE tasks
DROP CONSTRAINT IF EXISTS fk_tasks_campaign_tenant;

-- 3. campaigns: Make the PK tenant-prefixed
ALTER TABLE campaigns
ALTER PRIMARY KEY USING COLUMNS (company_id, id);

-- 4. tasks: Make the PK tenant-prefixed
ALTER TABLE tasks
ALTER PRIMARY KEY USING COLUMNS (company_id, id);

-- 5. Restore the original campaign deletion behavior.
-- Deleting a campaign sets campaign_id to NULL rather than
-- deleting the task.
ALTER TABLE tasks
ADD CONSTRAINT fk_tasks_campaign_legacy FOREIGN KEY (campaign_id)
REFERENCES campaigns (id) ON DELETE SET NULL;

-- 6. Enforce tenant isolation.
-- A non-NULL campaign_id must belong to the same company
-- as the task.
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_campaign_tenant
FOREIGN KEY (company_id, campaign_id) REFERENCES campaigns (company_id, id);