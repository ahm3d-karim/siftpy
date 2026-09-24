"""Stage 3 tests: candidate detection and weighted stats against hand arithmetic."""
from __future__ import annotations

import pandas as pd
import pytest

from siftpy.core.weights import (
    candidates,
    weighted_counts,
    weighted_mean,
    weighted_percent,
    weighted_sum,
)

FRAME = pd.DataFrame(
    {
        "hh_id": [1, 2, 3, 4],
        "hh_wt": [1.0, 1.0, 2.0, 2.0],
        "psu": [1, 1, 2, 2],
        "female": [1, 0, 1, 1],
        "district": ["Lahore", "Lahore", "Multan", None],
    }
)
LABELS = {"hh_wt": "Sampling weight", "psu": "Primary sampling unit", "hh_id": "Household identifier"}


def test_the_weight_is_found_with_stated_evidence():
    ranked = candidates(FRAME, LABELS)
    top = ranked[0]

    assert top.name == "hh_wt"
    assert top.confidence == "high"
    assert any("name matches" in r for r in top.reasons)
    assert any("Sampling weight" in r for r in top.reasons)
    # whole-number weights are legal; the fractional hint is for the usual case
    assert not any("fractional" in r for r in top.reasons)
    assert any("sum" in e for e in top.evidence)


def test_fractional_weights_get_an_extra_hint():
    frame = pd.DataFrame({"w": [0.25, 1.5, 2.75], "x": [1, 2, 3]})

    top = candidates(frame, {"w": "Sampling weight"})[0]

    assert any("fractional" in r for r in top.reasons)


def test_design_variables_are_labelled_as_such_not_recommended():
    ranked = {c.name: c for c in candidates(FRAME, LABELS)}

    assert "design variable" in ranked["psu"].why()
    assert ranked["psu"].score < ranked["hh_wt"].score


def test_identifier_shaped_columns_rank_below_the_weight():
    ranked = {c.name: c for c in candidates(FRAME, LABELS)}

    assert ranked["hh_id"].score < ranked["hh_wt"].score
    assert "identifier-shaped" in ranked["hh_id"].why()


def test_plain_categorical_columns_are_not_candidates():
    names = {c.name for c in candidates(FRAME, LABELS)}

    assert "district" not in names
    assert "female" not in names


def test_weighted_mean_matches_hand_arithmetic():
    # (1*1 + 0*1 + 1*2 + 1*2) / (1+1+2+2) = 5/6
    got = weighted_mean(FRAME["female"], FRAME["hh_wt"])

    assert got == pytest.approx(5 / 6, abs=1e-12)
    assert weighted_mean(FRAME["female"]) == pytest.approx(0.75)  # unweighted mean


def test_weighted_sum_is_the_expansion_of_the_column():
    assert weighted_sum(FRAME["female"], FRAME["hh_wt"]) == pytest.approx(5.0)
    assert weighted_sum(FRAME["female"]) == pytest.approx(3.0)


def test_weighted_percentages_come_out_of_the_weight_column():
    pct = weighted_percent(FRAME["female"], FRAME["hh_wt"])

    assert pct[1] == pytest.approx(5 / 6 * 100)
    assert pct[0] == pytest.approx(1 / 6 * 100)
    assert pct.sum() == pytest.approx(100.0)


def test_missing_values_are_their_own_category_not_dropped():
    counts = weighted_counts(FRAME["district"], FRAME["hh_wt"])

    assert pd.isna(counts.index).any() or "(missing)" in [str(i) for i in counts.index]
    assert counts.sum() == pytest.approx(6.0)  # every weight is still accounted for
