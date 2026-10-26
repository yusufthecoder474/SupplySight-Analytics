from supplysight.ingestion import ingest
from supplysight.storage import write_parquet
from supplysight.transformations import gold_tables


def test_output_replacement_does_not_retain_old_part_files(spark, tmp_path):
    dest = tmp_path / "gold"
    write_parquet(spark.createDataFrame([(1,), (2,)], ["n"]), dest)
    import shutil

    shutil.copyfile(dest / "data.parquet", dest / "legacy-part.parquet")
    write_parquet(spark.createDataFrame([(3,)], ["n"]), dest)
    assert [row.n for row in spark.read.parquet(str(dest)).collect()] == [3]


from supplysight.validation import validate


def test_aggregation_references_and_reproducibility(spark, raw_file):
    from pyspark.sql import functions as F

    silver, _ = validate(ingest(spark, raw_file))
    tables = gold_tables(spark, silver)
    daily = tables["daily_demand"]
    assert daily.count() == 365
    assert daily.agg(F.sum("units")).first()[0] == 6
    assert (
        daily.select("product_id").subtract(tables["product_master"].select("product_id")).count()
        == 0
    )
    other = gold_tables(spark, silver)["daily_demand"]
    assert daily.exceptAll(other).count() == other.exceptAll(daily).count() == 0
    # Applying validation to identical raw data gives identical accepted row IDs.
    s2, _ = validate(ingest(spark, raw_file))
    assert silver.select("source_row_id").exceptAll(s2.select("source_row_id")).count() == 0
