"""Run five source notebooks locally with one shared Spark session, not Databricks."""

import runpy
import sys
from pathlib import Path

from supplysight.config import spark_session

root = Path(__file__).resolve().parents[1]
run_root = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root
spark = spark_session()
spark.sparkContext.setLogLevel("ERROR")
try:
    for notebook in sorted((root / "notebooks").glob("*.py")):
        print(f"LOCAL NOTEBOOK: {notebook.name}", flush=True)
        runpy.run_path(str(notebook), init_globals={"spark": spark, "run_root":run_root})
finally:
    spark.stop()
