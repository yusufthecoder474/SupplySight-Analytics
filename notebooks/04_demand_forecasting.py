# Databricks notebook source
# MAGIC %md
# MAGIC # Forecast evaluation and synthetic planning outputs
# MAGIC Three models share targets. Stock, lead time and capacity are hypothetical.

# COMMAND ----------
import time
_notebook_started = time.perf_counter()
import sys
from pathlib import Path

if "dbutils" in globals():
    dbutils = globals()["dbutils"]
    dbutils.widgets.text("project_root", "")
    code_root = Path(dbutils.widgets.get("project_root"))
    dbutils.widgets.text("data_root", "")
    root = Path(dbutils.widgets.get("data_root"))
    if not str(root).startswith("/Volumes/") or not (code_root / "src").exists():
        raise ValueError("Set project_root to workspace source and data_root to a dedicated /Volumes/.../run folder")
else:
    code_root = Path(__file__).resolve().parents[1]
    root = Path(globals().get("run_root", code_root))
sys.path.insert(0, str(code_root / "src"))
from pyspark.sql import functions as F

from supplysight.config import spark_session
from supplysight.reporting import finish
from supplysight.validation import RULES

if "spark" not in globals():
    spark = spark_session()
frames = {
    name: spark.read.parquet(str(root / f"data/processed/gold/{name}")).toPandas()
    for name in ["product_master", "daily_demand", "weekly_demand", "date_dimension"]
}
bronze = spark.read.parquet(str(root / "data/processed/bronze"))
silver = spark.read.parquet(str(root / "data/processed/silver"))
rejected = spark.read.parquet(str(root / "data/processed/rejected"))
stats = {
    "raw_records": bronze.count(),
    "accepted_records": silver.count(),
    "rejected_records": rejected.count(),
    "quality_rules": len(RULES),
    "silver_units": silver.agg(F.sum("units")).first()[0],
    "gold_units": float(frames["daily_demand"].units.sum()),
}
finish(root, frames, stats)
from supplysight.constrained_planning import run as constrained_plan
constrained_plan(root)
print((root / "reports/evaluation.json").read_text())

# COMMAND ----------
from supplysight.runtime_log import record_runtime
record_runtime(root, "04_demand_forecasting", spark if "spark" in globals() else None, "Databricks" if "dbutils" in globals() else "local PySpark", time.perf_counter() - _notebook_started)
