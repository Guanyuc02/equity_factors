from __future__ import annotations
import json, os, uuid, time
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .utils import sha1, file_lock

class Store:
    def __init__(self, root: Optional[Path] = None) -> None:
        root_env = os.getenv("FZR_DATA_ROOT")
        self.root = Path(root_env) if root_env else (Path(__file__).resolve().parents[2] / "data")
        if root:
            self.root = Path(root)
        self.raw = self.root / "raw"
        self.manifest = self.root / "manifest" / "manifest.jsonl"
        self.fp_dir = self.root / "manifest" / "fingerprints"
        self.lock_root = self.root / "locks"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.fp_dir.mkdir(parents=True, exist_ok=True)
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        self.lock_root.mkdir(parents=True, exist_ok=True)

    def table_root(self, table: str) -> Path:
        return self.raw / table

    def partition_dir(self, table: str, year: int) -> Path:
        return self.table_root(table) / f"year={year}"

    def _partition_lock(self, table: str, year: int) -> Path:
        return self.lock_root / table / f"{year}.lock"

    def _manifest_lock(self) -> Path:
        return self.lock_root / "manifest.lock"

    def _fingerprint_lock(self, table: str, year: int) -> Path:
        return self.lock_root / "fingerprints" / table / f"{year}.lock"

    def read_partitions(self, table: str, years: Iterable[int], columns: Optional[List[str]] = None) -> Dict[int, pd.DataFrame]:
        out: Dict[int, pd.DataFrame] = {}
        for y in years:
            d = self.partition_dir(table, y)
            if not d.exists():
                continue
            parts = sorted(d.glob("part-*.parquet"))
            if not parts:
                continue
            dfs = [pd.read_parquet(p, columns=columns) for p in parts]
            df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
            out[y] = df
        return out

    def write_partition(self, df: pd.DataFrame, table: str, year: int, meta: Dict) -> Path:
        d = self.partition_dir(table, year)
        lock_path = self._partition_lock(table, year)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with file_lock(lock_path):
            d.mkdir(parents=True, exist_ok=True)
            path = d / f"part-{uuid.uuid4().hex}.parquet"
            tmp = d / f".tmp-{uuid.uuid4().hex}.parquet"
            table_pa = pa.Table.from_pandas(df, preserve_index=False)
            pq.write_table(table_pa, tmp, compression="zstd")
            os.replace(tmp, path)

            for existing in d.glob("part-*.parquet"):
                if existing != path:
                    existing.unlink(missing_ok=True)

            rec = {
                "event": "write_partition",
                "table": table,
                "year": year,
                "rows": int(len(df)),
                "bytes": int(path.stat().st_size),
                "path": str(path),
                "meta": meta,
                "written_at": time.time(),
                "spec_sha": sha1(meta.get("spec_key", "")),
            }
            self.upsert_manifest(rec)
            return path

    def upsert_manifest(self, rec: Dict) -> None:
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        lock = self._manifest_lock()
        lock.parent.mkdir(parents=True, exist_ok=True)
        with file_lock(lock):
            with open(self.manifest, "a") as f:
                f.write(json.dumps(rec) + "\n")

    def fp_path(self, table: str, year: int) -> Path:
        return self.fp_dir / table / f"{year}.json"

    def compute_fingerprint(self, df: pd.DataFrame, table: str, year: int, date_col: str) -> Dict:
        schema = list(df.columns)
        fp = {
            "table": table,
            "year": year,
            "schema": schema,
            "rows": int(len(df)),
            "max_date": None if df.empty else str(pd.to_datetime(df[date_col]).max().date()),
            "computed_at": time.time(),
        }
        p = self.fp_path(table, year)
        p.parent.mkdir(parents=True, exist_ok=True)
        lock = self._fingerprint_lock(table, year)
        lock.parent.mkdir(parents=True, exist_ok=True)
        with file_lock(lock):
            with open(p, "w") as f:
                json.dump(fp, f)
        return fp

    def need_refresh(self, table: str, year: int, ttl_days: int) -> bool:
        if ttl_days <= 0:
            return True
        d = self.partition_dir(table, year)
        if not d.exists() or not any(d.glob("part-*.parquet")):
            return True
        fp = self.fp_path(table, year)
        if not fp.exists():
            return True
        age_days = (time.time() - fp.stat().st_mtime) / 86400.0
        return age_days > ttl_days
