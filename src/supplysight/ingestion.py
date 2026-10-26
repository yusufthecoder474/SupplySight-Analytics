import hashlib

from pyspark.sql import functions as F

REQUIRED = [
    "source_row_id",
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


def ingest(spark, path, version=1):
    if version != 1:
        raise ValueError("Unsupported schema version")
    if not path.exists():
        raise FileNotFoundError(path)
    raw = (
        spark.read.option("header", True)
        .option("multiLine", True)
        .option("escape", '"')
        .csv(str(path))
    )
    if set(raw.columns) != set(REQUIRED):
        raise ValueError(f"Source schema mismatch: expected {REQUIRED}, got {raw.columns}")
    return (
        raw.withColumn("source_file", F.lit(path.name))
        .withColumn("source_sha256", F.lit(hashlib.sha256(path.read_bytes()).hexdigest()))
        .withColumn("ingested_at", F.current_timestamp())
        .withColumn("schema_version", F.lit(version))
    )
