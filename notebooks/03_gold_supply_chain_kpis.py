# Databricks notebook source
# MAGIC %md
# MAGIC # Gold daily and weekly sales
# MAGIC Absent transactions are assumed zero sales, not proven zero latent demand.

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
from supplysight.storage import write_parquet
from supplysight.transformations import gold_tables

if "spark" not in globals():
    spark = spark_session()
silver = spark.read.parquet(str(root / "data/processed/silver"))
for name, table in gold_tables(spark, silver).items():
    write_parquet(table, root / f"data/processed/gold/{name}")
    print(name, table.count())
spark.sql(
    "SELECT product_id, sum(units) AS units FROM daily_demand GROUP BY product_id ORDER BY product_id"
).show()

# COMMAND ----------
from supplysight.runtime_log import record_runtime
record_runtime(root, "03_gold_supply_chain_kpis", spark if "spark" in globals() else None, "Databricks" if "dbutils" in globals() else "local PySpark", time.perf_counter() - _notebook_started)
