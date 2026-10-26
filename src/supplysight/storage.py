"""Single-writer local filesystem output replacement, including on restricted Spark hosts."""

import os
import shutil
import uuid
from pathlib import Path


def write_parquet(frame, destination):
    path = Path(destination)
    if path.name in ("", ".", "..") or len(path.resolve().parts) < 4:
        raise ValueError("Refusing unsafe output path")
    if path.exists() and not path.is_dir():
        raise ValueError(f"Expected dataset directory: {path}")
    if str(path).startswith("/Volumes/"):
        # Spark owns distributed output on Unity Catalog volumes. Never manipulate its part files locally.
        frame.write.mode("overwrite").parquet(str(path))
        return
    # Write to a fresh path so Hadoop cannot retain a previous file listing.
    # Only replace this one dedicated output after Spark completes successfully.
    staging = path.parent / f".writing-{path.name}-{uuid.uuid4().hex}"
    try:
        # This portfolio sample is bounded, so one stable part name simplifies
        # replacement and keeps exports portable across local filesystem adapters.
        frame.coalesce(1).write.mode("errorifexists").parquet(str(staging))
        parts = list(staging.glob("*.parquet"))
        if len(parts) != 1:
            raise RuntimeError(f"Expected one completed Parquet part, got {len(parts)}")
        path.mkdir(parents=True, exist_ok=True)
        # Keep the directory itself: deleting and recreating the same directory
        # can revive cached children on virtualized filesystem adapters.
        for child in path.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        os.replace(parts[0], path / "data.parquet")
        if [p.name for p in path.glob("*.parquet")] != ["data.parquet"]:
            raise RuntimeError("Stale Parquet files remain after output replacement")
    finally:
        if staging.exists():
            shutil.rmtree(staging)
