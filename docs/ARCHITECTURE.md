# Architecture
The source preparation step reads official XLSX once and adds source_row_id.
Spark Bronze preserves raw strings and provenance. Silver applies eight reason
families without editing the source. Every source row enters exactly one partition.
Gold uses Spark SQL for weekly aggregation and a complete date-product grid.
Business functions compute rolling forecasts and scenario inventory in pandas.
DuckDB recomputes 14 aggregates independently from Gold reporting frames. It does
not merely compare two copied KPI columns. Spark separately checks Silver units.
CSV feeds Excel/Power BI, Parquet preserves typed local analytics.

Module ownership: ingestion.py contracts and hashing; validation.py rejects;
transformations.py Spark Gold; forecasting.py leakage-safe features and models;
metrics.py error math; inventory.py scenario formulas; reporting.py exports,
SQL reconciliation and measured charts; cli.py orchestration/error report.
Re-running stages Spark writes into unique sibling paths, then replaces each dataset
through Python filesystem operations. This avoids stale Hadoop part listings observed
in this host. Source and stable IDs stay intact. A regression checks replacement. Ingestion
timestamps and Parquet byte layout need not remain identical. This is batch ETL,
not a transactional incremental platform. No Delta or PostgreSQL is needed.
