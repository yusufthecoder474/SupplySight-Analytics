import numpy as np
import pandas as pd

from .config import SEED


def inventory_metrics(mean, std, stock, lead, capacity, future_daily):
    values = [mean, std, stock, lead, capacity, future_daily]
    if any(pd.isna(x) for x in values):
        return {
            "days_cover": None,
            "reorder_point": None,
            "stock_risk": None,
            "overstock": None,
            "planned_utilization": None,
        }
    if min(values) < 0 or lead == 0 or capacity == 0:
        raise ValueError("Nonnegative planning values, positive lead time/capacity required")
    safety = 1.65 * std * np.sqrt(lead)
    reorder = future_daily * lead + safety
    return {
        "days_cover": stock / mean if mean else None,
        "reorder_point": reorder,
        "stock_risk": bool(stock < reorder),
        "overstock": bool(mean > 0 and stock / mean > 60),
        "planned_utilization": future_daily * 7 / capacity,
    }


def planning(daily, future):
    rng = np.random.default_rng(SEED)
    rows = []
    for product, g in daily.groupby("product_id", sort=True):
        recent = g.sort_values("date").tail(28)
        mean, std = float(recent.units.mean()), float(recent.units.std(ddof=0))
        lead = int(rng.integers(5, 22))
        stock = float(round(mean * rng.uniform(2, 85)))
        capacity = float(max(1, round(mean * 7 * rng.uniform(0.65, 1.5))))
        fd = float(future[future.product_id == product].predicted.mean())
        rows.append(
            {
                "product_id": product,
                "as_of": g.date.max(),
                "mean_daily_28d": mean,
                "std_daily_28d": std,
                "on_hand": stock,
                "lead_days": lead,
                "weekly_capacity": capacity,
                "forecast_daily": fd,
                **inventory_metrics(mean, std, stock, lead, capacity, fd),
                "demand_cv": std / mean if mean else None,
                "wow_change": float(
                    recent.units.iloc[-7:].sum() / recent.units.iloc[-14:-7].sum() - 1
                )
                if recent.units.iloc[-14:-7].sum()
                else None,
                "planning_source": "SYNTHETIC scenario; seed 52316; not observed inventory",
            }
        )
    return pd.DataFrame(rows)
