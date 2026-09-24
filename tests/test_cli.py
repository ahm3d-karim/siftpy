"""CLI surface: the entry point exists and behaves from the command line."""
from __future__ import annotations

import pytest

from siftpy import __version__, cli


def test_version_prints(capsys):
    assert cli.main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == __version__


def test_help_exits_zero():
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
