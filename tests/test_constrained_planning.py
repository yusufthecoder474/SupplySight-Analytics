import numpy as np
import pandas as pd
import pytest

from supplysight.constrained_planning import (
    Policy,
    apply_forecasts,
    plan_product,
    plan_table,
)


def test_hand_calculated_capacity_and_balance():
    # Safety 2*3*sqrt(4)=12; reorder=52; target=122; request=102; capacity=35.
    r = plan_product(10, 20, 4, 35, 3, policy=Policy(safety_z=2))
    assert r["safety_stock"] == 12 and r["reorder_point"] == 52
    assert r["target_stock"] == 122 and r["requested_production"] == 102
    assert r["planned_production"] == 35 and r["deferred_production"] == 67
    assert r["prearrival_shortfall"] == 20 and r["modeled_unserved_units"] == 20
    assert r["fulfilled_units"] == 50 and r["projected_ending_stock"] == 5


def test_safety_and_reorder_overrides(tmp_path):
    r = plan_product(10, 20, 2, 100, safety_stock=5, reorder_point=30)
    assert r["safety_stock"] == 5 and r["reorder_point"] == 30
    assert r["requested_production"] == 75 and r["planned_production"] == 75
    from supplysight.constrained_planning import run

    gold = tmp_path / "data/processed/gold"
    gold.mkdir(parents=True)
    inputs = scenario()
    inputs["reorder_point"] = 9999  # Gold-derived output must not override a new policy.
    inputs.to_csv(gold / "inventory_risk.csv", index=False)
    computed = run(tmp_path, policy=Policy(safety_z=0))
    assert computed.reorder_point.iloc[0] == 20


def test_threshold_equality_does_not_order():
    r = plan_product(10, 50, 5, 100)
    assert not r["reorder_required"] and r["planned_production"] == 0


def test_zero_capacity_is_closed_line():
    r = plan_product(10, 0, 1, 0)
    assert r["capacity_limited"] and r["planned_production"] == 0
    assert r["modeled_unserved_units"] == 70


def test_zero_demand_stock_and_lead():
    r = plan_product(0, 0, 0, 0)
    assert r["requested_production"] == 0 and r["modeled_unserved_units"] == 0


def test_delayed_arrival_cannot_supply_horizon():
    r = plan_product(10, 0, 8, 1000)
    assert r["planned_production"] == 150 and r["arriving_in_horizon"] == 0
    assert r["modeled_unserved_units"] == 70 and r["production_arrives_after_horizon"]


def test_lead_equal_horizon_keeps_prearrival_shortfall():
    r = plan_product(10, 0, 7, 1000)
    assert r["arriving_in_horizon"] == 140 and r["modeled_unserved_units"] == 70
    assert r["projected_ending_stock"] == 140


def test_horizon_scales_capacity():
    r = plan_product(10, 0, 1, 70, policy=Policy(horizon_days=14))
    assert r["horizon_capacity"] == 140 and r["planned_production"] <= 140


@pytest.mark.parametrize(
    "field",
    [
        "forecast_daily",
        "on_hand",
        "lead_days",
        "weekly_capacity",
        "std_daily",
        "safety_stock",
        "reorder_point",
    ],
)
@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_invalid_numbers(field, value):
    args = {"forecast_daily": 1, "on_hand": 1, "lead_days": 1, "weekly_capacity": 1, "std_daily": 1}
    args[field] = value
    with pytest.raises(ValueError):
        plan_product(**args)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"horizon_days": 0},
        {"horizon_days": 1.5},
        {"horizon_days": True},
        {"review_days": -1},
        {"safety_z": float("inf")},
    ],
)
def test_invalid_policy(kwargs):
    with pytest.raises(ValueError):
        Policy(**kwargs)


def scenario():
    return pd.DataFrame(
        [
            {
                "product_id": "p1",
                "on_hand": 0,
                "lead_days": 2,
                "weekly_capacity": 30,
                "std_daily_28d": 1,
                "forecast_daily": 10,
                "planning_source": "SYNTHETIC test",
            }
        ]
    )


@pytest.mark.parametrize("change", ["duplicate", "missing", "unlabeled", "empty_key"])
def test_scenario_validation(change):
    frame = scenario()
    if change == "duplicate":
        frame = pd.concat([frame, frame])
    if change == "missing":
        frame = frame.drop(columns="weekly_capacity")
    if change == "unlabeled":
        frame["planning_source"] = "unknown"
    if change == "empty_key":
        frame["product_id"] = ""
    with pytest.raises(ValueError):
        plan_table(frame)


def test_forecast_override_key_alignment():
    f = scenario()
    changed = apply_forecasts(f, pd.DataFrame({"product_id": ["p1"], "forecast_daily": [2]}))
    assert changed.forecast_daily.iloc[0] == 2
    without_embedded_forecast = apply_forecasts(
        f.drop(columns="forecast_daily"),
        pd.DataFrame({"product_id": ["p1"], "forecast_daily": [2]}),
    )
    assert without_embedded_forecast.forecast_daily.iloc[0] == 2
    with pytest.raises(ValueError):
        apply_forecasts(f, pd.DataFrame({"product_id": ["p2"], "forecast_daily": [2]}))


def test_randomized_capacity_and_inventory_invariants():
    rng = np.random.default_rng(52316)
    for _ in range(100):
        demand, stock, lead, capacity = rng.uniform(0, 100, 4)
        r = plan_product(demand, stock, lead, capacity)
        assert 0 <= r["planned_production"] <= r["horizon_capacity"]
        assert r["requested_production"] == pytest.approx(
            r["planned_production"] + r["deferred_production"]
        )
        assert r["horizon_demand"] == pytest.approx(
            r["fulfilled_units"] + r["modeled_unserved_units"]
        )
        assert stock + r["arriving_in_horizon"] == pytest.approx(
            r["fulfilled_units"] + r["projected_ending_stock"]
        )
