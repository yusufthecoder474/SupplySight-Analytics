# Databricks notebook source
# MAGIC %md
# MAGIC # Quality controls
# MAGIC This notebook checks recorded business controls and source partition totals.

# COMMAND ----------
import time
_notebook_started = time.perf_counter()
import json
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
evaluation = json.loads((root / "reports/evaluation.json").read_text())
checks = pd.read_csv(root / "reports/kpi_reconciliation.csv")
assert checks.passed.all()
assert checks.difference.abs().max() < 1e-6
assert evaluation["raw_records"] == evaluation["accepted_records"] + evaluation["rejected_records"]
assert evaluation["silver_units"] == evaluation["gold_units"]
assert (evaluation["raw_records"],evaluation["accepted_records"],evaluation["rejected_records"]) == (26058,24258,1800)
plans = pd.read_csv(root / "reports/constrained_planning/production_plan.csv")
assert (plans.planned_production <= plans.horizon_capacity + 1e-9).all()
assert (plans.projected_ending_stock >= 0).all()
assert ((plans.requested_production - plans.planned_production - plans.deferred_production).abs() < 1e-7).all()
print(checks.to_string(index=False))
print("All independent arithmetic controls passed; native BI execution still unverified.")

# COMMAND ----------
from supplysight.runtime_log import record_runtime
record_runtime(root, "05_data_quality_reconciliation", globals().get("spark"), "Databricks" if "dbutils" in globals() else "local PySpark", time.perf_counter() - _notebook_started)
