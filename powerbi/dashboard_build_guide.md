# Power BI Desktop build and acceptance
1. Blank report → Transform Data → create GoldRoot text query and LoadGold function
   by copying individual sections of power_query.m. Do not paste the whole file as
   one query. Create Product, Date, Demand, Forecast, Inventory from the named calls.
   Disable load for GoldRoot/LoadGold. Verify dates, numbers and true/false types.
2. Apply changes, create relationships from model_specification.md, mark Date.
3. Create each DAX measure separately, import theme.json, make three 16:9 pages.
4. Save a real SupplySight.pbix and reopen it. Only then record PBIX completion.

| Page | Visuals and interaction |
|---|---|
| Executive Operations Overview | cards Total Demand, Products Monitored, At Risk Products, Forecast WAPE; monthly demand line; exception table; Date and Product slicers; Model single-select |
| Inventory Health & Capacity | risk table with stock/reorder/cover; product cover bars; overstock filter; planned capacity bars; Product drill-through; fixed synthetic as-of label |
| Demand Forecast & Variance | Actual vs Forecast line using measures, not raw actual; model WAPE/MAE/bias table; high-error product table; Product, Date and single-select Model slicers |

Navy #17324D, slate #64748B, teal #0D9488, blue #2563EB, white background.
Red highlights risk only. All inventory/capacity visuals say SYNTHETIC.
Forecast tooltip includes model, train_end, fold, actual, predicted and error.
Demand trend covers historical reporting window; forecast trend covers the held-out
42 days. Model comparison table uses Forecast[model] rows; chosen-model measures
resolve per row. In a date/product subset, WAPE recomputes pooled numerator and denominator.
Week-change measure compares equally sized date windows; use full weeks for weekly decisions.

Acceptance controls with all filters cleared:
- Total Demand = 350,997; Products Monitored = 20.
- Scenario at-risk = 8; overstock = 4.
- WAPE by model: naive 92.532852%, seasonal-naive 99.060447%, ridge 76.642939%.
- Compare MAE, bias and capacity controls to reports/kpi_reconciliation.csv (tolerance 1e-6).
- Single-product filter must affect all facts through Product. Date filters affect
  sales/forecast but not the fixed inventory scenario. Confirm this visually.
- Do not display zero error when selected actual total is zero: DIVIDE returns blank.
- With model slicer cleared, default seasonal-naive prevents triple-counting actuals.
Capture each page from actual Desktop only after these checks. All these native
acceptance actions remain pending; there is no PBIX or Power BI screenshot here.
