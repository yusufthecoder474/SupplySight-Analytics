# Configurable capacity-constrained planning

This extension uses the existing inventory_risk.csv and never overwrites the eight Gold datasets or existing Excel workbook. Its stock, capacity and lead-time inputs are explicit SYNTHETIC assumptions. It does not imply observed factory utilization or stock-outs.

## Reproduce on Windows PowerShell
```powershell
$env:PYTHONPATH = "src"
python -m supplysight.constrained_planning --policy data/synthetic/planning_policy.json
```
Outputs are reports/constrained_planning/scenario_inputs.csv, production_plan.csv, exceptions.csv and summary.json. The first is the exact input snapshot; the others are calculated from it.

To customize, copy scenario_inputs.csv to a new CSV. Keep one row per product, a nonempty product_id and planning_source containing SYNTHETIC. Required columns are product_id,forecast_daily,on_hand,lead_days,weekly_capacity,std_daily_28d,planning_source. Optional safety_stock and reorder_point replace the calculated per-product values. Blank optional overrides use the policy formula. Negative, nonfinite, missing mandatory fields and duplicate product keys fail validation. Zero demand, zero stock, zero lead and zero capacity are supported. A zero-capacity line cannot produce.

A separate forecast CSV may contain product_id,forecast_daily, with exact unique key coverage; it replaces the embedded daily forecast. The scenario can omit forecast_daily when this file supplies it.
```powershell
python -m supplysight.constrained_planning --inputs data/synthetic/my_scenario.csv --forecasts data/synthetic/my_daily_forecasts.csv --policy data/synthetic/planning_policy.json --output reports/my_scenario
```
Policy JSON defines positive integer horizon_days and review_days, plus finite nonnegative safety_z. Included defaults are 7 days, 7 days and 1.65. Keep each scenario in a different output folder. Forecast inputs must be generated at a single declared as-of time; do not use future actuals. The default is the existing prespecified seasonal-naive future forecast.

## Calculation contract
- Safety stock = safety_z × daily demand standard deviation × sqrt(lead days), unless overridden.
- Reorder point = daily forecast × lead days + safety stock, unless overridden.
- Target stock = maximum of the reorder point and daily forecast × (lead + review days) + safety stock.
- Reorder trigger is on_hand < reorder_point, matching the existing strict threshold convention. Equality does not order.
- Requested production = max(target stock − on_hand,0) only when the reorder trigger is active.
- Available horizon capacity = weekly capacity × horizon days /7.
- Planned production = min(requested production,available horizon capacity). Deferred production is the difference. Capacities belong to independent products. There is no shared-machine optimizer.
- All planned production arrives after lead_days; none is available in this horizon if lead_days exceeds horizon_days.
- Prearrival shortage = max(daily forecast × min(lead days,horizon days) − on_hand,0). Demand is assumed uniform.
- Modeled unserved demand is the larger of prearrival shortage and total-horizon demand minus starting stock and in-horizon arrivals, floored at zero. It is a lost-sales exposure, not a measured stock-out or backorder.
- Fulfilled units = horizon demand − modeled unserved units. Ending stock = starting stock + in-horizon arrivals − fulfilled units. This inventory balance is tested.

At lead == horizon, production arrives at the bucket boundary and cannot satisfy demand already missed before arrival; it remains ending stock. Production quantities are continuous units for analysis; no batch size, integer rounding, yield, purchase orders, inbound receipts or working-day calendars are modeled. Safety-stock statistics assume independent daily variability, not a service-level guarantee. A short planning horizon can show fewer immediate risk products than the existing full-lead-time risk module.

## Default scenario results
20 products; requested production 11,757.1561 units; capacity-limited plan 4,638 units; deferred 7,119.1561 units; 8 capacity-limited order recommendations. The seven-day lost-sales model flags 2 products and 349 unserved units. These are synthetic model outputs. The previous module's 5 demand/capacity shortfalls and 6 full-lead-time stock risks measure different conditions and are preserved.

Tests include hand-calculated safety stock/reorder/production/inventory balances, timing boundaries, zero capacity, threshold equality, forecast-key alignment, validation and 100 fixed-seed randomized invariant scenarios. Databricks notebook 04 now runs this same module; notebook 05 checks capacity limits and balances. Actual Databricks execution is pending.
