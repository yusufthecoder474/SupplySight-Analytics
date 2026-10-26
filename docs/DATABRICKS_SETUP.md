# Databricks Free Edition verification — PENDING

Local five-notebook execution passed on Spark 3.5.3. Databricks access was not available. Source-format import and serverless execution are prepared, not runtime certified.

## Workspace and data setup
1. Sign into your authorized Free Edition workspace. Select serverless Python compute. Use your available catalog and schema; examples below use workspace.default, which you must replace if absent.
2. Create a NEW workspace folder /Workspace/Users/<your-user>/SupplySight-Enhanced. Upload src/supplysight as workspace files, keeping the package directories and __init__.py. Import the five notebooks/*.py using Workspace → Import → File → Python. Keep them in a notebooks folder. If folder upload is unavailable, use the authenticated Databricks CLI from Windows: `databricks workspace import-dir . /Users/<your-user>/SupplySight-Enhanced` into that new folder. Do not overwrite unrelated workspace files. The Python filesystem path for it starts /Workspace/Users/.
3. In a SQL cell run `CREATE VOLUME IF NOT EXISTS workspace.default.supplysight;`. Use Catalog Explorer → volume → Upload to upload data/raw/retail_subset.csv to a new dedicated directory, e.g. /Volumes/workspace/default/supplysight/danfoss-run-01/data/raw/retail_subset.csv. The source has 26,058 rows excluding its header. Keep each evidence run in a new directory.
4. In the notebook Environment side panel install the NON-SPARK dependencies from requirements-databricks.txt. Retain managed PySpark; do not install local requirements.txt over the managed runtime. Resolve any runtime dependency conflict in the panel and record chosen versions.
5. Set project_root on EACH notebook to /Workspace/Users/<your-user>/SupplySight-Enhanced and data_root to /Volumes/workspace/default/supplysight/danfoss-run-01. Leave the data files out of /Workspace for Spark I/O.
6. In a setup Python cell create the output folders before notebook 04:
```python
from pathlib import Path
r = Path('/Volumes/workspace/default/supplysight/danfoss-run-01')
for d in ['reports','data/synthetic','docs/screenshots']:
    (r/d).mkdir(parents=True, exist_ok=True)
```

## Execution and checks
Run 01_bronze_ingestion → 02_silver_validation → 03_gold_supply_chain_kpis → 04_demand_forecasting → 05_data_quality_reconciliation. Managed spark is reused; no SparkContext or local session builder is called in this branch. Volume writes use Spark overwrite rather than local part-file renames.

Expected checks: Bronze 26,058; Silver 24,258; rejected 1,800; accepted and daily Gold units 350,997; 20 products ×365 days =7,300 daily rows; four Spark Gold tables plus four forecast/planning datasets = eight Gold datasets; 14 KPI rows all passed. Notebook 05 asserts the counts. Check the exact parquet folder totals with `spark.read.parquet(str(r/'data/processed/bronze')).count()` and equivalent silver/rejected reads. Never sum files across different run directories.

Download reports/evaluation.json, reports/kpi_reconciliation.csv, reports/data_quality.csv, reports/rejected_records.csv and reports/notebook_runtime.jsonl. Save real notebook output screenshots and the environment/version panel. Runtime JSONL records client-side Spark/package versions and notebook completion timestamps; query profiling and execution duration should be captured from Databricks. Failed notebooks do not log successful completion.

Then run the extension in a Python cell, reusing the code path added by 01:
```python
from supplysight.study import run as study
from supplysight.capacity import run as planning
study(r)
planning(r)
```
Reconcile pooled scores to the included local study; explain version-dependent differences. Do not set the Databricks status to PASS until all five notebooks succeed in the actual workspace. No Databricks screenshot has been supplied.

## Compatibility review
Free Edition is serverless only. Use absolute workspace imports and Unity Catalog Volume data paths. The code uses DataFrame/SQL APIs, session temp views, bounded toPandas operations and client Python libraries, without RDDs, global temp views or DBFS mounts. ANSI handling follows the original validation contract by setting spark.sql.ansi.enabled=false; verify that the selected environment permits this setting. The full CLI is the local runner, not the Databricks entry point. Volume overwrite assumes one writer and a dedicated output path. Source-format imports are supported, but Databricks warns serverless metadata may not be retained in source-format notebooks: after importing, save them in the workspace's native notebook format.

Official references checked 26 Oct 2026:
- https://docs.databricks.com/aws/en/getting-started/free-edition-limitations
- https://docs.databricks.com/aws/en/compute/serverless/limitations
- https://docs.databricks.com/aws/en/compute/serverless/dependencies

## Capacity-constrained extension
Notebook 04 now calls supplysight.constrained_planning.run(root) after writing the existing Gold outputs. Notebook 05 also validates that production is at most horizon capacity, stock stays nonnegative and requested = planned + deferred. Download reports/constrained_planning with the other evidence. Defaults are the synthetic scenario and a seven-day horizon; overrides are documented in CAPACITY_CONSTRAINED_PLANNING.md. The five notebooks were executed locally after this extension; Databricks runtime is still PENDING.
