"""Single-bucket, per-product production planning using explicit synthetic assumptions.

The model is not an optimizer for shared machines. Demand is uniform within the
bucket; all planned production arrives after lead_days. Unserved demand is lost
sales, not a backorder. It is a modeled exposure, never an observed stock-out.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Policy:
    horizon_days: int = 7
    review_days: int = 7
    safety_z: float = 1.65

    def __post_init__(self):
        for name in ("horizon_days", "review_days"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not np.isfinite(self.safety_z) or self.safety_z < 0:
            raise ValueError("safety_z must be finite and nonnegative")


def number(value, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric, not boolean")
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be numeric") from None
    if not np.isfinite(result) or result < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return result


def plan_product(
    forecast_daily,
    on_hand,
    lead_days,
    weekly_capacity,
    std_daily=0,
    safety_stock=None,
    reorder_point=None,
    policy=None,
):
    """Return an auditable capacity-limited order and projected inventory balance.

    Below-reorder is strict (<), consistent with the existing inventory module.
    Target stock covers lead time + review period and configured safety stock.
    Capacity is available units/week, scaled linearly to the horizon. A closed
    line (zero capacity) is allowed. Orders arriving after the horizon cannot
    satisfy its demand. Within-horizon timing is included in lost-sales exposure.
    """
    policy = policy or Policy()
    daily = number(forecast_daily, "forecast_daily")
    stock = number(on_hand, "on_hand")
    lead = number(lead_days, "lead_days")
    capacity = number(weekly_capacity, "weekly_capacity")
    std = number(std_daily, "std_daily")
    safety = (
        policy.safety_z * std * np.sqrt(lead)
        if safety_stock is None
        else number(safety_stock, "safety_stock")
    )
    reorder = (
        daily * lead + safety if reorder_point is None else number(reorder_point, "reorder_point")
    )
    target = max(reorder, daily * (lead + policy.review_days) + safety)
    needs_order = stock < reorder
    requested = max(0.0, target - stock) if needs_order else 0.0
    available = capacity * policy.horizon_days / 7
    planned = min(requested, available)
    deferred = requested - planned
    arrives = planned if lead <= policy.horizon_days else 0.0
    demand = daily * policy.horizon_days
    prearrival_demand = daily * min(lead, policy.horizon_days)
    prearrival_shortfall = max(0.0, prearrival_demand - stock)
    # Respect demand timing even if total supply would cover the full bucket.
    unserved = max(prearrival_shortfall, demand - stock - arrives, 0.0)
    fulfilled = demand - unserved
    ending = stock + arrives - fulfilled
    return {
        "forecast_daily": daily,
        "on_hand": stock,
        "lead_days": lead,
        "weekly_capacity": capacity,
        "safety_stock": float(safety),
        "reorder_point": float(reorder),
        "target_stock": float(target),
        "reorder_required": bool(needs_order),
        "horizon_days": policy.horizon_days,
        "horizon_demand": float(demand),
        "horizon_capacity": float(available),
        "requested_production": float(requested),
        "planned_production": float(planned),
        "deferred_production": float(deferred),
        "arriving_in_horizon": float(arrives),
        "capacity_limited": bool(deferred > 0),
        "prearrival_shortfall": float(prearrival_shortfall),
        "modeled_unserved_units": float(unserved),
        "fulfilled_units": float(fulfilled),
        "projected_ending_stock": float(max(0.0, ending)),
        "production_arrives_after_horizon": bool(planned > 0 and lead > policy.horizon_days),
    }


REQUIRED = {
    "product_id",
    "on_hand",
    "lead_days",
    "weekly_capacity",
    "std_daily_28d",
    "forecast_daily",
    "planning_source",
}


def plan_table(inputs, policy=None):
    missing = REQUIRED - set(inputs.columns)
    if missing:
        raise ValueError(f"Missing planning fields: {sorted(missing)}")
    if (
        inputs.empty
        or inputs.product_id.isna().any()
        or inputs.product_id.astype(str).str.strip().eq("").any()
    ):
        raise ValueError("Nonempty product identifiers and scenario required")
    if inputs.product_id.duplicated().any():
        raise ValueError("One planning row per product required")
    if (
        inputs.planning_source.isna().any()
        or not inputs.planning_source.astype(str).str.contains("SYNTHETIC", case=False).all()
    ):
        raise ValueError("Every scenario must be explicitly labeled SYNTHETIC")

    def optional(row, name):
        value = row.get(name)
        return None if value is None or pd.isna(value) else value

    rows = []
    for row in inputs.to_dict("records"):
        rows.append(
            dict(
                product_id=str(row["product_id"]),
                planning_source=row["planning_source"],
                **plan_product(
                    row["forecast_daily"],
                    row["on_hand"],
                    row["lead_days"],
                    row["weekly_capacity"],
                    row["std_daily_28d"],
                    optional(row, "safety_stock"),
                    optional(row, "reorder_point"),
                    policy,
                ),
            )
        )
    return pd.DataFrame(rows)


def apply_forecasts(inputs, forecasts):
    """Replace demand using an explicit product/daily-forecast CSV, with exact key coverage."""
    if not {"product_id", "forecast_daily"} <= set(forecasts):
        raise ValueError("Forecast CSV requires product_id,forecast_daily")
    if forecasts.product_id.isna().any() or forecasts.product_id.duplicated().any():
        raise ValueError("Unique non-null forecast product keys required")
    if set(inputs.product_id) != set(forecasts.product_id):
        raise ValueError("Forecast product coverage must exactly match the scenario")
    return inputs.drop(columns="forecast_daily", errors="ignore").merge(
        forecasts[["product_id", "forecast_daily"]], on="product_id", validate="one_to_one"
    )


def run(root, inputs_path=None, forecast_path=None, policy=None, output=None):
    root = Path(root)
    policy = policy or Policy()
    source = Path(inputs_path) if inputs_path else root / "data/processed/gold/inventory_risk.csv"
    inputs = pd.read_csv(source, dtype={"product_id": str})
    if inputs_path is None:
        # Gold reorder_point is a derived result, not a user override. Recompute
        # it from the chosen policy. Explicit scenario CSVs may override it.
        inputs = inputs[[column for column in inputs.columns if column in REQUIRED]]
    if forecast_path:
        inputs = apply_forecasts(inputs, pd.read_csv(forecast_path, dtype={"product_id": str}))
    plans = plan_table(inputs, policy)
    out = Path(output) if output else root / "reports/constrained_planning"
    out.mkdir(parents=True, exist_ok=True)
    # Snapshot inputs so a recommendation can be traced to its exact assumptions.
    inputs.to_csv(out / "scenario_inputs.csv", index=False)
    plans.to_csv(out / "production_plan.csv", index=False)
    plans[plans.capacity_limited | (plans.modeled_unserved_units > 0)].to_csv(
        out / "exceptions.csv", index=False
    )
    summary = {
        "policy": asdict(policy),
        "products": len(plans),
        "requested_production": float(plans.requested_production.sum()),
        "planned_production": float(plans.planned_production.sum()),
        "deferred_production": float(plans.deferred_production.sum()),
        "capacity_limited_products": int(plans.capacity_limited.sum()),
        "modeled_unserved_units": float(plans.modeled_unserved_units.sum()),
        "modeled_risk_products": int((plans.modeled_unserved_units > 0).sum()),
        "scope": "SYNTHETIC independent product capacities; uniform forecast demand; lost sales; no shared factory optimization",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False))
    return plans


def main():
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--inputs", type=Path, help="Explicitly labeled synthetic product scenario CSV")
    p.add_argument("--forecasts", type=Path, help="product_id,forecast_daily overrides")
    p.add_argument("--policy", type=Path, help="JSON: horizon_days,review_days,safety_z")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    policy = Policy(**json.loads(args.policy.read_text())) if args.policy else Policy()
    run(args.root, args.inputs, args.forecasts, policy, args.output)


if __name__ == "__main__":
    main()
