# Engineering decisions
1. Use UCI instead of M5: direct unauthenticated download and explicit CC BY 4.0 attribution.
2. Select frequent products using only pre-March history: manageable sample without holdout-based selection.
3. End on November 30: December 2011 source ends on day 9, unsuitable as a complete month.
4. Keep returns/cancellations separate: model positive sales, not net returns.
5. Reject exact duplicates using lowest row ID: conservative explicit assumption, reversible through raw retention.
6. Missing customer IDs allowed: unrelated to product-day analytics. No imputation of transaction prices.
7. Zero-fill missing sales: necessary regular forecast grid, with censoring limitation prominently documented.
8. Ridge with fixed alpha and training-only scaling: explainable and reproducible, no holdout tuning.
9. Prespecify seasonal-naive for planning: keep holdout model comparison separate from model-selection claims.
10. Per-product synthetic capacity: simple scenario exercise, no unsupported optimization/savings claim.
11. Parquet + DuckDB: portable storage and independent SQL arithmetic, without extra servers.
12. Excel artifact builder + Desktop refresh: real editable workbook; native engine refresh remains a manual verification step.
