-- Empty results are expected for each diagnostic.
SELECT product_id, date, count(*) FROM demand GROUP BY ALL HAVING count(*) <> 1;
SELECT product_id, fold, model, date, count(*) FROM forecasts GROUP BY ALL HAVING count(*) <> 1;
SELECT * FROM forecasts WHERE train_end >= date OR predicted < 0 OR actual < 0;
SELECT * FROM inventory WHERE days_cover < 0 OR lead_days <= 0 OR weekly_capacity <= 0;

