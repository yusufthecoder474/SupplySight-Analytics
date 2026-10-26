# Executed forecasting comparison

```csv
model,mae,wape,bias,mape_nonzero_only,absolute_error,actual_units,zero_days,zero_day_forecast_units,underforecast_units
croston_sba,60.09442115810038,0.8291608701183364,-0.18287523324647492,1.8972609437869672,50479.31377280432,60880.0,137,7700.065751125519,30806.378986424854
naive,67.06428571428572,0.9253285151116951,-0.11879106438896189,1.8365856339200712,56334.0,60880.0,137,7855.0,31783.0
ridge,55.54788244192644,0.76642938980319,-0.3154998461555157,1.7714268582420256,46660.22125121821,60880.0,137,3192.9579450513083,32933.925942583
seasonal_naive,71.79523809523809,0.990604467805519,-0.09471090670170827,2.1538398311291385,60308.0,60880.0,137,716.0,33037.0
```

All methods use 3 expanding origins × 14 days × 20 products (840 actual targets per method). No parameter tuning or product exclusion. WAPE is pooled absolute error / pooled actual demand; undefined for all-zero groups. Bias is signed error / actual demand; negative means underforecasting. MAE includes zero-demand days.

Volume tertiles and ADI/CV² patterns use only the first training prefix. ADI ≥1.32 and nonzero CV² ≥0.49 are descriptive conventional cutoffs, not fitted. Croston assumes stable arrival intervals and positive-demand sizes; SBA may lag trend or obsolescence. Ridge is recursive and may underforecast spikes. Sales are a demand proxy; absent records are assumed zero. These reused historical periods are not a new untouched holdout. A prospective holdout is pending. Product deltas report every improvement and deterioration against seasonal naive. Negative deltas are improvements. No causal or factory outcome is claimed.
