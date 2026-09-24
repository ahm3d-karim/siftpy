"""Stage 2 tests: column profiling and its flags, on hand-checkable data."""
from __future__ import annotations

import pandas as pd

from siftpy.core.profile import (
    ALL_MISSING,
    CONSTANT,
    HIGH_CARDINALITY,
    QUANTITATIVE,
    SUSPECTED_ID,
    profile_column,
    profile_frame,
)

FRAME = pd.DataFrame(
    {
        "hh_id": [1, 2, 3, 4],
        "hh_wt": [1.0, 1.0, 2.0, 2.0],
        "female": [1, 0, 1, 1],
        "district": ["Lahore", "Lahore", "Multan", None],
        "constant": [7, 7, 7, 7],
        "allmiss": [None, None, None, None],
    }
)


def test_missing_math_is_exact():
    prof = profile_column(FRAME["district"])

    assert prof.n_missing == 1
    assert prof.pct_missing == 25.0
    assert prof.missing_text == "25.0%"
    assert prof.n_unique == 2  # missing is not a category in the profile


def test_flags_fire_on_the_right_columns():
    profiles = {p.name: p for p in profile_frame(FRAME)}

    assert ALL_MISSING in profiles["allmiss"].flags
    assert CONSTANT in profiles["constant"].flags
    assert SUSPECTED_ID in profiles["hh_id"].flags
    assert QUANTITATIVE in profiles["hh_wt"].flags
    assert profiles["district"].flags == []  # ordinary text column: no noise


def test_numeric_columns_report_a_range_and_text_reports_a_top_n():
    profiles = {p.name: p for p in profile_frame(FRAME)}

    assert profiles["hh_wt"].vmin == 1.0 and profiles["hh_wt"].vmax == 2.0
    assert "1 … 2" in profiles["hh_wt"].range_text
    assert profiles["district"].top[0] == ("Lahore", 2)
    assert "Lahore" in profiles["district"].range_text


def test_all_missing_column_has_no_range():
    prof = profile_column(FRAME["allmiss"])

    assert prof.range_text == "—"
    assert prof.n_unique == 0


def test_high_cardinality_text_is_flagged():
    frame = pd.DataFrame({"note": [f"free text {i}" for i in range(60)]})
    prof = profile_column(frame["note"])

    assert HIGH_CARDINALITY in prof.flags


def test_labels_ride_along_from_the_file_dictionary():
    profiles = profile_frame(FRAME, {"hh_wt": "Sampling weight"})
    by_name = {p.name: p for p in profiles}

    assert by_name["hh_wt"].label == "Sampling weight"
    assert by_name["female"].label == ""
