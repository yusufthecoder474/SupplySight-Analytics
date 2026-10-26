import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .config import FOLDS, HORIZON
from .metrics import errors

MODELS = ("naive", "seasonal_naive", "ridge")


def features(history, date):
    return [
        history[-1],
        history[-7],
        history[-14],
        np.mean(history[-7:]),
        np.mean(history[-28:]),
        np.sin(2 * np.pi * date.dayofweek / 7),
        np.cos(2 * np.pi * date.dayofweek / 7),
    ]


def predict(train, dates, model):
    y = train.units.to_numpy(dtype=float)
    if len(y) < 35 or model not in MODELS:
        raise ValueError("At least 35 training days and a known model required")
    if len(dates) and pd.Timestamp(dates[0]) <= train.date.max():
        raise ValueError("Forecast dates must follow training")
    if model == "naive":
        return np.repeat(y[-1], len(dates))
    if model == "seasonal_naive":
        return np.resize(y[-7:], len(dates))
    x = [features(y[:i], d) for i, d in enumerate(train.date) if i >= 28]
    reg = make_pipeline(StandardScaler(), Ridge(alpha=10)).fit(x, y[28:])
    history = y.tolist()
    predictions = []
    for d in dates:
        p = max(0.0, float(reg.predict([features(history, d)])[0]))
        predictions.append(p)
        history.append(p)  # Recursive predictions, never future actuals.
    return np.array(predictions)


def backtest(daily):
    result = []
    for product, group in daily.groupby("product_id", sort=True):
        g = group.sort_values("date").reset_index(drop=True)
        if g.date.duplicated().any() or not g.date.diff().dropna().eq(pd.Timedelta(days=1)).all():
            raise ValueError("Daily regular unique series required")
        if len(g) < 35 + FOLDS * HORIZON:
            raise ValueError("Insufficient history for backtest")
        for fold in range(FOLDS):
            cut = len(g) - (FOLDS - fold) * HORIZON
            train, test = g.iloc[:cut], g.iloc[cut : cut + HORIZON]
            for model in MODELS:
                predicted = predict(train, test.date.tolist(), model)
                for d, actual, p in zip(test.date, test.units, predicted):
                    result.append(
                        [product, fold + 1, train.date.max(), d, model, float(actual), float(p)]
                    )
    out = pd.DataFrame(
        result, columns=["product_id", "fold", "train_end", "date", "model", "actual", "predicted"]
    )
    out["absolute_error"] = (out.predicted - out.actual).abs()
    out["signed_error"] = out.predicted - out.actual
    summaries = [{"model": m, **errors(g.actual, g.predicted)} for m, g in out.groupby("model")]
    product_scores = [
        {"product_id": p, "model": m, **errors(g.actual, g.predicted)}
        for (p, m), g in out.groupby(["product_id", "model"])
    ]
    return out, pd.DataFrame(summaries), pd.DataFrame(product_scores)


def future(daily, model="seasonal_naive"):
    rows = []
    for product, g in daily.groupby("product_id", sort=True):
        g = g.sort_values("date")
        dates = pd.date_range(g.date.max() + pd.Timedelta(days=1), periods=HORIZON)
        for d, p in zip(dates, predict(g, dates, model)):
            rows.append([product, g.date.max(), d, model, p])
    return pd.DataFrame(rows, columns=["product_id", "as_of", "date", "model", "predicted"])
