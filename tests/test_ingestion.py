import pytest

from supplysight.ingestion import ingest
from supplysight.validation import validate


def test_valid_source(spark, raw_file):
    df = ingest(spark, raw_file)
    assert df.count() == 1
    assert len(df.first().source_sha256) == 64


def test_missing_file(spark, tmp_path):
    with pytest.raises(FileNotFoundError):
        ingest(spark, tmp_path / "absent.csv")


def test_missing_field(spark, tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("StockCode,Quantity\n12345,1\n")
    with pytest.raises(ValueError, match="schema"):
        ingest(spark, path)


def test_schema_version(spark, raw_file):
    with pytest.raises(ValueError, match="version"):
        ingest(spark, raw_file, version=99)


@pytest.mark.parametrize(
    "column,value,reason",
    [
        ("Quantity", "abc", "quantity"),
        ("Quantity", "-1", "quantity"),
        ("Quantity", "1.5", "quantity"),
        ("Quantity", "NaN", "quantity"),
        ("UnitPrice", "0", "price"),
        ("UnitPrice", "Infinity", "price"),
        ("StockCode", "POST", "product"),
        ("Description", "", "description"),
        ("InvoiceNo", "C536365", "invoice"),
        ("InvoiceDate", "bad", "date"),
        ("InvoiceDate", "2011-12-09 08:00:00", "date"),
        ("source_row_id", "bad", "source_id"),
    ],
)
def test_invalid_record_isolated(spark, raw_file, column, value, reason):
    from pyspark.sql import functions as F

    df = ingest(spark, raw_file).withColumn(column, F.lit(value))
    accepted, rejected = validate(df)
    assert accepted.count() == 0
    assert reason in rejected.first().rejection_reasons


def test_empty_header_only(spark, raw_file):
    raw_file.write_text(raw_file.read_text().splitlines()[0] + "\n")
    assert ingest(spark, raw_file).count() == 0


def test_duplicate_policy(spark, raw_file):
    from pyspark.sql import functions as F

    df = ingest(spark, raw_file)
    second = df.withColumn("source_row_id", F.lit("3"))
    accepted, rejected = validate(df.unionByName(second))
    assert accepted.count() == 1
    assert accepted.first().source_row_id == "2"
    assert "duplicate" in rejected.first().rejection_reasons
