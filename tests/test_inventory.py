import numpy as np
import pandas as pd
import pytest

from supplysight.inventory import inventory_metrics, planning


def test_hand_calculated_inventory():
    r = inventory_metrics(10, 2, 30, 4, 70, 10)
    assert r["days_cover"] == 3
    assert r["reorder_point"] == pytest.approx(46.6)
    assert r["stock_risk"] is True
    assert r["planned_utilization"] == 1


def test_exact_threshold_is_not_risk():
    assert inventory_metrics(10, 0, 40, 4, 70, 10)["stock_risk"] is False


@pytest.mark.parametrize("stock,expected", [(600, False), (601, True)])
def test_overstock_boundary(stock, expected):
    assert inventory_metrics(10, 0, stock, 5, 70, 10)["overstock"] == expected


def test_missing_inventory_stays_unknown():
    assert inventory_metrics(10, 1, None, 5, 70, 10)["stock_risk"] is None


def test_zero_demand():
    r = inventory_metrics(0, 0, 10, 5, 70, 0)
    assert r["days_cover"] is None
    assert r["planned_utilization"] == 0


@pytest.mark.parametrize("capacity,lead", [(0, 5), (70, 0), (-1, 5)])
def test_invalid_planning(capacity, lead):
    with pytest.raises(ValueError):
        inventory_metrics(10, 1, 10, lead, capacity, 10)


def test_deterministic_scenario():
    daily = pd.DataFrame(
        {
            "product_id": ["12345"] * 40,
            "date": pd.date_range("2020-01-01", periods=40),
            "units": np.arange(40),
        }
    )
    future = pd.DataFrame({"product_id": ["12345"], "predicted": [10.0]})
    pd.testing.assert_frame_equal(planning(daily, future), planning(daily, future))
