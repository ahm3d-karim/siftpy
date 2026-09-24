"""Stage 5 tests: cross-tabs, weighted and unweighted, with missingness kept."""
from __future__ import annotations

import pandas as pd
import pytest

from siftpy.core.crosstab import MISSING_LABEL, crosstab, table_text

FRAME = pd.DataFrame(
    {
        "district": ["Lahore", "Lahore", "Multan", None],
        "female": [1, 0, 1, 1],
        "hh_wt": [1.0, 1.0, 2.0, 2.0],
    }
)


def test_unweighted_counts_are_exact_and_missing_has_its_own_row():
    table = crosstab(FRAME, "district", "female")

    assert table.loc["Lahore", 0] == 1
    assert table.loc["Lahore", 1] == 1
    assert table.loc["Multan", 1] == 1
    assert MISSING_LABEL in table.index, table
    assert table.loc[MISSING_LABEL, 1] == 1
    # nobody vanished: 4 rows in, 4 counted
    assert table.to_numpy().sum() == 4


def test_weighted_counts_are_weight_sums_not_row_counts():
    table = crosstab(FRAME, "district", "female", weight="hh_wt")

    assert table.loc["Lahore", 1] == pytest.approx(1.0)
    assert table.loc["Multan", 1] == pytest.approx(2.0)
    assert table.loc[MISSING_LABEL, 1] == pytest.approx(2.0)
    assert table.to_numpy().sum() == pytest.approx(6.0)  # every weight accounted for


def test_row_percentages_sum_to_a_hundred():
    table = crosstab(FRAME, "district", "female", normalize="row")

    for label in table.index:
        assert table.loc[label].sum() == pytest.approx(100.0), label


def test_column_percentages_sum_to_a_hundred():
    table = crosstab(FRAME, "district", "female", normalize="col")

    for column in table.columns:
        assert table[column].sum() == pytest.approx(100.0), column


def test_weighted_row_percentages_use_the_weights():
    table = crosstab(FRAME, "district", "female", weight="hh_wt", normalize="row")

    assert table.loc["Multan", 1] == pytest.approx(100.0)
    assert table.loc[MISSING_LABEL, 1] == pytest.approx(100.0)


def test_axes_carry_their_names_and_text_renders():
    table = crosstab(FRAME, "district", "female")
    text = table_text(table)

    assert table.index.name == "district"
    assert table.columns.name == "female"
    assert "Lahore" in text and "Multan" in text


def test_bad_arguments_are_refused_loudly():
    with pytest.raises(ValueError):
        crosstab(FRAME, "district", "female", normalize="sideways")
    with pytest.raises(KeyError):
        crosstab(FRAME, "district", "no_such_column")
    with pytest.raises(KeyError):
        crosstab(FRAME, "district", "female", weight="no_such_weight")
