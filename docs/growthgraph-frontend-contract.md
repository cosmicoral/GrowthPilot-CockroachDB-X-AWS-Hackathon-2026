# GrowthGraph frontend contract (T36)

The dashboard calls `POST /api/growthgraph/insights` with an authenticated,
company-scoped session:

```json
{
  "query": "What challenges are founders facing around product-market fit?"
}
```

The endpoint should run the allowlisted `company_id IN (...)` cross-tenant
query described by T36 and return only anonymized aggregates:

```json
{
  "query": "What challenges are founders facing around product-market fit?",
  "cohort_size": 75,
  "generated_at": "2026-08-17T22:30:00Z",
  "insight": "Product-market-fit uncertainty appears across 24 founders.",
  "insights": [
    {
      "theme": "Unclear ideal customer profile",
      "summary": "Founders frequently connect PMF uncertainty to an ICP that is too broad.",
      "matched_founders": 24,
      "cohort_size": 75,
      "prevalence": 0.32,
      "average_similarity": 0.86
    }
  ]
}
```

Privacy boundary: do not return company IDs, memory IDs, founder names, raw
memory content, or per-company rows. The frontend intentionally has no fields
that render those values.
