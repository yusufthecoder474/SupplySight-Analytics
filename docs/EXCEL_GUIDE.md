# Excel usage and verification
Open excel/SupplySight_Operations_Analysis.xlsx in Excel Desktop. Seven sheets:
Executive Summary, Inventory Risk, Forecast Results, Product Master, Demand History,
KPI Validation and Data Dictionary. The chart and formulas are editable.

Inventory Risk uses editable scenario inputs in E:H, historical means/std in C:D,
and formula-derived cover, reorder point, numeric risk flag (1/0), overstock (1/0),
utilization and variability in I:N. Description in Q uses XLOOKUP (modern Excel).
Forecast error formulas are H:I on Forecast Results. KPI Validation D:E computes
difference/pass from independently generated reference and SQL values. Small
floating errors are acceptable below 1e-6; false checks need investigation.
The terminal validation sheet does not feed business summary formulas.

Artifact Tool recalculation and a stock-input mutation were executed. All seven
sheets were rendered and reviewed. Previews are Artifact Tool renders, not screenshots
of Excel Desktop. openpyxl is used only to inspect the saved XLSX, not to author it.
Native Excel, PivotTables, Power Query refresh and COM automation are NOT VERIFIED.

To refresh using Excel, close it and run scripts/Refresh-Workbook.ps1 after pipeline.
It preserves formulas and checks the 20-product / 365-day template row counts.
If inputs/shapes change, rebuild rather than truncate. The included build_workbook.mjs
requires @oai/artifact-tool in its supported authoring runtime.

Manual PivotTable: select Demand History table → Insert → PivotTable → New Worksheet.
Rows: product_id; Columns: date grouped by month; Values: sum of units. Reconcile
Grand Total to Executive Summary B6. Do not sum ratios or forecast actuals across models.
For Power Query: Data → Get Data → From Text/CSV → daily_demand.csv; set product_id
to Text, date to Date and units to Decimal Number → Close & Load. Refresh All after
rerunning the pipeline and compare totals. These are manual instructions, not completed features.
