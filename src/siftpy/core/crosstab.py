"""crosstab.py — the number RAs actually make, with the missing row kept.

Counts, row % or column %, weighted or not. Missing values appear as their own
category labelled "(missing)" — never silently dropped, because a table that
hides its missingness is a table that lies about its denominator.
"""
from __future__ import annotations

import pandas as pd

MISSING_LABEL = "(missing)"


def _categorised(series: pd.Series, label: str = MISSING_LABEL) -> pd.Series:
    return series.astype("object").where(series.notna(), other=label)


def crosstab(
    df: pd.DataFrame,
    row: str,
    col: str,
    weight: str | None = None,
    normalize: str | None = None,
    missing_label: str = MISSING_LABEL,
    drop_empty: bool = True,
) -> pd.DataFrame:
    """Two-way table. normalize=None counts, "row" or "col" gives percentages."""
    if normalize not in (None, "row", "col", "all"):
        raise ValueError(f"normalize must be None, 'row', 'col' or 'all', not {normalize!r}")
    for name in (row, col):
        if name not in df.columns:
            raise KeyError(f"no column named {name!r}")

    frame = pd.DataFrame(
        {
            row: _categorised(df[row], missing_label),
            col: _categorised(df[col], missing_label),
        }
    )
    if weight is not None:
        if weight not in df.columns:
            raise KeyError(f"no column named {weight!r}")
        frame["_w"] = pd.to_numeric(df[weight], errors="coerce").fillna(0.0)

    if weight is None:
        table = pd.crosstab(frame[row], frame[col], dropna=False)
    else:
        table = frame.pivot_table(
            index=row, columns=col, values="_w", aggfunc="sum", fill_value=0.0, dropna=False
        )
        table = table.astype(float)

    table.index.name = row
    table.columns.name = col
    if drop_empty:
        keep_r = [i for i in table.index if not (table.loc[i] == 0).all()]
        keep_c = [c for c in table.columns if not (table[c] == 0).all()]
        table = table.loc[keep_r, keep_c]

    if normalize:
        if normalize == "row":
            totals = table.sum(axis=1).replace(0, pd.NA)
            table = table.div(totals, axis=0) * 100.0
        elif normalize == "col":
            totals = table.sum(axis=0).replace(0, pd.NA)
            table = table.div(totals, axis=1) * 100.0
        else:
            total = table.to_numpy().sum()
            table = table / total * 100.0 if total else table
    return table


def table_text(table: pd.DataFrame, decimals: int = 1) -> str:
    """Plain-text rendering for the terminal, with the axis names kept."""
    return table.to_string(float_format=lambda v: f"{v:,.{decimals}f}")
