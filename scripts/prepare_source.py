"""Download CC BY 4.0 source and retain an auditable product subset, without inventing rows."""

import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path)
    p.add_argument("--products", type=int, default=20)
    args = p.parse_args()
    payload = (
        args.archive.read_bytes()
        if args.archive
        else urllib.request.urlopen(URL, timeout=90).read()
    )
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        df = pd.read_excel(
            io.BytesIO(z.read("Online Retail.xlsx")), dtype={"StockCode": str, "InvoiceNo": str}
        )
    df.insert(0, "source_row_id", range(2, len(df) + 2))
    df["StockCode"] = df.StockCode.str.strip()
    early = df[
        (df.InvoiceDate < "2011-03-01")
        & (df.Quantity > 0)
        & df.StockCode.str.fullmatch(r"\d{5}[A-Za-z]?")
    ]
    # Rank by early transaction frequency, tie-break by identifier; never use holdout sales.
    rank = (
        early.groupby("StockCode")
        .size()
        .rename("n")
        .reset_index()
        .sort_values(["n", "StockCode"], ascending=[False, True])
    )
    ids = rank.head(args.products).StockCode.tolist()
    subset = df[df.StockCode.isin(ids)].copy()
    subset.InvoiceDate = subset.InvoiceDate.dt.strftime("%Y-%m-%d %H:%M:%S")
    out = ROOT / "data/raw/retail_subset.csv"
    subset.to_csv(out, index=False)
    meta = {
        "source": URL,
        "landing_page": "https://archive.ics.uci.edu/dataset/352/online+retail",
        "citation": "Chen, D. (2015). Online Retail. UCI. DOI: 10.24432/C5BW33",
        "license": "CC BY 4.0",
        "archive_sha256": hashlib.sha256(payload).hexdigest(),
        "subset_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "original_rows": len(df),
        "subset_rows": len(subset),
        "product_ids": ids,
        "selection": "Top 20 by line frequency before 2011-03-01, positive quantities, valid product codes; all rows for these products retained. Source row IDs are Excel row numbers.",
        "date_min": str(df.InvoiceDate.min()),
        "date_max": str(df.InvoiceDate.max()),
        "fields": list(subset.columns),
        "modifications": "Subset only; dates serialized ISO; StockCode stripped; source row number added.",
    }
    (ROOT / "data/provenance.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
