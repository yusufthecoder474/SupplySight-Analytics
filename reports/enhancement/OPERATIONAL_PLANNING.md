# Synthetic operational planning scenario

{
  "products": 20,
  "capacity_shortfall_products": 5,
  "lead_time_stock_risk_products": 6,
  "reorder_required_products": 8,
  "exceptions": 10,
  "weekly_demand": 11238.0,
  "weekly_capacity": 14110.0
}

Existing seed-52316 scenario inputs are reused. Capacity is modeled units/week, not measured utilization. Weekly demand = prespecified seasonal-naive daily forecast ×7. Cover uses forecast daily units, whereas historical_days_cover retains the original 28-day mean denominator. Lead-time risk compares on-hand with forecast daily demand × lead days. Reorder threshold adds 1.65 × historical daily standard deviation × sqrt(lead days); constant demand/independent daily variability is assumed. Equality at capacity or threshold does not flag. No purchase orders, inbound receipts, shared machines, yield loss, calendars or observed stock-outs are modeled. Products with zero forecast have undefined cover. Prioritize lead-time shortfalls, review capacity exceptions, and validate scenario inputs before any real decision.
