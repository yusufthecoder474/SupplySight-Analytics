"""Client-side notebook logs; never imply server-side Spark logs are available."""
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError


def record_runtime(root, notebook, spark, environment, elapsed_seconds=None):
    packages={}
    for name in ["pandas","numpy","scikit-learn","duckdb","pyarrow"]:
        try:packages[name]=version(name)
        except PackageNotFoundError:packages[name]="unavailable"
    row=dict(elapsed_seconds=elapsed_seconds,notebook=notebook,environment=environment,utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),spark=spark.version if spark is not None else None,packages=packages)
    folder=root/"reports";folder.mkdir(parents=True,exist_ok=True)
    with (folder/"notebook_runtime.jsonl").open("a") as f:f.write(json.dumps(row)+"\n")
    print(json.dumps(row))
