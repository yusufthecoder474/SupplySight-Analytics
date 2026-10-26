import numpy as np


def errors(actual, predicted):
    a, p = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    if (
        a.shape != p.shape
        or not len(a)
        or not np.isfinite(a).all()
        or not np.isfinite(p).all()
        or (a < 0).any()
    ):
        raise ValueError("Finite, aligned, nonempty nonnegative actuals required")
    total = a.sum()
    nz = a != 0
    return {
        "mae": float(np.abs(p - a).mean()),
        "wape": float(np.abs(p - a).sum() / total) if total else None,
        "bias": float((p - a).sum() / total) if total else None,
        "mape_nonzero_only": float(np.mean(np.abs((p[nz] - a[nz]) / a[nz]))) if nz.any() else None,
        "absolute_error": float(np.abs(p - a).sum()),
        "actual_units": float(total),
    }
