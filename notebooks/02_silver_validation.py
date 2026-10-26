# Databricks notebook source
# MAGIC %md
# MAGIC # Silver validation
# MAGIC Cancellations, invalid data and out-of-window dates are isolated with reasons.

# COMMAND ----------
import time
_notebook_started = time.perf_counter()
import sys
from pathlib import Path

import pandas as pd

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
from supplysight.storage import write_parquet
from supplysight.validation import RULES, validate

if "spark" not in globals():
    spark = spark_session()
spark.conf.set("spark.sql.ansi.enabled", "false")
bronze = spark.read.parquet(str(root / "data/processed/bronze"))
silver, rejected = validate(bronze)
write_parquet(silver, root / "data/processed/silver")
write_parquet(rejected, root / "data/processed/rejected")
assert bronze.count() == silver.count() + rejected.count()
root.joinpath("reports").mkdir(exist_ok=True)
rejected.toPandas().to_csv(root / "reports/rejected_records.csv", index=False)
quality = [
    {
        "rule": name,
        "description": rule,
        "violating_rows": rejected.filter(
            F.array_contains(F.split("rejection_reasons", ";"), name)
        ).count(),
    }
    for name, rule in RULES.items()
]
pd.DataFrame(quality).to_csv(root / "reports/data_quality.csv", index=False)
print({"accepted": silver.count(), "rejected": rejected.count()})

# COMMAND ----------
from supplysight.runtime_log import record_runtime
record_runtime(root, "02_silver_validation", spark if "spark" in globals() else None, "Databricks" if "dbutils" in globals() else "local PySpark", time.perf_counter() - _notebook_started)
