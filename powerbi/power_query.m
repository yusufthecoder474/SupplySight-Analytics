// Create a blank query named GoldRoot, replace its entire contents with:
"C:\SupplySight-Analytics\data\processed\gold"

// Create a second blank query named LoadGold. Replace contents with this function:
(FileName as text, Types as list) as table =>
let
    Raw = Csv.Document(File.Contents(GoldRoot & "\" & FileName),
          [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, Types, "en-US")
in Typed

// Create these individual queries with the indicated names:
// Product
LoadGold("product_master.csv", {{"product_id",type text},{"description",type text}})
// Date
LoadGold("date_dimension.csv", {{"date",type date},{"year",Int64.Type},{"month",Int64.Type},{"week",type date}})
// Demand
LoadGold("daily_demand.csv", {{"product_id",type text},{"date",type date},{"units",type number}})
// Forecast
LoadGold("forecast_results.csv", {{"product_id",type text},{"fold",Int64.Type},{"train_end",type date},{"date",type date},{"model",type text},{"actual",type number},{"predicted",type number},{"absolute_error",type number},{"signed_error",type number}})
// Inventory
LoadGold("inventory_risk.csv", {{"product_id",type text},{"as_of",type date},{"mean_daily_28d",type number},{"std_daily_28d",type number},{"on_hand",type number},{"lead_days",Int64.Type},{"weekly_capacity",type number},{"forecast_daily",type number},{"days_cover",type number},{"reorder_point",type number},{"stock_risk",type logical},{"overstock",type logical},{"planned_utilization",type number},{"demand_cv",type number},{"wow_change",type number}})

