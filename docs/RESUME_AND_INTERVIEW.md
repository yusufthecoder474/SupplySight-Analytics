# Evidence-based resume and interview material

## Three resume bullets
- Engineered a local PySpark Bronze/Silver/Gold pipeline for 26,058
  public retail records, isolating 1,800 rejected rows through
  eight quality-rule families and producing eight analytical datasets with
  Databricks-importable notebooks (Databricks execution unverified).
- Evaluated 20 product series using three chronological 14-day backtests, reducing
  pooled WAPE from 99.06% for seasonal-naive to 76.64% with leakage-safe
  Ridge regression, a 22.63% relative reduction.
- Built a seven-sheet Excel analysis workbook and Power BI-ready inventory/forecast
  datasets, reconciling 14 KPIs through independent SQL checks and flagging
  8 products in an explicitly synthetic planning scenario.

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
