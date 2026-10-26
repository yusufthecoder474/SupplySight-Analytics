import numpy as np
import pandas as pd
import pytest

from supplysight.forecasting import backtest, predict
from supplysight.metrics import errors


def series():
    return pd.DataFrame(
        {
            "product_id": ["12345"] * 120,
            "date": pd.date_range("2020-01-01", periods=120),
            "units": np.tile(np.arange(1, 8), 18)[:120].astype(float),
        }
    )


def test_metric_hand_calculation():
    r = errors([0, 10, 20], [2, 8, 24])
    assert r["mae"] == pytest.approx(8 / 3)
    assert r["wape"] == pytest.approx(8 / 30)
    assert r["bias"] == pytest.approx(4 / 30)
    assert r["mape_nonzero_only"] == pytest.approx(0.2)


def test_all_zero_metrics():
    r = errors([0, 0], [1, 1])
    assert r["wape"] is None and r["bias"] is None
    assert r["mape_nonzero_only"] is None
    assert r["mae"] == 1


@pytest.mark.parametrize("a,p", [([], []), ([1], [1, 2]), ([float("nan")], [1]), ([-1], [1])])
def test_invalid_metrics(a, p):
    with pytest.raises(ValueError):
        errors(a, p)


@pytest.mark.parametrize("model", ["naive", "seasonal_naive", "ridge"])
def test_horizon_and_reproducibility(model):
    g = series()
    a = predict(g.iloc[:100], g.date.iloc[100:114].tolist(), model)
    assert len(a) == 14
    np.testing.assert_allclose(a, predict(g.iloc[:100], g.date.iloc[100:114].tolist(), model))
    assert (a >= 0).all()


def test_seasonal_baseline_exact_periodic():
    g = series()
    np.testing.assert_allclose(
        predict(g.iloc[:100], g.date.iloc[100:114].tolist(), "seasonal_naive"),
        g.units.iloc[100:114],
    )


def test_train_dates_precede_targets():
    out, _, _ = backtest(series())
    assert (out.train_end < out.date).all()
    assert out.groupby(["fold", "model"]).size().eq(14).all()
    assert not out.duplicated(["product_id", "fold", "date", "model"]).any()


def test_mutating_holdout_cannot_change_same_origin_predictions():
    g = series()
    original, _, _ = backtest(g)
    mutated = g.copy()
    mutated.loc[78:91, "units"] = 99999
    changed, _, _ = backtest(mutated)
    # First origin is day 78. All changed targets must remain invisible to this forecast.
    np.testing.assert_allclose(
        original[original.fold == 1].predicted, changed[changed.fold == 1].predicted
    )


def test_irregular_series_rejected():
    with pytest.raises(ValueError, match="regular"):
        backtest(series().drop(index=40))


def test_short_history_rejected():
    with pytest.raises(ValueError):
        backtest(series().head(40))
