> Historical verification retained. Current enhancement results: reports/enhancement/VERIFICATION.md (61 SupplySight tests; 96 CustomsDesk tests plus 2 PostgreSQL skips).

# Verification evidence — 2026-10-25

## Final verified result
- Linux x86_64, Python 3.12.14, Java OpenJDK 17.0.20, Spark 3.5.3.
- 46 passed, 0 failed, 0 errors, 0 skipped. See pytest.xml / pytest.log.
- Ruff check and format check passed. No GitHub Actions run was requested or executed.
- Actual Spark input: 26,058 subset rows; accepted 24,258; rejected 1,800.
- Bronze/Silver/Gold checked against exported CSV and Parquet: product master 20,
  daily demand 7,300, weekly demand 1,060, calendar 365 rows.
- Accepted demand 350,997 units. Eight Gold datasets, eight quality-rule families,
  14 independent arithmetic KPI reconciliations, four SQL diagnostics with zero violations.
- Twenty products, 365 history days; three nonoverlapping 14-day backtests.
  There are 840 evaluated product-days per model and 2,520 model prediction rows.
- WAPE: naive 92.532852%; seasonal-naive 99.060447%; Ridge 76.642939%.
  Ridge relative reduction vs seasonal: 22.630130%; improves 18/20 products.
  Ridge pooled bias −31.549985%. Accuracy remains inadequate for autonomous ordering.
- Synthetic scenario only: eight products below reorder point, four above 60 days cover.
- Excel: seven sheets, 5,222 formulas, 20 XLOOKUPs,
  6 tables and 1 native chart.
  Artifact Tool recalculation, stock-input mutation, error scan, cached metric
  reconciliation and saved-file structure inspection passed. All seven sheets were
  rendered and visually reviewed; images are Artifact Tool previews, not Excel screenshots.
- Five Databricks source notebooks ran locally in order. Their local console output
  is notebooks_local.log. This does not verify Databricks execution.

## Executed commands and evidence
Commands below use the conversation virtual environment. For Windows equivalents
see docs/WINDOWS_SETUP.md. Invocation paths differ because the project is nested here.

| Command/action | Result | Evidence |
|---|---|---|
| `java -version`, Python module inspection | Java present; Spark initially missing | environment check |
| Python urllib download of UCI archive | HTTP 200, downloaded and parsed | data/provenance.json includes hash |
| `uv pip install --python /usr/local/bin/python ...` | failed: no interpreter at specified path | corrected with uv venv |
| `uv venv .venv --system-site-packages` and dependency install | passed | install.log records final editable install |
| `python scripts/prepare_source.py --archive /tmp/online-retail.zip` | passed; 541,909 original rows inspected, 26,058 selected | data/provenance.json |
| `uv pip install --python .venv/bin/python -e 'SupplySight-Analytics[dev]'` | passed | install.log |
| `python -m supplysight.cli` / installed `supplysight` | passed after fixes; final run regenerates all datasets | pipeline_final.log, evaluation.json |
| `python -u scripts/verify_notebooks.py` | five notebooks passed locally after output replacement fixes | notebooks_local.log |
| Artifact runtime Node `build_workbook.mjs PROJECT_ROOT` | passed, recalculated, rendered, exported | workbook_build.log, excel/, docs/screenshots/ |
| `python -m pytest tests -q --junitxml=reports/pytest.xml` | 46 passed, 0 skipped | pytest.xml, pytest.log |
| `ruff check src scripts tests notebooks` | passed | lint.log |
| `ruff format --check src scripts tests notebooks` | passed | format_check.log |
| DuckDB execute gold_kpis.sql + data_validation.sql | passed; four zero-violation diagnostics | sql_execution.txt |
| `python scripts/write_docs.py` | generated documentation from real evaluation | README and docs |
| `node --check scripts/build_workbook.mjs` | passed | JS syntax checked before authoring |
| Python ZIP creation + testzip | passed | archive integrity checked at packaging |

## Failures and corrective actions retained
1. Initial Spark startup could not bind the default hostname. Local IP and bind
   address were set to loopback. See initial_spark_bind_failure.log.
2. Initial lint found unused imports, formatting issues, a min selection issue and
   Databricks-injected globals. Imports/style were fixed and globals resolved explicitly.
3. Core tests passed (43) initially. One first full-suite workbook test read empty
   styled rows beyond the populated checks; its range was bounded to actual controls.
   See pytest_initial_full.log.
4. Notebook reruns exposed stale Spark part files and doubled totals. Reconciliation
   failed rather than accepting them: product count 40 vs 20 and weekly sum 1,403,988
   vs daily 701,994. A direct directory-recreate attempt also hit PATH_ALREADY_EXISTS.
   See notebooks_output_path_failure.log and pytest_stale_files_failure.log.
5. Final writes use a fresh Spark staging location and a single stable data.parquet
   file. Existing children are removed explicitly, then the completed part is moved
   into place. The regression test seeds a legacy part before replacement.
   This bounded sample deliberately uses one output partition; no scale claim is made.
6. The host's virtual filesystem retained legacy parts across earlier JVM shutdowns.
   They were explicitly removed after shutdown before final release tests. Final
   folder reads, CSVs and the packaged files agree. No source rows were changed.
7. A reporting command initially used the parent virtualenv path from the project
   directory and failed with interpreter not found. Corrected to ../.venv/bin/python.

## Unexecuted native and external work
Databricks runtime: NOT VERIFIED. Power BI Desktop: unavailable, no PBIX created,
zero completed native report pages, 17 measures authored and zero engine-verified.
Excel Desktop opening, PivotTables, native Power Query refresh and the PowerShell COM
refresh script: NOT VERIFIED. Windows runtime: NOT VERIFIED. Remote GitHub Actions:
configured but NOT RUN. No public repository or deployment was created.

Full original XLSX is not included; the licensed subset and download script are.
No manufacturing stock, supplier lead-time observations or real capacity data exist
in the source. Planning results are explicitly synthetic. No financial savings claimed.
