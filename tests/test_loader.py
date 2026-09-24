"""Stage 1 tests: the loader, on fixtures generated at test time (no binaries in the repo)."""
from __future__ import annotations

import pandas as pd
import pyreadstat
import pytest

from siftpy.core.loader import LoadError, read_file

FRAME = pd.DataFrame(
    {
        "hh_id": [1001, 1002, 1003, 1004],
        "hh_wt": [1.25, 0.75, 2.5, 1.0],
        "female": [1, 0, 1, 1],
    }
)
VAR_LABELS = {
    "hh_id": "Household identifier",
    "hh_wt": "Sampling weight",
    "female": "Head is female",
}
VALUE_LABELS = {"female": {1: "Yes", 0: "No"}}


@pytest.fixture
def stata_file(tmp_path):
    path = tmp_path / "lfs.dta"
    FRAME.to_stata(
        path,
        write_index=False,
        variable_labels=VAR_LABELS,
        value_labels=VALUE_LABELS,
    )
    return path


@pytest.fixture
def spss_file(tmp_path):
    path = tmp_path / "lfs.sav"
    pyreadstat.write_sav(
        FRAME.copy(),
        str(path),
        column_labels=[VAR_LABELS[c] for c in FRAME.columns],
        variable_value_labels=VALUE_LABELS,
    )
    return path


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "lfs.csv"
    FRAME.to_csv(path, index=False)
    return path


@pytest.mark.parametrize("fmt", ["stata_file", "spss_file", "csv_file"])
def test_every_format_loads_with_the_right_shape(fmt, request):
    path = request.getfixturevalue(fmt)
    df, meta = read_file(path)

    assert df.shape == (4, 3)
    assert meta.shape == (4, 3)
    assert meta.path == path
    assert list(df.columns) == ["hh_id", "hh_wt", "female"]


@pytest.mark.parametrize("fmt", ["stata_file", "spss_file"])
def test_variable_and_value_labels_survive(fmt, request):
    df, meta = read_file(request.getfixturevalue(fmt))

    assert meta.fmt in {"stata", "spss"}
    assert meta.var_labels["hh_wt"] == "Sampling weight"
    assert meta.var_labels["female"] == "Head is female"
    assert meta.n_labelled == 3
    # value labels arrive as a map beside the frame, not baked into the data
    assert meta.value_labels["female"][1] == "Yes"
    assert df["female"].tolist() == [1, 0, 1, 1]


def test_csv_loads_without_a_dictionary(csv_file):
    df, meta = read_file(csv_file)

    assert meta.fmt == "csv"
    assert meta.n_labelled == 0
    assert meta.var_labels == {"hh_id": "", "hh_wt": "", "female": ""}


def test_status_summary_is_one_line_and_honest(stata_file):
    _, meta = read_file(stata_file)
    line = meta.summary()

    assert "lfs.dta" in line and "stata" in line
    assert "4 rows × 3 cols" in line
    assert "3/3 labelled" in line


@pytest.mark.parametrize(
    "bad,expected",
    [
        ("", "No path given"),
        ("does-not-exist.dta", "No such file"),
        ("notes.xlsx", "Unsupported file type"),
    ],
)
def test_bad_input_becomes_a_readable_error(bad, expected):
    with pytest.raises(LoadError) as exc:
        read_file(bad)
    assert expected in str(exc.value)


def test_a_directory_is_not_a_file(tmp_path):
    with pytest.raises(LoadError, match="directory"):
        read_file(tmp_path)


def test_corrupt_file_does_not_leak_a_traceback(tmp_path):
    """A file with the right extension and the wrong contents."""
    path = tmp_path / "broken.dta"
    path.write_bytes(b"this is not a Stata file")

    with pytest.raises(LoadError) as exc:
        read_file(path)
    assert "broken.dta" in str(exc.value)
