"""Capacity and lead-time exceptions for the existing deterministic planning scenario."""
import json
from pathlib import Path
import numpy as np
import pandas as pd


def capacity_metrics(daily, capacity, stock, lead, std):
    vals=np.array([daily,capacity,stock,lead,std],dtype=float)
    if not np.isfinite(vals).all() or (vals<0).any() or capacity==0 or lead==0:
        raise ValueError("Finite nonnegative values and positive capacity/lead required")
    weekly=daily*7
    lead_demand=daily*lead
    reorder=lead_demand+1.65*std*np.sqrt(lead)
    return dict(weekly_expected_demand=weekly, demand_capacity_ratio=weekly/capacity, capacity_shortfall=bool(weekly>capacity), shortfall_units=max(0.,weekly-capacity), lead_time_demand=lead_demand, lead_time_stock_risk=bool(stock<lead_demand), forecast_days_cover=stock/daily if daily else None, reorder_threshold=reorder, reorder_required=bool(stock<reorder))


def run(root):
    root=Path(root);out=root/"reports/enhancement";out.mkdir(parents=True,exist_ok=True)
    risk=pd.read_csv(root/"data/processed/gold/inventory_risk.csv",dtype={"product_id":str})
    rows=[]
    for r in risk.itertuples():
        rows.append(dict(product_id=r.product_id,as_of=r.as_of,forecast_daily=r.forecast_daily,weekly_capacity=r.weekly_capacity,on_hand=r.on_hand,lead_days=r.lead_days,std_daily_28d=r.std_daily_28d,historical_days_cover=r.days_cover,**capacity_metrics(r.forecast_daily,r.weekly_capacity,r.on_hand,r.lead_days,r.std_daily_28d),planning_source=r.planning_source))
    table=pd.DataFrame(rows)
    table["exception"]=table.capacity_shortfall|table.lead_time_stock_risk|table.reorder_required
    table.to_csv(out/"capacity_planning.csv",index=False)
    table[table.exception].to_csv(out/"planning_exceptions.csv",index=False)
    assert np.allclose(table.reorder_threshold,risk.reorder_point)
    scenario=table[["product_id","as_of","on_hand","lead_days","weekly_capacity","planning_source"]]
    scenario.to_csv(out/"synthetic_planning_inputs.csv",index=False)
    report=dict(products=len(table),capacity_shortfall_products=int(table.capacity_shortfall.sum()),lead_time_stock_risk_products=int(table.lead_time_stock_risk.sum()),reorder_required_products=int(table.reorder_required.sum()),exceptions=int(table.exception.sum()),weekly_demand=float(table.weekly_expected_demand.sum()),weekly_capacity=float(table.weekly_capacity.sum()))
    (out/"planning_summary.json").write_text(json.dumps(report,indent=2))
    (out/"OPERATIONAL_PLANNING.md").write_text("# Synthetic operational planning scenario\n\n"+json.dumps(report,indent=2)+"\n\nExisting seed-52316 scenario inputs are reused. Capacity is modeled units/week, not measured utilization. Weekly demand = prespecified seasonal-naive daily forecast ×7. Cover uses forecast daily units, whereas historical_days_cover retains the original 28-day mean denominator. Lead-time risk compares on-hand with forecast daily demand × lead days. Reorder threshold adds 1.65 × historical daily standard deviation × sqrt(lead days); constant demand/independent daily variability is assumed. Equality at capacity or threshold does not flag. No purchase orders, inbound receipts, shared machines, yield loss, calendars or observed stock-outs are modeled. Products with zero forecast have undefined cover. Prioritize lead-time shortfalls, review capacity exceptions, and validate scenario inputs before any real decision.\n")
    return table

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]);run(p.parse_args().root)
