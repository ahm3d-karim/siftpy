"""profile.py — what is this column, honestly.

Per column: dtype, missingness, cardinality, a range or a top-5, and flags for
the four things that bite in survey data (all-missing, constant, looks like an
ID, high-cardinality text). Flags are heuristics and say so — the flag carries
the evidence, and the profile carries the counts, so a human can disagree.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

ALL_MISSING = "all-missing"
CONSTANT = "constant"
SUSPECTED_ID = "suspected-id"
HIGH_CARDINALITY = "high-cardinality"
QUANTITATIVE = "quantitative"

TOP_N = 5


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    n_rows: int
    n_missing: int
    n_unique: int
    vmin: object = None
    vmax: object = None
    top: list[tuple[object, int]] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    label: str = ""

    @property
    def pct_missing(self) -> float:
        return 100.0 * self.n_missing / self.n_rows if self.n_rows else 0.0

    @property
    def missing_text(self) -> str:
        return f"{self.pct_missing:.1f}%"

    @property
    def range_text(self) -> str:
        if self.flags and ALL_MISSING in self.flags:
            return "—"
        if self.vmin is None and self.vmax is None:
            return self._top_text()
        return f"{_short(self.vmin)} … {_short(self.vmax)}"

    def _top_text(self) -> str:
        if not self.top:
            return "—"
        shown = ", ".join(f"{_short(v)}×{c}" for v, c in self.top[:3])
        return shown

    def flag_text(self) -> str:
        return " ".join(self.flags) if self.flags else ""


def _short(value: object, width: int = 18) -> str:
    if isinstance(value, float) and value.is_integer():
        text = str(int(value))  # 1.0 reads better as 1
    else:
        text = "" if value is None else str(value)
    return text if len(text) <= width else text[: width - 1] + "…"


def _is_quantitative(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series)


def profile_column(series: pd.Series, label: str = "") -> ColumnProfile:
    n_rows = int(len(series))
    n_missing = int(series.isna().sum())
    present = series.dropna()
    n_unique = int(present.nunique())

    prof = ColumnProfile(
        name=str(series.name),
        dtype=str(series.dtype),
        n_rows=n_rows,
        n_missing=n_missing,
        n_unique=n_unique,
        label=label,
    )

    if n_rows and n_missing == n_rows:
        prof.flags.append(ALL_MISSING)
    elif n_unique <= 1:
        prof.flags.append(CONSTANT)

    if n_unique and n_unique == len(present) and len(present) > 1:
        prof.flags.append(SUSPECTED_ID)

    # ponytail: cardinality thresholds are rules of thumb, not statistics.
    # They flag for a human to look; they never drop or reshape anything.
    if n_unique > 50 and n_unique > 0.5 * max(len(present), 1):
        prof.flags.append(HIGH_CARDINALITY)

    if _is_quantitative(present) and len(present):
        prof.flags.append(QUANTITATIVE)
        prof.vmin = present.min()
        prof.vmax = present.max()
    elif len(present):
        prof.top = [(v, int(c)) for v, c in present.value_counts().head(TOP_N).items()]

    return prof


def profile_frame(df: pd.DataFrame, var_labels: dict[str, str] | None = None) -> list[ColumnProfile]:
    labels = var_labels or {}
    return [profile_column(df[c], labels.get(str(c), "")) for c in df.columns]
