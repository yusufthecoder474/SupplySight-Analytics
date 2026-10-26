# Stale notebook log resolution

The supplied reports/notebooks_local.log logged bronze_rows=26,058 in notebook 01 but later raw_records=52,116, accepted=24,258 and rejected=27,858. The final supplied reports/evaluation.json and pipeline_final.log use 26,058 /24,258 /1,800. Both reports were archived unchanged in reports/archive/original. The original log remains at its original path and is HISTORICAL, not the enhancement run.

The prior verification.md documents retained legacy Spark part files on the prior virtual filesystem, and storage.py already contained a fresh staging path and stable data.parquet replacement repair. The totals are consistent with a duplicated raw partition: 52,116 =2×26,058 and the excess rejects are 26,058. This is a supported diagnosis from prior evidence, not a newly reproduced host bug.

This task executed the CLI in /tmp/supplysight-clean and all five notebooks in a separate /tmp/supplysight-notebooks, each beginning with only the unchanged raw source. Both fresh runs report 26,058 raw, 24,258 accepted, 1,800 rejected, 350,997 units and 14 reconciled KPIs. No raw records were removed or corrected. The existing stale-output replacement test remains in the suite.

Current notebook evidence: reports/enhancement/notebooks_clean.log and clean_notebook_evaluation.json. Current CLI evidence: pipeline_clean.log and clean_pipeline_evaluation.json. Runtime JSONL is included. Notebook 05 now checks the expected dataset-specific counts as well as arithmetic reconciliation, so a doubled but internally balanced partition fails. Local output replacement continues to be single-writer only.
