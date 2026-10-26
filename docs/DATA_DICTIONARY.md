# Data dictionary and lineage
Column-level run types, null presence, grain and lineage:
[data_dictionary.csv](../reports/data_dictionary.csv).

| Table | Grain | Origin | Validation |
|---|---|---|---|
| Bronze | original source row | subset CSV, raw string fields + SHA/file/time/version | exact header contract |
| Silver | accepted source row | Bronze + date, units, product_id, price | 8 rule families; raw partition reconciliation |
| Rejected | rejected source row | Bronze + semicolon-separated reasons | every rejected row kept; reasons may overlap |
| product_master | product | distinct Silver product_id, min description | unique ID, no null description |
| daily_demand | product/calendar day | sum Silver quantities, dense zero-filled calendar | unique key, positive/zero units, matches Silver sum |
| weekly_demand | product/Monday week | daily_demand sum | total equals daily; edge weeks partial |
| date_dimension | calendar day | fixed 365-day reporting window | unique continuous dates |
| forecast_results | product/fold/model/target day | daily sales and training-only features | train_end < target; 14 targets/fold/model |
| future_forecast | product/future day | full history seasonal-naive | 14 days after last observation |
| inventory_risk | product/scenario snapshot | recent daily stats + synthetic inputs + future forecast | positive capacity/lead; formula controls |
| product_forecast_scores | product/model | pooled evaluation targets | 42 targets per product/model |

units/actual/predicted/absolute_error/signed_error/reorder_point/on_hand are product
units. days_cover/lead_days are days. weekly_capacity is units/week.
wape/bias/demand_cv/wow_change/planned_utilization are dimensionless ratios.
fold is 1..3, model identifies the method, train_end is last date visible to model,
as_of is snapshot date, date is observation or target date. Source UnitPrice is GBP
per unit but is only validated, never used for cost or turnover claims.
Inventory financial value, supplier performance and factory throughput are unavailable.
