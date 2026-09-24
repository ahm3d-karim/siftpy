"""TUI checks: the shell mounts, the pointer moves, loading works, q quits.

Textual's pilot harness instead of a real terminal, so these run headless in CI.
No pytest-asyncio: asyncio.run wraps the async pilot.
"""
from __future__ import annotations

import asyncio

import pandas as pd
from textual.widgets import ListView, Static

from siftpy.tui.app import MENU, SiftApp, menu_label


def text_of(static: Static) -> str:
    """The row's text, through whatever Rich/Textual version we're on."""
    rendered = static.render()
    plain = getattr(rendered, "plain", None)
    return plain if plain is not None else str(rendered)


def rows(app: SiftApp) -> list[str]:
    menu = app.query_one("#menu", ListView)
    return [text_of(item.query_one(Static)) for item in menu.children]


def test_menu_label_puts_the_pointer_on_one_row_only():
    first = menu_label(0, True, MENU[0])
    second = menu_label(1, False, MENU[1])

    assert first.startswith("▸ Open a data file")
    assert second.startswith("  Column profile")
    assert "(stage 2)" in second
    assert "(stage" not in first  # built entries carry no stage tag


def test_shell_mounts_with_a_pointer_on_row_one():
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            assert "survey-microdata profiler" in SiftApp.SUB_TITLE
            assert len(app.query_one("#menu", ListView).children) == 8

            lines = rows(app)
            assert lines[0].startswith("▸ Open a data file")
            assert not lines[1].startswith("▸")

            await pilot.press("q")

    asyncio.run(_run())


def test_arrows_move_the_pointer():
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            await pilot.press("down")
            lines = rows(app)
            assert lines[1].startswith("▸ Column profile"), lines
            assert not lines[0].startswith("▸")

            await pilot.press("down", "down")
            assert rows(app)[3].startswith("▸ Weights"), rows(app)

            await pilot.press("up")
            assert rows(app)[2].startswith("▸ Label dictionary"), rows(app)

            await pilot.press("q")

    asyncio.run(_run())


def test_unbuilt_entry_says_which_stage_it_belongs_to():
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            await pilot.press("down")  # Column profile — needs a file, stage 2
            await pilot.press("enter")
            notice = text_of(app.query_one("#notice", Static))
            assert "Open a file first" in notice and "stage 2" in notice

            await pilot.press("q")

    asyncio.run(_run())


def test_loading_a_file_through_the_screen_updates_the_status(tmp_path):
    frame = pd.DataFrame({"hh_id": [1, 2], "hh_wt": [0.5, 1.5]})
    path = tmp_path / "mini.csv"
    frame.to_csv(path, index=False)

    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            assert app.meta is None
            assert app.load_path(str(path)) is True

            assert app.df is not None and app.df.shape == (2, 2)
            status = text_of(app.query_one("#status", Static))
            assert "mini.csv" in status and "2 rows × 2 cols" in status

            await pilot.press("q")

    asyncio.run(_run())


def test_a_bad_path_is_a_notice_not_a_crash():
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            assert app.load_path("nope.dta") is False
            notice = text_of(app.query_one("#notice", Static))
            assert "No such file" in notice
            assert app.meta is None

            await pilot.press("q")

    asyncio.run(_run())


def test_empty_path_says_so_instead_of_an_extension_error():
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            await pilot.press("o")  # opens and focuses the path box
            await pilot.press("enter")  # submit with nothing typed
            notice = text_of(app.query_one("#notice", Static))
            assert "Type a path" in notice, notice

            await pilot.press("q")

    asyncio.run(_run())


def test_q_quits():
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            assert app._exit is False
            await pilot.press("q")
            await pilot.pause()
            assert app._exit is True

    asyncio.run(_run())
