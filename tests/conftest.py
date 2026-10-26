import os

import pytest

os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")


@pytest.fixture(scope="session")
def spark():
    from supplysight.config import spark_session

    session = spark_session()
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


@pytest.fixture
def raw_file(tmp_path):
    import csv

    from supplysight.ingestion import REQUIRED

    path = tmp_path / "source.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(REQUIRED)
        w.writerow(
            [
                2,
                "536365",
                "85123A",
                "WHITE HANGING HEART",
                6,
                "2010-12-01 08:26:00",
                2.55,
                "17850",
                "UK",
            ]
        )
    return path
