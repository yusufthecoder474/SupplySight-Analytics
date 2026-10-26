import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HORIZON = 14
FOLDS = 3
SEED = 52316
START = "2010-12-01"
END = "2011-11-30"


def spark_session():
    from pyspark.sql import SparkSession

    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    return (
        SparkSession.builder.appName("SupplySight")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.sql.ansi.enabled", "false")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
