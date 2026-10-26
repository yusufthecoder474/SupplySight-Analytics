-- DuckDB: execute from project root after the pipeline. No external database required.
CREATE OR REPLACE VIEW demand AS SELECT * FROM read_csv_auto('data/processed/gold/daily_demand.csv');
CREATE OR REPLACE VIEW forecasts AS SELECT * FROM read_csv_auto('data/processed/gold/forecast_results.csv');
CREATE OR REPLACE VIEW inventory AS SELECT * FROM read_csv_auto('data/processed/gold/inventory_risk.csv');
SELECT sum(units) AS total_demand, count(DISTINCT product_id) AS products FROM demand;
SELECT model, avg(abs(predicted-actual)) AS mae,
  sum(abs(predicted-actual))/nullif(sum(actual),0) AS wape,
  sum(predicted-actual)/nullif(sum(actual),0) AS bias FROM forecasts GROUP BY model;
SELECT count(*) FILTER(WHERE stock_risk) AS at_risk_synthetic,
  count(*) FILTER(WHERE overstock) AS overstock_synthetic,
  avg(days_cover) AS mean_days_cover,
  sum(forecast_daily*7)/nullif(sum(weekly_capacity),0) AS planned_utilization
FROM inventory;

