from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass(frozen=True)
class RequestSpec:
    table: str
    columns: List[str]
    date_col: str
    date_range: Tuple[str, str]
    filters: Dict[str, str] = field(default_factory=dict)
    join_policy: Optional[str] = None
    asof_policy: Optional[str] = None
    version: str = "v1"

    def key(self) -> str:
        cols = ",".join(sorted(self.columns))
        flt = ",".join(f"{k}={self.filters[k]}" for k in sorted(self.filters))
        pol = f"jp={self.join_policy or ''}|asof={self.asof_policy or ''}|v={self.version}"
        start, end = self.date_range
        return f"{self.table}|{cols}|{self.date_col}|{start}|{end}|{flt}|{pol}"
