# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze ingestion
# MAGIC Public UCI sales subset. Raw strings are preserved alongside source metadata.

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
from supplysight.config import spark_session
from supplysight.ingestion import ingest
from supplysight.storage import write_parquet

if "spark" not in globals():
    spark = spark_session()
spark.conf.set("spark.sql.ansi.enabled", "false")
bronze = ingest(spark, root / "data/raw/retail_subset.csv")
write_parquet(bronze, root / "data/processed/bronze")
print({"bronze_rows": bronze.count(), "spark_version": spark.version})
bronze.select("source_file", "source_sha256", "schema_version").distinct().show(truncate=False)

# COMMAND ----------
from supplysight.runtime_log import record_runtime
record_runtime(root, "01_bronze_ingestion", spark if "spark" in globals() else None, "Databricks" if "dbutils" in globals() else "local PySpark", time.perf_counter() - _notebook_started)
