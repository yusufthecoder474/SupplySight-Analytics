# Dimensional model
| One side | Many side | Key | Direction |
|---|---|---|---|
| Product | Demand | product_id | single, Product→Demand |
| Product | Forecast | product_id | single, Product→Forecast |
| Product | Inventory | product_id | single, Product→Inventory |
| Date | Demand | date | single, Date→Demand |
| Date | Forecast | date | single, Date→Forecast |

Product and Date must have unique non-null keys. Mark Date as a date table.
Inventory is a fixed November 30 scenario, filtered by Product only. Its as_of
date is not an active relationship: historical date slicers must not silently turn
the scenario on/off. Label this snapshot explicitly and disable date-slicer interactions
with inventory cards if necessary. No bidirectional relationships or fact-to-fact joins.
Product categories are unavailable; drill down by product_id and description only.

Forecast has three model rows per product-target day; never sum raw actual across
models. Use authored measures with a single model selection, default seasonal_naive.
Train-end/fold belong to the forecast fact, not the Date dimension relationship.
Future forecast dates exceed the historical Date range. Future forecast is a
separate export, excluded from this model unless Date is extended appropriately.

Format counts as integers, units to 0–1 decimals, ratios as 0.0%, dates dd-mmm-yyyy.
On-hand units are additive across products but never across snapshot dates.
Days cover is a labeled unweighted mean, not a total; capacity is a ratio of sums.
Demand CV is meaningful for a single product; restrict that visual to one product.
