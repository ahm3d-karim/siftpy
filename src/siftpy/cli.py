"""cli.py — entry point. Bare `siftpy` (tty) opens the TUI; subcommands land per stage.

Test command: .venv/Scripts/python.exe -m pytest -q  (uv run broken in git-bash on
this machine — document persists from the CLI-shipping skill).
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="siftpy",
        description="Survey-microdata profiler TUI: profile columns, weights, cross-tabs, reproducible cleaning scripts.",
    )
    parser.add_argument("--version", action="store_true", help="print version and exit")
    args = parser.parse_args(argv)

    if args.version:
        from siftpy import __version__

        print(__version__)
        return 0

    from siftpy.tui.app import run_tui

    return run_tui()


if __name__ == "__main__":
    sys.exit(main())
