"""loader.py — one file in, one DataFrame plus its metadata out.

Supports the three shapes PBS files actually arrive in:

    .dta  Stata       pandas.read_stata  + StataReader variable/value labels
    .sav  SPSS        pyreadstat.read_sav            (column + value labels)
    .csv  plain       pandas.read_csv                (no labels)

Design rule from the plan: nothing here is allowed to raise a raw pandas or
pyreadstat traceback at the UI. Every failure becomes LoadError with a message a
human can act on, because a corrupt file must not kill the session.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

STATA_SUFFIXES = {".dta"}
SPSS_SUFFIXES = {".sav", ".zsav", ".por"}
CSV_SUFFIXES = {".csv", ".txt", ".tsv"}

SUPPORTED = STATA_SUFFIXES | SPSS_SUFFIXES | CSV_SUFFIXES


class LoadError(Exception):
    """A file we could not turn into a DataFrame, with a readable reason."""


@dataclass
class FileMeta:
    """What the file told us about itself, cached for the rest of the session."""

    path: Path
    fmt: str  # "stata" | "spss" | "csv"
    n_rows: int
    n_cols: int
    var_labels: dict[str, str] = field(default_factory=dict)
    value_labels: dict[str, dict] = field(default_factory=dict)

    @property
    def n_labelled(self) -> int:
        """How many columns carried a variable label."""
        return sum(1 for v in self.var_labels.values() if v)

    @property
    def shape(self) -> tuple[int, int]:
        return (self.n_rows, self.n_cols)

    def summary(self) -> str:
        """One line for the status bar."""
        return (
            f"{self.path.name}  ·  {self.fmt}  ·  "
            f"{self.n_rows:,} rows × {self.n_cols} cols  ·  "
            f"{self.n_labelled}/{self.n_cols} labelled"
        )


def read_file(path: str | Path) -> tuple[pd.DataFrame, FileMeta]:
    """Load one survey file. Raises LoadError with a human message on any failure."""
    p = Path(path).expanduser()

    if not str(path).strip():
        raise LoadError("No path given.")
    # Most specific condition first: a directory is a directory whatever it is
    # called, and an unreadable file *type* is worth saying even when the file
    # does not exist. Only then "no such file".
    if p.is_dir():
        raise LoadError(f"That is a directory, not a file: {p}")
    if p.suffix.lower() not in SUPPORTED:
        supported = ", ".join(sorted(SUPPORTED))
        raise LoadError(f"Unsupported file type '{p.suffix}'. Supported: {supported}")
    if not p.exists():
        raise LoadError(f"No such file: {p}")

    suffix = p.suffix.lower()
    try:
        if suffix in STATA_SUFFIXES:
            df, meta = _read_stata(p)
        elif suffix in SPSS_SUFFIXES:
            df, meta = _read_spss(p)
        else:
            df, meta = _read_csv(p)
    except LoadError:
        raise
    except Exception as exc:  # noqa: BLE001 — the whole point is to not leak tracebacks
        raise LoadError(f"{p.name} could not be read ({type(exc).__name__}): {exc}") from exc

    meta.n_rows, meta.n_cols = int(df.shape[0]), int(df.shape[1])
    return df, meta


def _read_stata(p: Path) -> tuple[pd.DataFrame, FileMeta]:
    from pandas.io.stata import StataReader

    # convert_categoricals=False keeps the stored codes; the label maps travel
    # beside the frame so the profile screen can show both.
    df = pd.read_stata(p, convert_categoricals=False)
    with StataReader(p) as reader:
        var_labels = dict(reader.variable_labels())
        value_labels = {k: dict(v) for k, v in reader.value_labels().items()}
    meta = FileMeta(p, "stata", *df.shape, var_labels=var_labels, value_labels=value_labels)
    return df, meta


def _read_spss(p: Path) -> tuple[pd.DataFrame, FileMeta]:
    import pyreadstat

    df, spss_meta = pyreadstat.read_sav(str(p))
    labels = dict(zip(spss_meta.column_names, spss_meta.column_labels or []))
    var_labels = {k: (v or "") for k, v in labels.items()}
    value_labels = {
        col: dict(mapping)
        for col, mapping in (spss_meta.variable_value_labels or {}).items()
    }
    meta = FileMeta(p, "spss", *df.shape, var_labels=var_labels, value_labels=value_labels)
    return df, meta


def _read_csv(p: Path) -> tuple[pd.DataFrame, FileMeta]:
    sep = "\t" if p.suffix.lower() in {".tsv", ".txt"} else ","
    df = pd.read_csv(p, sep=sep, low_memory=False)
    # ponytail: CSV carries no dictionary, so labels are the column names
    # themselves. If a sidecar dictionary ever appears, read it here.
    var_labels = {str(c): "" for c in df.columns}
    return df, FileMeta(p, "csv", *df.shape, var_labels=var_labels)
