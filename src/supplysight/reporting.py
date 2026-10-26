import json

import duckdb
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .config import FOLDS, HORIZON
from .forecasting import backtest, future
from .inventory import planning


def finish(root, frames, stats):
    keys = {
        "product_master": ["product_id"],
        "daily_demand": ["product_id", "date"],
        "weekly_demand": ["product_id", "week"],
        "date_dimension": ["date"],
    }
    for name, columns in keys.items():
        frames[name] = frames[name].sort_values(columns).reset_index(drop=True)
    daily = frames["daily_demand"]
    daily["date"] = pd.to_datetime(daily.date)
    forecasts, comparison, product_scores = backtest(daily)
    # A prespecified seasonal baseline supplies planning. Evaluation remains an honest holdout,
    # rather than selecting a winning model on the holdout and calling that an unbiased result.
    upcoming = future(daily)
    risk = planning(daily, upcoming)
    frames.update(
        forecast_results=forecasts,
        future_forecast=upcoming,
        inventory_risk=risk,
        product_forecast_scores=product_scores,
    )
    for name, df in frames.items():
        df.to_csv(root / f"data/processed/gold/{name}.csv", index=False)
        if name in (
            "forecast_results",
            "future_forecast",
            "inventory_risk",
            "product_forecast_scores",
        ):
            df.to_parquet(root / f"data/processed/gold/{name}.parquet", index=False)
    risk[
        ["product_id", "as_of", "on_hand", "lead_days", "weekly_capacity", "planning_source"]
    ].to_csv(root / "data/synthetic/planning_inputs.csv", index=False)
    comparison.to_csv(root / "reports/forecast_comparison.csv", index=False)
    product_scores.sort_values("wape", ascending=False).to_csv(
        root / "reports/high_error_products.csv", index=False
    )
    scores = comparison.set_index("model")
    by_product = product_scores.pivot(index="product_id", columns="model", values="absolute_error")
    stats.update(
        {
            "products": int(daily.product_id.nunique()),
            "history_days": int(daily.date.nunique()),
            "history_start": str(daily.date.min().date()),
            "history_end": str(daily.date.max().date()),
            "folds": FOLDS,
            "horizon_days": HORIZON,
            "evaluated_days_per_product": FOLDS * HORIZON,
            "forecast_rows": len(forecasts),
            "gold_datasets": len(frames),
            "model_comparison": comparison.replace({np.nan: None}).to_dict("records"),
            "ridge_improvement_vs_seasonal_wape": float(
                1 - scores.loc["ridge", "wape"] / scores.loc["seasonal_naive", "wape"]
            ),
            "ridge_products_improved_pct": float(
                100 * (by_product.ridge < by_product.seasonal_naive).mean()
            ),
            "planning_model": "seasonal_naive (prespecified)",
            "at_risk_products_synthetic": int(risk.stock_risk.sum()),
            "overstock_products_synthetic": int(risk.overstock.sum()),
            "databricks": "NOT EXECUTED",
            "powerbi_pages_verified": 0,
            "dax_measures_verified": 0,
            "ci": "configured, not executed remotely",
        }
    )
    reconciliation = reconcile(frames, stats)
    reconciliation.to_csv(root / "reports/kpi_reconciliation.csv", index=False)
    assert reconciliation.passed.all(), reconciliation.to_string()
    stats["reconciled_kpis"] = len(reconciliation)
    (root / "reports/evaluation.json").write_text(json.dumps(stats, indent=2, allow_nan=False))
    dictionary = []
    grains = {
        "product_master": "one row/product",
        "daily_demand": "product/day",
        "weekly_demand": "product/week (edge weeks partial)",
        "date_dimension": "one row/calendar day",
        "forecast_results": "product/fold/model/target day",
        "future_forecast": "product/future day",
        "inventory_risk": "product/as-of scenario",
        "product_forecast_scores": "product/model, pooled across folds",
    }
    for name, df in frames.items():
        for col in df.columns:
            dictionary.append(
                {
                    "dataset": name,
                    "grain": grains[name],
                    "column": col,
                    "type": str(df[col].dtype),
                    "nullable_in_run": bool(df[col].isna().any()),
                    "lineage": "SYNTHETIC planning plus historical demand and prespecified forecast"
                    if name == "inventory_risk"
                    else "accepted UCI sales → daily totals → derived analytics",
                }
            )
    dictionary = pd.DataFrame(dictionary)
    dictionary.to_csv(root / "reports/data_dictionary.csv", index=False)
    plots(root, daily, forecasts, comparison, risk)
    # Typed JSON intermediate consumed by the JS workbook builder.
    tables = {
        "Product Master": frames["product_master"],
        "Demand History": daily[["product_id", "date", "units"]],
        "Forecast Results": forecasts,
        "Inventory Risk": risk,
        "KPI Validation": reconciliation,
        "Data Dictionary": dictionary,
    }
    payload = {
        name: {
            "columns": list(df.columns),
            "rows": json.loads(df.to_json(orient="values", date_format="iso")),
        }
        for name, df in tables.items()
    }
    payload["metrics"] = stats
    payload["comparison"] = json.loads(comparison.to_json(orient="values"))
    (root / "reports/workbook_data.json").write_text(json.dumps(payload))


def reconcile(frames, stats):
    con = duckdb.connect()
    for name, df in frames.items():
        con.register(name, df)
    daily, risk = frames["daily_demand"], frames["inventory_risk"]
    checks = [
        ("total_demand", "SELECT sum(units) FROM daily_demand", stats["silver_units"]),
        ("weekly_demand", "SELECT sum(units) FROM weekly_demand", float(daily.units.sum())),
        ("product_count", "SELECT count(*) FROM product_master", daily.product_id.nunique()),
        (
            "risk_count",
            "SELECT count(*) FROM inventory_risk WHERE stock_risk",
            int(risk.stock_risk.sum()),
        ),
        (
            "overstock_count",
            "SELECT count(*) FROM inventory_risk WHERE overstock",
            int(risk.overstock.sum()),
        ),
        (
            "reorder_points",
            "SELECT sum(forecast_daily*lead_days+1.65*std_daily_28d*sqrt(lead_days)) FROM inventory_risk",
            float(risk.reorder_point.sum()),
        ),
        (
            "days_cover",
            "SELECT avg(on_hand/nullif(mean_daily_28d,0)) FROM inventory_risk",
            float(risk.days_cover.mean()),
        ),
        (
            "capacity_utilization",
            "SELECT sum(forecast_daily*7)/sum(weekly_capacity) FROM inventory_risk",
            float((risk.forecast_daily * 7).sum() / risk.weekly_capacity.sum()),
        ),
    ]
    for model in ("naive", "seasonal_naive", "ridge"):
        score = next(s for s in stats["model_comparison"] if s["model"] == model)
        checks += [
            (
                f"{model}_wape",
                f"SELECT sum(abs(predicted-actual))/nullif(sum(actual),0) FROM forecast_results WHERE model='{model}'",
                score["wape"],
            ),
            (
                f"{model}_bias",
                f"SELECT sum(predicted-actual)/nullif(sum(actual),0) FROM forecast_results WHERE model='{model}'",
                score["bias"],
            ),
        ]
    rows = []
    for name, sql, expected in checks:
        actual = float(con.execute(sql).fetchone()[0])
        rows.append(
            {
                "kpi": name,
                "reference": float(expected),
                "duckdb_sql": actual,
                "difference": actual - float(expected),
                "passed": bool(np.isclose(actual, expected, rtol=1e-9, atol=1e-7)),
            }
        )
    con.close()
    return pd.DataFrame(rows)


def plots(root, daily, forecasts, comparison, risk):
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
    target = root / "docs/screenshots"
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(comparison.model, comparison.wape * 100, color=["#64748b", "#0d9488", "#2563eb"])
    ax.set(
        ylabel="WAPE (%) — lower is better",
        title="Measured rolling-origin forecast errors | public retail sales",
    )
    fig.tight_layout()
    fig.savefig(target / "forecast_comparison.png", dpi=150)
    plt.close(fig)
    product = min(daily.product_id.unique())
    g = forecasts[(forecasts.product_id == product) & (forecasts.fold == FOLDS)]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    actual = g[g.model == "naive"]
    ax.plot(actual.date, actual.actual, label="Observed sales", color="#0f172a", linewidth=2)
    for model, color in zip(
        ["naive", "seasonal_naive", "ridge"], ["#94a3b8", "#0d9488", "#2563eb"]
    ):
        m = g[g.model == model]
        ax.plot(m.date, m.predicted, label=model, color=color)
    ax.set(title=f"Product {product} | final 14-day holdout", ylabel="Units sold (demand proxy)")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(target / "actual_vs_forecast.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 5))
    g = risk.sort_values("days_cover")
    ax.bar(g.product_id, g.days_cover, color=["#dc2626" if x else "#0d9488" for x in g.stock_risk])
    ax.axhline(60, color="#64748b", linestyle="--", label="Overstock threshold: >60 days")
    ax.set(
        title="SYNTHETIC inventory scenario | red = below modeled reorder point",
        ylabel="Days of cover",
    )
    ax.tick_params(axis="x", rotation=60)
    ax.legend()
    fig.tight_layout()
    fig.savefig(target / "inventory_scenario.png", dpi=150)
    plt.close(fig)
