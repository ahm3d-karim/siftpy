"""Stage 2 export tests: the dictionary goes where you said, and nowhere else."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from siftpy.core.export import (
    ExportError,
    check_dir,
    dictionary_csv,
    dictionary_markdown,
    write_dictionary,
)
from siftpy.core.loader import read_file
from siftpy.core.profile import profile_frame

FRAME = pd.DataFrame(
    {
        "hh_id": [1, 2, 3],
        "hh_wt": [1.0, 1.5, 2.0],
        "female": [1, 0, 1],
        "district": ["Lahore", None, "Multan"],
    }
)


@pytest.fixture
def loaded(tmp_path):
    path = tmp_path / "lfs.csv"
    FRAME.to_csv(path, index=False)
    df, meta = read_file(path)
    return meta, profile_frame(df)


def test_markdown_dictionary_lists_every_variable(loaded):
    meta, profiles = loaded
    text = dictionary_markdown(meta, profiles)

    assert text.startswith("# Data dictionary — lfs.csv")
    assert "| `hh_wt` |" in text
    for name in FRAME.columns:
        assert f"`{name}`" in text
    assert "25" in text or "33.3" in text  # district has one missing of three


def test_csv_dictionary_has_a_header_and_one_row_per_variable(loaded):
    meta, profiles = loaded
    lines = dictionary_csv(meta, profiles).strip().splitlines()

    assert lines[0].startswith("variable,dtype,label")
    assert len(lines) == len(FRAME.columns) + 1


def test_value_labels_are_written_when_the_file_has_them(tmp_path):
    frame = pd.DataFrame({"female": [1, 0, 1]})
    path = tmp_path / "labelled.csv"
    frame.to_csv(path, index=False)
    df, meta = read_file(path)
    meta.value_labels = {"female": {1: "Yes", 0: "No"}}

    text = dictionary_markdown(meta, profile_frame(df, meta.var_labels))

    assert "## Value labels" in text
    assert "1 = Yes" in text


def test_write_dictionary_lands_in_the_directory_that_was_chosen(loaded, tmp_path):
    meta, profiles = loaded
    out = tmp_path / "exports"
    out.mkdir()

    written = write_dictionary(out, meta, profiles, fmt="md")

    assert written == out / "lfs-dictionary.md"
    assert written.exists()
    assert "Data dictionary" in written.read_text(encoding="utf-8")

    as_csv = write_dictionary(out, meta, profiles, fmt="csv")
    assert as_csv.name == "lfs-dictionary.csv"
    assert as_csv.read_text(encoding="utf-8").count("\n") == len(profiles) + 1


@pytest.mark.parametrize("bad", ["", "no-such-folder-here"])
def test_a_directory_that_does_not_exist_is_an_error_with_a_sentence(bad):
    with pytest.raises(ExportError):
        check_dir(bad)


def test_a_file_is_not_a_directory(tmp_path):
    target = tmp_path / "notes.md"
    target.write_text("x", encoding="utf-8")

    with pytest.raises(ExportError, match="Not a directory"):
        check_dir(target)


def test_unknown_format_is_refused(loaded, tmp_path):
    meta, profiles = loaded
    with pytest.raises(ExportError, match="Unsupported export format"):
        write_dictionary(tmp_path, meta, profiles, fmt="xlsx")
