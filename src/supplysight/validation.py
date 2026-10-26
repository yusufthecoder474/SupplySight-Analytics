from pyspark.sql import Window
from pyspark.sql import functions as F

from .config import END, START

RULES = {
    "source_id": "Source row ID is a positive integer and unique",
    "invoice": "Invoice identifier is six digits; cancellation invoices isolated",
    "product": "Product identifier has five digits and optional alphabetic suffix",
    "date": "Timestamp parses and lies in the complete reporting window",
    "quantity": "Quantity is an integer strictly greater than zero",
    "price": "Price is finite and positive",
    "description": "Description is nonempty",
    "duplicate": "Exact business-field duplicates retain lowest source row ID",
}


def validate(bronze):
    business = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
    ]
    w = Window.partitionBy(*business).orderBy(F.col("source_row_id").cast("long"))
    idw = Window.partitionBy("source_row_id").orderBy(*business)
    df = (
        bronze.withColumn("product_id", F.upper(F.trim("StockCode")))
        .withColumn("date", F.to_date(F.to_timestamp("InvoiceDate", "yyyy-MM-dd HH:mm:ss")))
        .withColumn("units", F.col("Quantity").cast("double"))
        .withColumn("price", F.col("UnitPrice").cast("double"))
        .withColumn("duplicate_rank", F.row_number().over(w))
        .withColumn("id_rank", F.row_number().over(idw))
    )
    conditions = [
        (
            F.col("source_row_id").cast("long").isNull()
            | (F.col("source_row_id").cast("long") <= 0)
            | (F.col("id_rank") > 1),
            "source_id",
        ),
        (~F.col("InvoiceNo").rlike(r"^\d{6}$"), "invoice"),
        (~F.col("product_id").rlike(r"^\d{5}[A-Z]?$"), "product"),
        (F.col("date").isNull() | ~F.col("date").between(START, END), "date"),
        (
            F.col("units").isNull()
            | F.isnan("units")
            | (F.col("units") <= 0)
            | (F.col("units") != F.floor("units"))
            | (F.abs("units") == float("inf")),
            "quantity",
        ),
        (
            F.col("price").isNull()
            | F.isnan("price")
            | (F.col("price") <= 0)
            | (F.abs("price") == float("inf")),
            "price",
        ),
        (F.col("Description").isNull() | (F.length(F.trim("Description")) == 0), "description"),
        (F.col("duplicate_rank") > 1, "duplicate"),
    ]
    reasons = [F.when(F.coalesce(c, F.lit(True)), F.lit(name)) for c, name in conditions]
    df = df.withColumn("rejection_reasons", F.concat_ws(";", *reasons))
    return df.filter("rejection_reasons = ''"), df.filter("rejection_reasons != ''")
