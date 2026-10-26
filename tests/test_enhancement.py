import numpy as np
import pandas as pd
import pytest
from supplysight.study import croston_sba,segments
from supplysight.capacity import capacity_metrics
from supplysight.forecasting import predict


def test_croston_hand_calculation():
    # size=10; first interval=1; next positive arrives 2 days later -> interval=1.1
    assert croston_sba([10,0,10],2).tolist()==pytest.approx([.95*10/1.1]*2)


def test_croston_zero_and_constant():
    assert not croston_sba([0]*40,14).any()
    assert croston_sba([10]*40,14)==pytest.approx([9.5]*14)

@pytest.mark.parametrize("values",[[-1],[float("nan")],[]])
def test_croston_invalid(values):
    with pytest.raises(ValueError):croston_sba(values,2)


def test_capacity_hand_calculation():
    r=capacity_metrics(10,50,30,4,2)
    assert r["weekly_expected_demand"]==70
    assert r["demand_capacity_ratio"]==1.4
    assert r["shortfall_units"]==20
    assert r["lead_time_demand"]==40
    assert r["forecast_days_cover"]==3
    assert r["reorder_threshold"]==46.6
    assert r["capacity_shortfall"] and r["lead_time_stock_risk"] and r["reorder_required"]


def test_capacity_equal_and_zero():
    r=capacity_metrics(10,70,40,4,0)
    assert not r["capacity_shortfall"] and not r["reorder_required"] and not r["lead_time_stock_risk"]
    r=capacity_metrics(0,70,0,4,0)
    assert r["forecast_days_cover"] is None
    assert not r["reorder_required"]

@pytest.mark.parametrize("args",[(1,0,1,1,1),(1,1,1,0,1),(-1,1,1,1,1),(1,1,float("nan"),1,1)])
def test_capacity_invalid(args):
    with pytest.raises(ValueError):capacity_metrics(*args)


def test_segmentation_never_reads_holdout():
    g=pd.DataFrame(dict(product_id=["x"]*100,date=pd.date_range("2020-01-01",periods=100),units=np.arange(100)))
    before=segments(g)
    g.loc[58:,"units"]=999999
    pd.testing.assert_frame_equal(before,segments(g))


def test_recursive_forecast_ignores_future_actuals():
    g=pd.DataFrame(dict(date=pd.date_range("2020-01-01",periods=100),units=np.arange(100)%13))
    train=g.iloc[:80].copy();dates=list(g.date.iloc[80:94])
    before=predict(train,dates,"ridge")
    g.loc[80:,"units"]=999999
    np.testing.assert_array_equal(before,predict(train,dates,"ridge"))


def test_study_target_equivalence_and_original_baselines():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    out=pd.read_csv(root/"reports/enhancement/predictions.csv")
    counts=out.groupby(["product_id","fold","date"]).agg(models=("model","nunique"),actuals=("actual","nunique"))
    assert len(counts)==840 and (counts.models==4).all() and (counts.actuals==1).all()
    assert (pd.to_datetime(out.date)>pd.to_datetime(out.train_end)).all()
    original=pd.read_csv(root/"reports/archive/original/forecast_comparison.csv").set_index("model")
    enhanced=pd.read_csv(root/"reports/enhancement/pooled_scores.csv").set_index("model")
    for model in original.index:
        for metric in ["wape","mae","bias"]:
            assert enhanced.loc[model,metric]==pytest.approx(original.loc[model,metric])


def test_capacity_outputs_match_legacy_reorder_points():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    old=pd.read_csv(root/"data/processed/gold/inventory_risk.csv").set_index("product_id")
    new=pd.read_csv(root/"reports/enhancement/capacity_planning.csv").set_index("product_id")
    np.testing.assert_allclose(old.reorder_point,new.reorder_threshold)
    np.testing.assert_allclose(new.demand_capacity_ratio,new.weekly_expected_demand/new.weekly_capacity,rtol=1e-12)
