"""Run study and capacity first, then regenerate the executed workbook snapshot input."""
from pathlib import Path
import json
import pandas as pd

root=Path(__file__).resolve().parents[1]
out=root/"reports/enhancement"
f=pd.read_csv(out/"predictions.csv");f=f[f.fold==3]
a=f[f.model=="naive"].groupby("date").actual.sum()
g=f.groupby(["date","model"]).predicted.sum().unstack();g.insert(0,"actual",a)
payload={"pooled":pd.read_csv(out/"pooled_scores.csv").to_dict("records"),"product":pd.read_csv(out/"product_scores.csv").to_dict("records"),"forecast":g.reset_index().to_dict("records")}
(out/"workbook_enhancement.json").write_text(json.dumps(payload))
