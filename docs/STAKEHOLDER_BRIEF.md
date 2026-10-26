# Hypothetical planner brief
**Practice deliverable, not presented to Danfoss or real customers.**

The synthetic scenario flags 8 of 20 products below
reorder threshold and 4 above 60 days of cover.
Open Inventory Risk and compare stock, lead time, daily forecast and safety stock
before deciding whether to place an order. These flags describe assumptions, not
actual inventory shortages. There are no receipts or open purchase orders in this data.

Ridge has the lowest pooled holdout WAPE (76.64%), compared with seasonal-naive
(99.06%). However it underforecasts by 31.55%
of actual units in aggregate. A planner relying on these forecasts alone could order
too little. High errors justify manual review and additional data, not automated orders.

Monitor WAPE, bias, cover, reorder thresholds, exceptions and planned utilization.
Review high-error products in reports/high_error_products.csv. The run's source
quality issues include cancellations/negative quantities, duplicate lines, prices,
missing descriptions and deliberately excluded December dates. Reason counts overlap.
All 14 independent KPI checks agree. That validates arithmetic, not the suitability
of scenario assumptions. Real lead times, shared capacity, stock records and service
targets require human confirmation. Forecast-error reduction is not business savings.
