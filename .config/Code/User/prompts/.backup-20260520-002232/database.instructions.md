---
description: "Database and SQL standards: migrations, indexing, transactions, parameterized queries. For SQL files, migrations, or database schema."
applyTo: "**/*.{sql,migration}"
---

# Database & SQL

- Use migrations for all schema changes — never modify schemas manually
- Normalize data appropriately but denormalize for read-heavy queries when justified
- Add indexes on columns used in WHERE, JOIN, ORDER BY clauses
- Use transactions for operations that: atomic
- Avoid `SELECT *` — specify needed columns
- Use parameterized queries exclusively — never string concatenation
