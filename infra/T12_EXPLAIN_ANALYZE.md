# T12 EXPLAIN ANALYZE Writeup: Multi-tenancy Index Tuning

This document describes the impact of prefixing the primary keys for `memories`, `campaigns`, and `tasks` with `company_id`.

## The Problem: Tenant-Scoped Queries

Before the index tuning, the core tables used a generic UUID as the leading column in the primary key:

```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    -- ...
);
```

A typical tenant-scoped query is:

```sql
SELECT id, content
FROM memories
WHERE company_id = '3f2b8c41-6e57-4a92-9d13-7c5e8b24a601';
```

With `id` as the leading primary-key column, the primary key is not ordered by `company_id`, so this query cannot use the primary-key ordering to target a narrow tenant-specific key range.

## The Solution: Tenant-Prefixed Primary Keys

We changed the primary keys to begin with `company_id`:

```sql
ALTER TABLE memories
ALTER PRIMARY KEY USING COLUMNS (company_id, id);
```

This places each company's records into tenant-prefixed key ranges. Tenant-scoped queries can therefore use the primary-key ordering to target the relevant key spans instead of scanning unrelated tenant keys.

### EXPLAIN ANALYZE

The following is an **illustrative expected execution-plan shape**, not a measured benchmark result:

```text
scan
  ...
  table: memories@memories_pkey
  spans: [/'3f2b8c41-6e57-4a92-9d13-7c5e8b24a601' - /'3f2b8c41-6e57-4a92-9d13-7c5e8b24a601']
```

The exact planning time, execution time, distribution, and span details depend on the actual cluster state, data volume, and CockroachDB configuration. Actual `EXPLAIN ANALYZE` output should be captured separately when benchmarking the deployed cluster.

**Key Takeaways:**

1. **Tenant-Targeted Spans:** Prefixing the primary key with `company_id` allows tenant-scoped queries to target narrower key ranges.
2. **Reduced Unrelated Scanning:** Queries can use the tenant prefix to avoid scanning primary-key ranges belonging to unrelated companies.
3. **Scalable Key Layout:** The tenant-prefixed key layout provides a stronger foundation for multi-tenant query performance as the dataset grows.

This multi-tenancy design provides a solid database foundation for the GrowthPilot hackathon project.
