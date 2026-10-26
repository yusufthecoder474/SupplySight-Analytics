from pyspark.sql import functions as F

from .config import END, START


def gold_tables(spark, silver):
    # One deterministic description per ID. Names are descriptive only, never forecast features.
    products = silver.groupBy("product_id").agg(F.min("Description").alias("description"))
    calendar = spark.sql(
        f"SELECT explode(sequence(to_date('{START}'), to_date('{END}'), interval 1 day)) AS date"
    )
    observed = silver.groupBy("product_id", "date").agg(F.sum("units").alias("units"))
    daily = (
        products.select("product_id")
        .crossJoin(calendar)
        .join(observed, ["product_id", "date"], "left")
        .fillna(0, subset=["units"])
    )
    daily = daily.withColumn(
        "observed_or_assumed_zero", F.lit("sales proxy; absent transactions assumed zero")
    )
    daily.createOrReplaceTempView("daily_demand")
    weekly = spark.sql(
        "SELECT product_id, cast(date_trunc('week', date) as date) AS week, sum(units) AS units, count(*) AS days_in_week FROM daily_demand GROUP BY product_id, date_trunc('week', date)"
    )
    dates = (
        calendar.withColumn("year", F.year("date"))
        .withColumn("month", F.month("date"))
        .withColumn("week", F.to_date(F.date_trunc("week", "date")))
    )
    return {
        "product_master": products,
        "daily_demand": daily,
        "weekly_demand": weekly,
        "date_dimension": dates,
    }
