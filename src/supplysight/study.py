"""Prespecified comparison on reused historical rolling origins; no holdout tuning."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .forecasting import backtest
from .metrics import errors
from .config import FOLDS, HORIZON


def croston_sba(values, horizon, alpha=0.1):
    """Croston with Syntetos-Boylan adjustment, fixed alpha; nonzero interval starts at 1."""
    y = np.asarray(values, dtype=float)
    if not len(y) or not np.isfinite(y).all() or (y < 0).any() or horizon < 0 or not 0 < alpha <= 1:
        raise ValueError("Nonnegative finite demand, horizon and valid alpha required")
    nz = np.flatnonzero(y > 0)
    if not len(nz):
        return np.zeros(horizon)
    first = int(nz[0])
    size, interval, elapsed = y[first], float(first + 1), 1
    for value in y[first + 1:]:
        if value > 0:
            size += alpha * (value - size)
            interval += alpha * (elapsed - interval)
            elapsed = 1
        else:
            elapsed += 1
    return np.repeat((1-alpha/2) * size/interval, horizon)


def segments(daily):
    rows = []
    for p, g in daily.groupby("product_id", sort=True):
        y = g.sort_values("date").units.to_numpy()[:-(FOLDS*HORIZON)]
        nz = y[y > 0]
        adi = len(y)/len(nz) if len(nz) else None
        cv2 = float((nz.std()/nz.mean())**2) if len(nz) else None
        pattern = "all_zero" if not len(nz) else ("lumpy" if adi >= 1.32 and cv2 >= .49 else "intermittent" if adi >= 1.32 else "erratic" if cv2 >= .49 else "smooth")
        rows.append(dict(product_id=p, training_units=float(y.sum()), training_days=len(y), zero_share=float((y==0).mean()), adi=adi, nonzero_cv2=cv2, demand_pattern=pattern))
    out = pd.DataFrame(rows)
    lo, hi = out.training_units.quantile([1/3,2/3])
    out["volume_segment"] = np.where(out.training_units <= lo, "low", np.where(out.training_units <= hi, "medium", "high"))
    out["low_cut_units"], out["high_cut_units"] = lo, hi
    return out


def run(root, output=None):
    root = Path(root)
    output = Path(output) if output else root/"reports/enhancement"
    output.mkdir(parents=True, exist_ok=True)
    source = root/"data/processed/gold/daily_demand.csv"
    daily = pd.read_csv(source, dtype={"product_id":str}, parse_dates=["date"])
    if daily.duplicated(["product_id","date"]).any() or daily.units.isna().any() or (daily.units < 0).any():
        raise ValueError("Unique finite nonnegative daily series required")
    manifest = dict(protocol="Fixed before this execution; historical test dates were evaluated previously", source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), models=["naive","seasonal_naive","ridge","croston_sba"], alpha=.1, folds=FOLDS, horizon=HORIZON, segmentation="initial training prefix only, volume tertiles", future_selection="No selection; planning retains seasonal_naive")
    (output/"protocol.json").write_text(json.dumps(manifest, indent=2))
    baseline, _, _ = backtest(daily)
    rows=[]
    for p,g in daily.groupby("product_id", sort=True):
        g=g.sort_values("date").reset_index(drop=True)
        for fold in range(FOLDS):
            cut=len(g)-(FOLDS-fold)*HORIZON
            train,test=g.iloc[:cut],g.iloc[cut:cut+HORIZON]
            for d,a,pred in zip(test.date,test.units,croston_sba(train.units,HORIZON)):
                rows.append([p,fold+1,train.date.max(),d,"croston_sba",float(a),float(pred)])
    extra=pd.DataFrame(rows,columns=baseline.columns[:7])
    extra["absolute_error"]=(extra.predicted-extra.actual).abs()
    extra["signed_error"]=extra.predicted-extra.actual
    out=pd.concat([baseline,extra],ignore_index=True).merge(segments(daily),on="product_id",validate="many_to_one")
    out.to_csv(output/"predictions.csv",index=False)
    segments(daily).to_csv(output/"demand_segments.csv",index=False)
    def score(keys, filename):
        result=[]
        for key,g in out.groupby(keys):
            key=key if isinstance(key,tuple) else (key,)
            result.append(dict(zip(keys,key),**errors(g.actual,g.predicted), zero_days=int((g.actual==0).sum()), zero_day_forecast_units=float(g.loc[g.actual==0,"predicted"].sum()), underforecast_units=float((g.actual-g.predicted).clip(lower=0).sum())))
        frame=pd.DataFrame(result)
        frame.to_csv(output/filename,index=False)
        return frame
    pooled=score(["model"],"pooled_scores.csv")
    products=score(["product_id","model"],"product_scores.csv")
    score(["volume_segment","model"],"segment_scores.csv")
    score(["demand_pattern","model"],"pattern_scores.csv")
    score(["fold","model"],"fold_scores.csv")
    delta=products.pivot(index="product_id",columns="model",values="wape")
    for model in ["naive","ridge","croston_sba"]:
        delta[model+"_delta_vs_seasonal"]=delta[model]-delta.seasonal_naive
    delta.to_csv(output/"product_deltas.csv")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(5,4,figsize=(20,17))
    for ax,(p,g) in zip(axes.flat,out.groupby("product_id",sort=True)):
        g=g[g.fold==FOLDS]
        a=g[g.model=="naive"]
        ax.plot(a.date,a.actual,color="black",label="actual")
        for m,h in g.groupby("model"):
            ax.plot(h.date,h.predicted,label=m,alpha=.8)
        ax.set_title(str(p));ax.tick_params(axis="x",rotation=40,labelsize=7)
    axes.flat[0].legend(fontsize=7)
    fig.suptitle("All 20 products: actual sales and final-origin forecasts (units)")
    fig.tight_layout();fig.savefig(output/"all_products_forecast.png",dpi=120);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4))
    ax.bar(pooled.model,pooled.wape*100,color="#0d9488");ax.set_ylabel("Pooled WAPE (%)")
    fig.tight_layout();fig.savefig(output/"pooled_wape.png",dpi=150);plt.close(fig)
    (output/"FORECAST_STUDY.md").write_text("# Executed forecasting comparison\n\n"+"```csv\n"+pooled.to_csv(index=False)+"```"+"\n\nAll methods use 3 expanding origins × 14 days × 20 products (840 actual targets per method). No parameter tuning or product exclusion. WAPE is pooled absolute error / pooled actual demand; undefined for all-zero groups. Bias is signed error / actual demand; negative means underforecasting. MAE includes zero-demand days.\n\nVolume tertiles and ADI/CV² patterns use only the first training prefix. ADI ≥1.32 and nonzero CV² ≥0.49 are descriptive conventional cutoffs, not fitted. Croston assumes stable arrival intervals and positive-demand sizes; SBA may lag trend or obsolescence. Ridge is recursive and may underforecast spikes. Sales are a demand proxy; absent records are assumed zero. These reused historical periods are not a new untouched holdout. A prospective holdout is pending. Product deltas report every improvement and deterioration against seasonal naive. Negative deltas are improvements. No causal or factory outcome is claimed.\n")
    return out,pooled,products

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument("--output",type=Path)
    a=p.parse_args();run(a.root,a.output)
