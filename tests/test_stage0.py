"""Stage 0 tests: CLI surface + menu skeleton.

Run: .venv/Scripts/python.exe -m pytest -q
"""
from __future__ import annotations

import pytest

from siftpy import cli
from siftpy.tui.app import MENU_ITEMS, SiftApp


def test_version_prints(capsys):
    assert cli.main(["--version"]) == 0
    out = capsys.readouterr().out.strip()
    assert out == "0.1.0"


def test_menu_has_eight_items_with_stages():
    assert len(MENU_ITEMS) == 8
    assert all(1 <= stage <= 6 for _, stage in MENU_ITEMS)


def test_all_menu_items_disabled_at_stage_0():
    """No stage >0 feature exists yet — every ListItem must be disabled."""
    entries = SiftApp._menu_entries()
    assert len(entries) == len(MENU_ITEMS)
    assert all(item.disabled for item in entries)


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
