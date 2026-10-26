# KPI definitions
Sales mean accepted positive transaction quantities, not unconstrained demand.
All inventory/capacity fields are synthetic and as of 2011-11-30.

| KPI | Formula / grain / time window | Null and aggregation policy | Interpretation |
|---|---|---|---|
| Total demand | sum units; product/day, 365 days | zero-filled dates; additive across products/dates | sales proxy units |
| Demand variability | population std / mean; product, last 28 days | null when mean zero; do not sum CVs | recent relative variability |
| MAE | sum absolute error / target rows; model, 3×14 days/product | finite aligned rows only | units error per product-day |
| WAPE | sum absolute error / sum actual; model, same holdout | null if actual total zero; pool numerators/denominators | volume-weighted error |
| Bias | sum(predicted−actual) / sum actual | null if total zero; pooled by model | negative = underforecast |
| Days cover | on_hand / last-28-day mean; product/snapshot | null if mean zero or missing stock; average only labeled mean | stock duration under recent sales |
| Safety stock | 1.65 × population std daily × sqrt(lead days) | null for missing planning fields | approximate scenario buffer |
| Reorder point | future-14-day mean × lead days + safety stock | null if inputs missing; sum units across products only for overview | proposed review threshold |
| Stock risk | on_hand < reorder point; product/snapshot | null if inputs missing; equality is not risk | scenario review, not observed stockout |
| Overstock | cover >60 days | false for zero demand; inspect zero-demand stock separately | excessive cover under assumed demand |
| Planned utilization | forecast daily ×7 / weekly_capacity | null if missing; zero capacity invalid; aggregate ratio of sums | scenario unit capacity, not factory actuals |
| WoW demand change | latest 7-day units / preceding 7-day units −1 | null when previous 7 days zero; product as-of | recent sales change |
| Forecast value added | 1 − challenger WAPE / baseline WAPE | same rows and horizon; undefined if baseline error zero | relative error reduction, not savings |

No lead-time variation KPI: only one synthetic lead-time assumption per product.
No inventory turnover/value KPI: no valid observed stock history or cost basis.
MAPE is diagnostic on nonzero actual periods only and cannot represent zero-demand performance.
