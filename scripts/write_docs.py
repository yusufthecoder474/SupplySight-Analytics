"""Generate factual documentation from evaluation output; never invent execution metrics."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(name, text):
    (ROOT / name).write_text(text.strip() + "\n", encoding="utf-8")


def main():
    s = json.loads((ROOT / "reports/evaluation.json").read_text())
    scores = {r["model"]: r for r in s["model_comparison"]}
    naive, seasonal, ridge = [scores[m]["wape"] * 100 for m in ["naive", "seasonal_naive", "ridge"]]
    write(
        "README.md",
        f"""
<p align="center"><img src="docs/banner.svg" alt="SupplySight Analytics" width="100%"></p>

# SupplySight Analytics
**Manufacturing inventory intelligence and demand forecasting**

![Python](https://img.shields.io/badge/Python-3.12-17324D)
![Spark](https://img.shields.io/badge/PySpark-3.5.3-E25A1C)
![Local execution](https://img.shields.io/badge/Local_pipeline-executed-0D9488)
![Databricks](https://img.shields.io/badge/Databricks-not_executed-64748B)
![Power BI](https://img.shields.io/badge/Power_BI-build_kit_only-64748B)

An independent final-year analytics engineering project aligned with a supply-chain
internship. **No affiliation with, deployment at, or real stakeholder engagement with Danfoss.**
Public retail sales demonstrate the engineering patterns. All stock, lead-time and
capacity inputs are separately labeled synthetic scenarios.

## What it answers
Which products need replenishment review? Which have excess stock under a scenario?
How much does a simple statistical model improve on baselines? Do source totals,
Gold datasets, SQL controls and workbook formulas agree?

## Executed results
| Evidence | Measured result |
|---|---:|
| Raw subset rows ingested by Spark | {s["raw_records"]:,} |
| Accepted / rejected | {s["accepted_records"]:,} / {s["rejected_records"]:,} |
| Accepted units, reconciled to Gold | {s["gold_units"]:,.0f} |
| Products / daily history | {s["products"]} / {s["history_days"]} days |
| Gold datasets / quality rules / KPI reconciliations | {s["gold_datasets"]} / {s["quality_rules"]} / {s["reconciled_kpis"]} |
| Rolling origins / equal horizon | 3 / 14 days |
| Synthetic at-risk / overstock products | {s["at_risk_products_synthetic"]} / {s["overstock_products_synthetic"]} |

Test and workbook verification: [verification report](reports/verification.md).
Machine-readable numbers: [evaluation.json](reports/evaluation.json).

## Architecture
```mermaid
flowchart TD
  A[UCI source subset] --> B[Bronze raw strings and metadata]
  B --> C[Silver validated sales]
  B --> Q[Rejected rows with reasons]
  C --> D[Gold daily and weekly sales]
  D --> E[Rolling forecast evaluation]
  D --> F[Synthetic planning scenario]
  E --> G[SQL reconciliation and reporting]
  F --> G
```
PySpark performs ingestion, validation, date-grid expansion and Gold aggregation.
Pandas/scikit-learn handle bounded per-product forecasting, DuckDB independently
reconciles metrics, and Parquet/CSV connect the layers. This dataset does not need
Spark for speed; Spark is chosen to demonstrate transferable ETL engineering.
No speedup or production-scale claim is made.

## Data and license
Chen, D. (2015), [Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail),
UCI, DOI 10.24432/C5BW33, **CC BY 4.0**. [Provenance](data/provenance.json)
records the download URL, source and subset SHA-256 hashes, fields and row counts.
The original workbook contained 541,909 rows. The actual Spark run ingested only
the included 26,058-row subset, not the entire original workbook.
M5 was not used to avoid a competition-account/download dependency.

Twenty products are selected using transaction frequency **before 2011-03-01**.
All their rows are retained in raw, including cancellations and out-of-window dates.
The complete analysis window is 2010-12-01 through 2011-11-30.
Sales are an imperfect proxy for demand: absent transactions are assumed zero,
which may hide stockouts or closures. No observed manufacturing data is claimed.

## Forecasting
| Model | Pooled WAPE | Role |
|---|---:|---|
| Last-value naive | {naive:.2f}% | Baseline |
| Seasonal-naive, lag 7 | {seasonal:.2f}% | Prespecified planning baseline |
| Standardized Ridge, alpha 10 | {ridge:.2f}% | Explainable challenger |

Three expanding training windows precede nonoverlapping 14-day targets. Each
product contributes 42 evaluated days per model. Ridge uses lag 1/7/14, trailing
7/28-day means and day-of-week sin/cos. Future lag features use recursive
predictions only. Scaling is fitted inside each training window. No random splits.

Ridge reduced pooled WAPE by {s["ridge_improvement_vs_seasonal_wape"] * 100:.2f}% relative
to seasonal-naive and improved absolute error for {s["ridge_products_improved_pct"]:.0f}%
of products. Its bias was {scores["ridge"]["bias"] * 100:.2f}%, meaning substantial
underforecasting. Absolute errors remain high. Do not treat this as production-ready
forecasting. No model was tuned on these holdouts. Planning uses seasonal-naive
chosen in advance rather than selecting a winner from the reported test results.

![Measured model errors](docs/screenshots/forecast_comparison.png)
![Measured forecast trend](docs/screenshots/actual_vs_forecast.png)

WAPE pools absolute error over actual units; it is not the average of product WAPEs.
Zero-total actuals yield undefined WAPE/bias, stored as null. MAPE excludes zero
actuals and is diagnostic only because intermittent sales make it unstable.
Forecast value added is 1 − challenger WAPE / baseline WAPE, on identical rows.

## Inventory and capacity
Seed 52316 creates stock = rounded recent mean × Uniform(2,85) days, lead time =
integer 5–21 days, weekly capacity = max(1, rounded mean × 7 × Uniform(.65,1.5)).
Safety stock = 1.65 × 28-day population std × sqrt(lead days).
Reorder point = forecast daily mean × lead days + safety stock.
Risk means stock < reorder point; overstock means cover >60 days.
The normal independent-demand approximation is illustrative, not calibrated
service-level assurance. On-order stock and receipts are unavailable and excluded.
Capacity is a per-product hypothetical unit limit, not a shared factory bottleneck.
No financial inventory turnover, savings or stockout outcomes are asserted.

![Synthetic planning scenario](docs/screenshots/inventory_scenario.png)

## Reporting deliverables
- [Excel workbook](excel/SupplySight_Operations_Analysis.xlsx): seven sheets,
  editable formulas, tables, XLOOKUP descriptions, conditional formatting and native chart.
  [Usage and refresh](docs/EXCEL_GUIDE.md). Artifact-rendered previews are not Excel screenshots.
- [Power BI build kit](powerbi/README.md): typed Power Query, 17 authored measures,
  relationships, three-page design and acceptance checks. **No PBIX or verified pages.**
- Five [Databricks source notebooks](notebooks/), with local functions and manual
  [import steps](docs/DATABRICKS_SETUP.md). **No Databricks runtime claim.**

![Workbook preview rendered with Artifact Tool](docs/screenshots/workbook_Executive_Summary_0.png)

## Run locally
Prerequisites: Python 3.12, Java 17, approximately 2 GB free memory. No database
server, paid API, cloud credentials or source download needed for the included subset.
```powershell
cd SupplySight-Analytics
py -3.12 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m supplysight.cli
python -m pytest -q
```
See [Windows setup](docs/WINDOWS_SETUP.md) for Java and troubleshooting.
Rebuild the full-data-derived subset, optionally:
```powershell
python scripts/prepare_source.py
```
The downloader reads the official XLSX using openpyxl only as an input reader.
The workbook was authored using `@oai/artifact-tool`; that builder requires the
ChatGPT artifact runtime. Outside it, use the included workbook and Excel Desktop
COM refresh script. Native Excel refresh is provided but unexecuted here.

## Quality assurance and reproducibility
`pytest` covers bad schemas, bad records, duplicates, source/Gold reconciliation,
hand-calculated KPIs, zero demand, threshold boundaries, leakage via holdout mutation,
chronological horizons, deterministic scenarios, output schemas and cached workbook
results. [CI](.github/workflows/ci.yml) runs local Spark, lint and tests with the
included small subset. Remote Actions is configured but unverified.
Ingestion timestamps vary; business row IDs, transformations and planning values
are deterministic. Writes stage each Spark dataset in a fresh directory and replace the dedicated
output after successful completion (single writer only).

## Documentation
| Reader | Guide |
|---|---|
| Business reviewer | [Requirements](docs/BUSINESS_REQUIREMENTS.md), [stakeholder brief](docs/STAKEHOLDER_BRIEF.md) |
| Analyst | [KPIs](docs/KPI_DEFINITIONS.md), [dictionary](docs/DATA_DICTIONARY.md), [Excel](docs/EXCEL_GUIDE.md) |
| Engineer | [Architecture](docs/ARCHITECTURE.md), [testing](docs/TESTING.md), [decision log](docs/DECISIONS.md) |
| Student | [Interview and resume material](docs/RESUME_AND_INTERVIEW.md) |
| Publisher | [Publishing checklist](docs/PUBLISHING.md), [risks](docs/RISK_REGISTER.md) |

## Limitations and next work
Small selected retail sample, one year, three folds, no demand censoring correction,
no real lead-time distribution or inventory history. Duplicate business rows might
represent genuine repeat lines; rejection is an explicit conservative assumption.
Missing customer IDs are allowed because customer attributes are not used.
First/last weeks are partial and carry days_in_week. Product descriptions may change;
the lexicographically first accepted description is display-only, never a feature.
No Delta dependency is introduced. Gold uses Parquet for portability.
Future work: validate on longer histories, add genuine inventory/receipt data,
calibrate safety stock, compare intermittent-demand methods and verify BI natively.
""",
    )
    write(
        "docs/BUSINESS_REQUIREMENTS.md",
        """
# Business requirements
This is a hypothetical planning case. No real stakeholders were interviewed.

| ID | User need | Implemented evidence | Acceptance |
|---|---|---|---|
| BR1 | Trust sales history | Bronze metadata, Silver rejects, Gold totals | raw = accepted + rejected; units match |
| BR2 | Compare demand forecasts fairly | Three models, 3 chronological origins | same 14 targets per model and origin |
| BR3 | Review inventory exceptions | Explicit synthetic stock and capacity | each flag traceable to formula and scenario |
| BR4 | Export understandable analytics | Excel and BI-ready datasets | workbook controls match SQL; BI native review pending |
| BR5 | Trace results | Stable source row IDs, hashes, rule IDs | rejected row reasons and lineage documented |

Hypothetical planner owns replenishment decisions, analyst owns KPI definitions,
engineer owns data contracts. Escalate changing schemas to the data owner; escalate
negative stock or large forecast bias to the planner. High WAPE prevents automated
purchasing approval. Data-quality root causes are described without claiming real
customer dissatisfaction, business savings, or stakeholder satisfaction scores.
""",
    )
    write(
        "docs/KPI_DEFINITIONS.md",
        """
# KPI definitions
Sales mean accepted positive transaction quantities, not unconstrained demand.
All inventory/capacity fields are synthetic and as of 2011-11-30.

| KPI | Formula / grain / time window | Null and aggregation policy | Interpretation |
|---|---|---|---|
| Total demand | sum units; product/day, 365 days | zero-filled dates; additive across products/dates | sales proxy units |
| Demand variability | population std / mean; product, last 28 days | null when mean zero; do not sum CVs | recent relative variability |
| MAE | sum absolute error / target rows; model, 3×14 days/product | finite aligned rows only | units error per product-day |
| WAPE | sum absolute error / sum actual; model, same holdout | null if actual total zero; pool numerators/denominators | volume-weighted error |
| Bias | sum(predicted−actual) / sum actual | null if total zero; pooled by model | negative = underforecast |
| Days cover | on_hand / last-28-day mean; product/snapshot | null if mean zero or missing stock; average only labeled mean | stock duration under recent sales |
| Safety stock | 1.65 × population std daily × sqrt(lead days) | null for missing planning fields | approximate scenario buffer |
| Reorder point | future-14-day mean × lead days + safety stock | null if inputs missing; sum units across products only for overview | proposed review threshold |
| Stock risk | on_hand < reorder point; product/snapshot | null if inputs missing; equality is not risk | scenario review, not observed stockout |
| Overstock | cover >60 days | false for zero demand; inspect zero-demand stock separately | excessive cover under assumed demand |
| Planned utilization | forecast daily ×7 / weekly_capacity | null if missing; zero capacity invalid; aggregate ratio of sums | scenario unit capacity, not factory actuals |
| WoW demand change | latest 7-day units / preceding 7-day units −1 | null when previous 7 days zero; product as-of | recent sales change |
| Forecast value added | 1 − challenger WAPE / baseline WAPE | same rows and horizon; undefined if baseline error zero | relative error reduction, not savings |

No lead-time variation KPI: only one synthetic lead-time assumption per product.
No inventory turnover/value KPI: no valid observed stock history or cost basis.
MAPE is diagnostic on nonzero actual periods only and cannot represent zero-demand performance.
""",
    )
    write(
        "docs/DATA_DICTIONARY.md",
        """
# Data dictionary and lineage
Column-level run types, null presence, grain and lineage:
[data_dictionary.csv](../reports/data_dictionary.csv).

| Table | Grain | Origin | Validation |
|---|---|---|---|
| Bronze | original source row | subset CSV, raw string fields + SHA/file/time/version | exact header contract |
| Silver | accepted source row | Bronze + date, units, product_id, price | 8 rule families; raw partition reconciliation |
| Rejected | rejected source row | Bronze + semicolon-separated reasons | every rejected row kept; reasons may overlap |
| product_master | product | distinct Silver product_id, min description | unique ID, no null description |
| daily_demand | product/calendar day | sum Silver quantities, dense zero-filled calendar | unique key, positive/zero units, matches Silver sum |
| weekly_demand | product/Monday week | daily_demand sum | total equals daily; edge weeks partial |
| date_dimension | calendar day | fixed 365-day reporting window | unique continuous dates |
| forecast_results | product/fold/model/target day | daily sales and training-only features | train_end < target; 14 targets/fold/model |
| future_forecast | product/future day | full history seasonal-naive | 14 days after last observation |
| inventory_risk | product/scenario snapshot | recent daily stats + synthetic inputs + future forecast | positive capacity/lead; formula controls |
| product_forecast_scores | product/model | pooled evaluation targets | 42 targets per product/model |

units/actual/predicted/absolute_error/signed_error/reorder_point/on_hand are product
units. days_cover/lead_days are days. weekly_capacity is units/week.
wape/bias/demand_cv/wow_change/planned_utilization are dimensionless ratios.
fold is 1..3, model identifies the method, train_end is last date visible to model,
as_of is snapshot date, date is observation or target date. Source UnitPrice is GBP
per unit but is only validated, never used for cost or turnover claims.
Inventory financial value, supplier performance and factory throughput are unavailable.
""",
    )
    write(
        "docs/STAKEHOLDER_BRIEF.md",
        f"""
# Hypothetical planner brief
**Practice deliverable, not presented to Danfoss or real customers.**

The synthetic scenario flags {s["at_risk_products_synthetic"]} of 20 products below
reorder threshold and {s["overstock_products_synthetic"]} above 60 days of cover.
Open Inventory Risk and compare stock, lead time, daily forecast and safety stock
before deciding whether to place an order. These flags describe assumptions, not
actual inventory shortages. There are no receipts or open purchase orders in this data.

Ridge has the lowest pooled holdout WAPE ({ridge:.2f}%), compared with seasonal-naive
({seasonal:.2f}%). However it underforecasts by {abs(scores["ridge"]["bias"]) * 100:.2f}%
of actual units in aggregate. A planner relying on these forecasts alone could order
too little. High errors justify manual review and additional data, not automated orders.

Monitor WAPE, bias, cover, reorder thresholds, exceptions and planned utilization.
Review high-error products in reports/high_error_products.csv. The run's source
quality issues include cancellations/negative quantities, duplicate lines, prices,
missing descriptions and deliberately excluded December dates. Reason counts overlap.
All 14 independent KPI checks agree. That validates arithmetic, not the suitability
of scenario assumptions. Real lead times, shared capacity, stock records and service
targets require human confirmation. Forecast-error reduction is not business savings.
""",
    )
    write(
        "docs/RISK_REGISTER.md",
        """
# Risk register
Hypothetical owners describe roles, not real named stakeholders.

| Risk | Impact | Mitigation / escalation |
|---|---|---|
| Retail sales substituted for manufacturing demand | external validity low | label proxy; planner must supply real factory demand |
| Zero-filled absent transactions hide censored demand | underforecast | label zero policy; request availability/closure history |
| Duplicate lines may be legitimate | demand undercount | preserve rejected rows; data-owner review before changing policy |
| High error / negative forecast bias | unsafe ordering | manual planning only; review product errors and additional history |
| Synthetic lead and stock assumptions | flags have no operational validity | maintain separate planning_source; planner replaces with observed data |
| Independent normal safety-stock approximation | service level not assured | calibrate variability and lead-time distribution |
| Single per-product capacity | shared resource bottlenecks ignored | no factory-utilization claim |
| Desktop applications unavailable | native report validation incomplete | exact local build and acceptance instructions |
| Output overwrite/concurrent run | partial files | dedicated root, single writer; preserve release ZIP |
| Customer IDs in public raw data | unnecessary identity distribution | no customer analytics; review licensed source before publishing |
""",
    )
    write(
        "docs/ARCHITECTURE.md",
        """
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
""",
    )
    write(
        "docs/DECISIONS.md",
        """
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
""",
    )
    write(
        "docs/WINDOWS_SETUP.md",
        r"""
# Windows 11 PowerShell setup
Install Python 3.12 and a Java 17 JDK. For example, if winget is available:
```powershell
winget install --exact --id Python.Python.3.12
winget install --exact --id EclipseAdoptium.Temurin.17.JDK
```
Reopen PowerShell, extract the ZIP, then:
```powershell
cd C:\path\SupplySight-Analytics
java -version
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:SPARK_LOCAL_IP = '127.0.0.1'
$env:PYSPARK_PYTHON = (Get-Command python).Source
python -m supplysight.cli
python -m pytest -q
ruff check src scripts tests notebooks
ruff format --check src scripts tests notebooks
```
If activation is blocked, use `.\.venv\Scripts\python.exe` directly in place of
python. Ensure JAVA_HOME points to the installed JDK root if Spark cannot find Java.
Use a local path without spaces if Hadoop path handling fails on Windows. Spark
may require Windows Hadoop native binaries for file permissions in some installations.
Do not download arbitrary winutils executables. Use WSL2 Ubuntu with Java 17/Python
3.12 as the reliable fallback, or a trusted matching Hadoop build from your institution.
Only Linux was executed here; native Windows runtime remains unverified.

Open the included Excel file. It already contains cached computed values. After
rerunning the pipeline, refresh it with Excel installed:
```powershell
powershell -File .\scripts\Refresh-Workbook.ps1
```
That COM script is authored but not executed here. Close the workbook before running.
It checks row counts before updating and preserves formulas. For full data refresh
without Desktop, request regeneration through the included Artifact Tool builder.
""",
    )
    write(
        "docs/EXCEL_GUIDE.md",
        """
# Excel usage and verification
Open excel/SupplySight_Operations_Analysis.xlsx in Excel Desktop. Seven sheets:
Executive Summary, Inventory Risk, Forecast Results, Product Master, Demand History,
KPI Validation and Data Dictionary. The chart and formulas are editable.

Inventory Risk uses editable scenario inputs in E:H, historical means/std in C:D,
and formula-derived cover, reorder point, numeric risk flag (1/0), overstock (1/0),
utilization and variability in I:N. Description in Q uses XLOOKUP (modern Excel).
Forecast error formulas are H:I on Forecast Results. KPI Validation D:E computes
difference/pass from independently generated reference and SQL values. Small
floating errors are acceptable below 1e-6; false checks need investigation.
The terminal validation sheet does not feed business summary formulas.

Artifact Tool recalculation and a stock-input mutation were executed. All seven
sheets were rendered and reviewed. Previews are Artifact Tool renders, not screenshots
of Excel Desktop. openpyxl is used only to inspect the saved XLSX, not to author it.
Native Excel, PivotTables, Power Query refresh and COM automation are NOT VERIFIED.

To refresh using Excel, close it and run scripts/Refresh-Workbook.ps1 after pipeline.
It preserves formulas and checks the 20-product / 365-day template row counts.
If inputs/shapes change, rebuild rather than truncate. The included build_workbook.mjs
requires @oai/artifact-tool in its supported authoring runtime.

Manual PivotTable: select Demand History table → Insert → PivotTable → New Worksheet.
Rows: product_id; Columns: date grouped by month; Values: sum of units. Reconcile
Grand Total to Executive Summary B6. Do not sum ratios or forecast actuals across models.
For Power Query: Data → Get Data → From Text/CSV → daily_demand.csv; set product_id
to Text, date to Date and units to Decimal Number → Close & Load. Refresh All after
rerunning the pipeline and compare totals. These are manual instructions, not completed features.
""",
    )
    write(
        "docs/DATABRICKS_SETUP.md",
        """
# Databricks notebook import — NOT EXECUTED on Databricks
Five Databricks source-format Python notebooks use the same package functions as
local Spark. They do not pretend to be executed Databricks jobs. Free Edition access
and current workspace policy determine availability of file upload and volumes.

1. In your workspace, upload the extracted project to a writable Workspace Files
   directory, or an authorized Unity Catalog volume. Retain data/raw and src.
2. Create/import each notebooks/*.py as a Python source notebook.
3. Attach available compute with Spark and compatible pandas/numpy/scikit-learn.
   The local tested runtime is Spark 3.5.3 + Python 3.12 + Java 17. Databricks runtime
   compatibility is unverified. Do not replace managed runtime PySpark with pip.
4. Set each notebook's project_root widget to the absolute project directory,
   e.g. /Workspace/Users/<you>/SupplySight-Analytics. Ensure it is writable.
5. Install missing non-Spark dependencies on that compute if workspace policy allows.
   Do not use requirements.txt unchanged because it pins local PySpark.
6. Run notebooks 01→05 in order. Existing managed `spark` is reused; it is not stopped.
7. Compare reported counts with evaluation.json and all checks with reconciliation CSV.
   Capture genuine notebook outputs/runtime details only after successful execution.

These notebooks also run locally through scripts/verify_notebooks.py using the
included data and local Spark. Local execution does not verify Databricks APIs,
permissions, managed dependencies or filesystem semantics. No DBFS mount, secret,
cloud deployment or paid service is required by the local path.
""",
    )
    write(
        "powerbi/README.md",
        """
# Power BI implementation kit — no PBIX created
Included: CSV exports, Power Query M, 17 authored DAX measures, model relationships,
theme and three-page build/acceptance guide. No measure was executed in the DAX
engine here. SQL reconciliation verifies the corresponding arithmetic, not DAX
syntax, relationship behavior or filter context in Power BI Desktop.

Follow dashboard_build_guide.md, then model_specification.md. See measures.dax
and power_query.m. Source CSVs are in ../data/processed/gold. No generated picture
is being presented as a Power BI preview. Native screenshots must be captured locally.
""",
    )
    write(
        "powerbi/model_specification.md",
        """
# Dimensional model
| One side | Many side | Key | Direction |
|---|---|---|---|
| Product | Demand | product_id | single, Product→Demand |
| Product | Forecast | product_id | single, Product→Forecast |
| Product | Inventory | product_id | single, Product→Inventory |
| Date | Demand | date | single, Date→Demand |
| Date | Forecast | date | single, Date→Forecast |

Product and Date must have unique non-null keys. Mark Date as a date table.
Inventory is a fixed November 30 scenario, filtered by Product only. Its as_of
date is not an active relationship: historical date slicers must not silently turn
the scenario on/off. Label this snapshot explicitly and disable date-slicer interactions
with inventory cards if necessary. No bidirectional relationships or fact-to-fact joins.
Product categories are unavailable; drill down by product_id and description only.

Forecast has three model rows per product-target day; never sum raw actual across
models. Use authored measures with a single model selection, default seasonal_naive.
Train-end/fold belong to the forecast fact, not the Date dimension relationship.
Future forecast dates exceed the historical Date range. Future forecast is a
separate export, excluded from this model unless Date is extended appropriately.

Format counts as integers, units to 0–1 decimals, ratios as 0.0%, dates dd-mmm-yyyy.
On-hand units are additive across products but never across snapshot dates.
Days cover is a labeled unweighted mean, not a total; capacity is a ratio of sums.
Demand CV is meaningful for a single product; restrict that visual to one product.
""",
    )
    write(
        "powerbi/dashboard_build_guide.md",
        f"""
# Power BI Desktop build and acceptance
1. Blank report → Transform Data → create GoldRoot text query and LoadGold function
   by copying individual sections of power_query.m. Do not paste the whole file as
   one query. Create Product, Date, Demand, Forecast, Inventory from the named calls.
   Disable load for GoldRoot/LoadGold. Verify dates, numbers and true/false types.
2. Apply changes, create relationships from model_specification.md, mark Date.
3. Create each DAX measure separately, import theme.json, make three 16:9 pages.
4. Save a real SupplySight.pbix and reopen it. Only then record PBIX completion.

| Page | Visuals and interaction |
|---|---|
| Executive Operations Overview | cards Total Demand, Products Monitored, At Risk Products, Forecast WAPE; monthly demand line; exception table; Date and Product slicers; Model single-select |
| Inventory Health & Capacity | risk table with stock/reorder/cover; product cover bars; overstock filter; planned capacity bars; Product drill-through; fixed synthetic as-of label |
| Demand Forecast & Variance | Actual vs Forecast line using measures, not raw actual; model WAPE/MAE/bias table; high-error product table; Product, Date and single-select Model slicers |

Navy #17324D, slate #64748B, teal #0D9488, blue #2563EB, white background.
Red highlights risk only. All inventory/capacity visuals say SYNTHETIC.
Forecast tooltip includes model, train_end, fold, actual, predicted and error.
Demand trend covers historical reporting window; forecast trend covers the held-out
42 days. Model comparison table uses Forecast[model] rows; chosen-model measures
resolve per row. In a date/product subset, WAPE recomputes pooled numerator and denominator.
Week-change measure compares equally sized date windows; use full weeks for weekly decisions.

Acceptance controls with all filters cleared:
- Total Demand = {s["gold_units"]:,.0f}; Products Monitored = 20.
- Scenario at-risk = {s["at_risk_products_synthetic"]}; overstock = {s["overstock_products_synthetic"]}.
- WAPE by model: naive {naive:.6f}%, seasonal-naive {seasonal:.6f}%, ridge {ridge:.6f}%.
- Compare MAE, bias and capacity controls to reports/kpi_reconciliation.csv (tolerance 1e-6).
- Single-product filter must affect all facts through Product. Date filters affect
  sales/forecast but not the fixed inventory scenario. Confirm this visually.
- Do not display zero error when selected actual total is zero: DIVIDE returns blank.
- With model slicer cleared, default seasonal-naive prevents triple-counting actuals.
Capture each page from actual Desktop only after these checks. All these native
acceptance actions remain pending; there is no PBIX or Power BI screenshot here.
""",
    )
    (ROOT / "powerbi/theme.json").write_text(
        json.dumps(
            {
                "name": "SupplySight",
                "dataColors": ["#0D9488", "#2563EB", "#64748B", "#DC2626"],
                "background": "#FFFFFF",
                "foreground": "#17324D",
                "tableAccent": "#0D9488",
            },
            indent=2,
        )
    )
    write(
        "docs/PUBLISHING.md",
        """
# Repository publishing checklist
- Review dataset attribution, customer-ID exposure, source license and reject policy.
- Review README execution limits and reports/verification.md. No fake CI badges.
- Exclude caches, virtual environments, credentials and Spark temporary files.
- Keep included subset + provenance + workbook + evaluation evidence for reproduction.
- Create a repository only when you choose to publish; no repository was created here.
- Commit source, run local checks, then push and inspect the first real Actions run.
- Add genuine Power BI/Databricks screenshots only after native validation.
- Do not tag Danfoss as a customer or imply company sponsorship.
""",
    )
    write(
        "docs/RESUME_AND_INTERVIEW.md",
        f"""
# Evidence-based resume and interview material

## Three resume bullets
- Engineered a local PySpark Bronze/Silver/Gold pipeline for {s["raw_records"]:,}
  public retail records, isolating {s["rejected_records"]:,} rejected rows through
  eight quality-rule families and producing eight analytical datasets with
  Databricks-importable notebooks (Databricks execution unverified).
- Evaluated 20 product series using three chronological 14-day backtests, reducing
  pooled WAPE from {seasonal:.2f}% for seasonal-naive to {ridge:.2f}% with leakage-safe
  Ridge regression, a {s["ridge_improvement_vs_seasonal_wape"] * 100:.2f}% relative reduction.
- Built a seven-sheet Excel analysis workbook and Power BI-ready inventory/forecast
  datasets, reconciling 14 KPIs through independent SQL checks and flagging
  {s["at_risk_products_synthetic"]} products in an explicitly synthetic planning scenario.

## ATS skills supported by executed work
Python, PySpark, Spark SQL, SQL, ETL, Parquet, pandas, NumPy, scikit-learn,
chronological backtesting, time-series forecasting, demand planning analytics,
inventory scenario analysis, data quality, KPI reconciliation, DuckDB, pytest,
Excel workbook formulas and charts. DAX, Power Query and Databricks notebook
authoring may be described as authored work, **not verified runtime proficiency**.
Power BI Desktop, native Excel refresh and deployed Databricks are not established.

## Portfolio summary
SupplySight Analytics transforms public retail sales into validated demand datasets,
compares explainable forecasts through rolling-origin evaluation, and connects the
results to transparent synthetic inventory and capacity scenarios. It combines
local Spark ETL, independent SQL reconciliation and an editable Excel reporting
workbook with Power BI implementation files and Databricks notebook sources.

## Five interview questions and suggested answers
1. **Why Spark for only 26k rows?** To demonstrate schema contracts, distributed
   transformations, Spark SQL and layered ETL. Pandas would be sufficient for this
   volume. I did not measure or claim a Spark performance advantage.
2. **How did you validate ETL?** Raw equals accepted plus rejected. Each rejected
   row keeps reasons and source ID. Silver units reconcile to daily Gold, weekly
   totals reconcile to daily, and DuckDB independently recomputes 14 KPI aggregates.
3. **How did you prevent leakage?** Products were selected before the test period.
   Each origin trains only on previous dates; scaling fits training values only.
   Recursive lags use predictions. A test changes holdout actuals and confirms
   same-origin predictions stay identical.
4. **How did you assess forecasting?** Same targets/horizons across naive,
   seasonal-naive and Ridge, three expanding origins, MAE/WAPE/bias and product
   comparisons. Ridge improves WAPE but remains highly inaccurate and underbiased.
5. **How would a manager use it?** Review the synthetic risk table and why each
   flag appears. Replace assumptions with real stock, lead and receipt inputs,
   inspect bias and errors, then make human replenishment decisions. No automated
   orders, observed stockouts or realized savings were claimed.
""",
    )
    write(
        "data/README.md",
        """
# Data provenance
Raw subset is an attributed derivative of Chen (2015), UCI Online Retail, CC BY 4.0.
https://archive.ics.uci.edu/dataset/352/online+retail
https://doi.org/10.24432/C5BW33
License: https://creativecommons.org/licenses/by/4.0/
See provenance.json for hashes and transformation/selection rules. The full original
XLSX is not redistributed in this archive; the included subset is sufficient to run.
Customer IDs are public source values, unnecessary for analytics and never modeled.
Synthetic planning_inputs.csv is generated with seed 52316; it is not UCI inventory.
Processed Gold is an analytical derivative. Do not treat retail sales as factory demand.
""",
    )
    banner = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 260"><rect width="1200" height="260" fill="#10283f"/><path d="M900 170h55v-55h55v-45h55v-30" fill="none" stroke="#2dd4bf" stroke-width="12"/><circle cx="1065" cy="40" r="10" fill="#2dd4bf"/><text x="65" y="110" font-size="56" fill="white" font-family="Arial" font-weight="bold">SupplySight</text><text x="68" y="158" font-size="25" fill="#a8c5d9" font-family="Arial">Inventory intelligence. Measured forecasting.</text><text x="68" y="214" font-size="17" fill="#5eead4" font-family="Arial">PYSPARK / SQL / FORECASTING / ANALYTICS</text></svg>"""
    write("docs/banner.svg", banner)
    write(
        "docs/logo.svg",
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><rect width="120" height="120" rx="22" fill="#17324D"/><path d="M20 85h25V60h25V35h25" fill="none" stroke="#2dd4bf" stroke-width="10"/></svg>',
    )


if __name__ == "__main__":
    main()
