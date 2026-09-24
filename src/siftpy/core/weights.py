"""weights.py — find the weight variable, then use it correctly.

The weight variable is tribal knowledge in every survey dataset. This turns it
into a ranked suggestion with stated evidence, and the suggestion is a choice,
never an assumption: nothing gets weighted until a human confirms.

Boundaries (from the plan, deliberate): point estimates only. No design-based
standard errors, no weighted quantiles. Weighted percentile is subtle enough to
be wrong quietly, so it is documented as absent rather than approximated.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

WEIGHT_NAME = re.compile(r"(^|_)(w|wt|wgt|weight|pweight|aweight|fweight|hh_wt|hhwt|sw|svy_wt)($|_)", re.I)
DESIGN_NAME = re.compile(r"(^|_)(psu|stratum|strata|cluster|clust|ea|enum|fpc)($|_)", re.I)
ID_NAME = re.compile(r"(^|_)(id|code|serial|slip|hhid)($|_)", re.I)
WEIGHT_LABEL = re.compile(r"weight|weighted|weighting", re.I)

STRONG, MEDIUM, WEAK = 3.0, 2.0, 1.0


@dataclass
class WeightCandidate:
    name: str
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    @property
    def confidence(self) -> str:
        return "high" if self.score >= STRONG else "medium" if self.score >= MEDIUM else "low"

    def why(self) -> str:
        return "; ".join(self.reasons)


def _numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series)


def candidates(df: pd.DataFrame, var_labels: dict[str, str] | None = None) -> list[WeightCandidate]:
    """Ranked guesses at the weight variable. Never applies one."""
    labels = var_labels or {}
    found: list[WeightCandidate] = []

    for name in df.columns:
        col = str(name)
        series = df[name]
        label = labels.get(col, "") or ""
        cand = WeightCandidate(name=col)

        if WEIGHT_NAME.search(col):
            cand.score += STRONG
            cand.reasons.append(f"name matches a weight pattern ({col})")
        if WEIGHT_LABEL.search(label):
            cand.score += STRONG
            cand.reasons.append(f"label says '{label}'")

        if _numeric(series):
            present = series.dropna()
            if len(present):
                fractional = bool((present % 1 != 0).mean() > 0.5)
                if fractional:
                    cand.score += MEDIUM
                    cand.reasons.append("fractional values (weights are rarely whole numbers)")
                cand.evidence.append(
                    f"sum {present.sum():,.0f} · mean {present.mean():.3f} · "
                    f"range {present.min():g}–{present.max():g}"
                )
                if present.sum() > 1_000 * max(len(present), 1):
                    cand.score += WEAK
                    cand.reasons.append("sum is far larger than the row count (expansion scale)")
        elif cand.reasons:
            # a weight pattern on a non-numeric column is usually a false friend
            cand.reasons.append("not numeric — probably a label, not a weight")
            cand.score -= MEDIUM

        if DESIGN_NAME.search(col):
            cand.reasons.append("design variable (PSU/stratum), not a weight")
            cand.score -= MEDIUM
        if ID_NAME.search(col) and not WEIGHT_NAME.search(col):
            cand.reasons.append("identifier-shaped name")
            cand.score -= WEAK

        if cand.reasons:
            found.append(cand)

    return sorted(found, key=lambda c: (-c.score, c.name))


# ---------- weighted stats: point estimates only ----------


def _pairs(series: pd.Series, weights: pd.Series | None) -> tuple[pd.Series, pd.Series]:
    if weights is None:
        return series, pd.Series(1.0, index=series.index)
    mask = series.notna() & weights.notna()
    return series[mask], weights[mask]


def weighted_mean(series: pd.Series, weights: pd.Series | None = None) -> float | None:
    values, w = _pairs(series, weights)
    if not len(values) or w.sum() == 0:
        return None
    return float((values * w).sum() / w.sum())


def weighted_sum(series: pd.Series, weights: pd.Series | None = None) -> float | None:
    values, w = _pairs(series, weights)
    if not len(values):
        return None
    return float((values * w).sum())


def weighted_counts(series: pd.Series, weights: pd.Series | None = None) -> pd.Series:
    """Weighted (or plain) counts per category, missing kept as its own category.

    A missing *value* is a category here (it is part of the denominator), even
    though a missing weight drops the row — you cannot expand a row you cannot
    weigh. That is the difference from weighted_mean, where a missing value has
    no mean to contribute to.
    """
    if weights is None:
        if not len(series):
            return pd.Series(dtype=float)
        out = series.groupby(series, dropna=False).size().astype(float)
    else:
        mask = weights.notna()
        frame = pd.DataFrame({"v": series[mask], "w": weights[mask]})
        if not len(frame):
            return pd.Series(dtype=float)
        out = frame.groupby("v", dropna=False)["w"].sum()
    return out.sort_values(ascending=False)


def weighted_percent(series: pd.Series, weights: pd.Series | None = None) -> pd.Series:
    counts = weighted_counts(series, weights)
    total = counts.sum()
    return (counts / total * 100.0) if total else counts
