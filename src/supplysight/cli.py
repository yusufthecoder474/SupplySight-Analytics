import argparse
import traceback
from pathlib import Path

from .config import ROOT, spark_session
from .ingestion import ingest
from .reporting import finish
from .storage import write_parquet
from .transformations import gold_tables
from .validation import RULES, validate


def run(root=ROOT, raw=None):
    root = Path(root)
    for d in ["reports", "data/processed", "data/synthetic", "docs/screenshots"]:
        (root / d).mkdir(parents=True, exist_ok=True)
    spark = spark_session()
    spark.sparkContext.setLogLevel("ERROR")
    try:
        bronze = ingest(spark, raw or root / "data/raw/retail_subset.csv").cache()
        raw_count = bronze.count()
        write_parquet(bronze, root / "data/processed/bronze")
        silver, rejects = validate(bronze)
        silver, rejects = silver.cache(), rejects.cache()
        accepted, rejected = silver.count(), rejects.count()
        assert raw_count == accepted + rejected
        write_parquet(silver, root / "data/processed/silver")
        write_parquet(rejects, root / "data/processed/rejected")
        rejects.toPandas().to_csv(root / "reports/rejected_records.csv", index=False)
        quality = []
        from pyspark.sql import functions as F

        for name, description in RULES.items():
            n = rejects.filter(F.array_contains(F.split("rejection_reasons", ";"), name)).count()
            quality.append({"rule": name, "description": description, "violating_rows": n})
        import pandas as pd

        pd.DataFrame(quality).to_csv(root / "reports/data_quality.csv", index=False)
        frames = {}
        for name, df in gold_tables(spark, silver).items():
            write_parquet(df, root / f"data/processed/gold/{name}")
            frames[name] = df.toPandas().sort_values(df.columns[:1]).reset_index(drop=True)
        # SQL sum independently reconciles accepted source records to zero-filled Gold demand.
        gold_units = spark.sql("SELECT sum(units) AS units FROM daily_demand").first().units
        silver_units = silver.agg(F.sum("units")).first()[0]
        assert gold_units == silver_units
        finish(
            root,
            frames,
            {
                "raw_records": raw_count,
                "accepted_records": accepted,
                "rejected_records": rejected,
                "quality_rules": len(RULES),
                "silver_units": silver_units,
                "gold_units": gold_units,
            },
        )
        bronze.unpersist()
        silver.unpersist()
        rejects.unpersist()
    except Exception:
        (root / "reports/ingestion_error.txt").write_text(traceback.format_exc())
        raise
    finally:
        spark.stop()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--raw", type=Path)
    args = p.parse_args()
    run(args.root, args.raw)
    print((args.root / "reports/evaluation.json").read_text())


if __name__ == "__main__":
    main()
