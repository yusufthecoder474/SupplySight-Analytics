# Testing and evidence
Run `python -m pytest -q` after the pipeline. The included workbook allows report
checks without proprietary authoring dependencies. Tests read its cached results
and formula structures, not an actual Excel Desktop engine.

See ../reports/verification.md for commands, final counts, failures and limitations.
pytest.xml is the machine-readable source of final test counts. release_metrics.json
records actual formula/table/chart counts. The CI workflow runs this same suite.

Coverage includes schema versions, missing files/fields, empty input, malformed
types, cancellations, negative quantities, invalid dates/IDs/prices, duplicates,
date-grid aggregation, referential integrity, deterministic transformations,
legacy-file replacement, hand-calculated inventory math, zero/missing inputs,
forecast metric math, horizon alignment and holdout-mutation leakage checks.
Release checks compare CSV/Parquet structures, KPI SQL controls and cached workbook
totals/errors. Native DAX, Databricks and Excel automation remain manual checks.
