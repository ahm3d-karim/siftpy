"""Stage 2/3/5 screen tests — the screens read from the app's loaded frame.

Driven through Textual's pilot so the real key handling is exercised, not just
the underlying functions (those have their own test modules).
"""
from __future__ import annotations

import asyncio

import pandas as pd
from textual.widgets import DataTable, Input, Select, Static

from siftpy.tui.app import SiftApp
from siftpy.tui.screens import CrosstabScreen, DictionaryScreen, ProfileScreen, WeightsScreen

FRAME = pd.DataFrame(
    {
        "hh_id": [1, 2, 3, 4],
        "hh_wt": [1.0, 1.25, 2.0, 2.5],
        "female": [1, 0, 1, 1],
        "district": ["Lahore", "Lahore", "Multan", None],
    }
)


def text_of(static: Static) -> str:
    rendered = static.render()
    plain = getattr(rendered, "plain", None)
    return plain if plain is not None else str(rendered)


def write_frame(tmp_path) -> str:
    path = tmp_path / "lfs.csv"
    FRAME.to_csv(path, index=False)
    return str(path)


def test_menu_enter_routes_to_the_profile_screen(tmp_path):
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            assert app.load_path(write_frame(tmp_path)) is True

            await pilot.press("down", "enter")  # Column profile
            await pilot.pause()

            assert isinstance(app.screen, ProfileScreen)
            table = app.screen.query_one(DataTable)
            assert table.row_count == len(FRAME.columns)
            title = text_of(app.screen.query_one("#title", Static))
            assert "lfs.csv" in title
            assert "4 columns" in title

            await pilot.press("escape")
            await pilot.pause()
            assert not isinstance(app.screen, ProfileScreen)

            await pilot.press("q")

    asyncio.run(_run())


def test_profile_screen_flags_the_identifier_column(tmp_path):
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            app.load_path(write_frame(tmp_path))
            app.push_screen(ProfileScreen())
            await pilot.pause()

            note = text_of(app.screen.query_one("#note", Static))
            assert "hh_id" in note  # suspected-id, surfaced rather than hidden

            await pilot.press("q")

    asyncio.run(_run())


def test_weights_screen_selecting_a_candidate_sets_the_session_weight(tmp_path):
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            app.load_path(write_frame(tmp_path))
            assert app.weight is None

            app.push_screen(WeightsScreen())
            await pilot.pause()
            await pilot.press("down", "enter")  # first candidate after "none"

            assert app.weight == "hh_wt", app.weight
            title = text_of(app.screen.query_one("#title", Static))
            assert "hh_wt" in title

            await pilot.press("escape")
            await pilot.pause()

            await pilot.press("q")

    asyncio.run(_run())


def test_weights_screen_can_go_back_to_unweighted(tmp_path):
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            app.load_path(write_frame(tmp_path))
            app.weight = "hh_wt"

            app.push_screen(WeightsScreen())
            await pilot.pause()
            await pilot.press("n")  # clear

            assert app.weight is None

            await pilot.press("q")

    asyncio.run(_run())


def test_crosstab_screen_renders_counts_then_percentages(tmp_path):
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            app.load_path(write_frame(tmp_path))
            app.push_screen(CrosstabScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, CrosstabScreen)
            screen.query_one("#row", Select).value = "district"
            screen.query_one("#col", Select).value = "female"
            await pilot.pause()

            body = text_of(screen.query_one("#table", Static))
            assert "Lahore" in body and "Multan" in body
            assert "(missing)" in body  # missingness kept, never dropped

            await pilot.press("m")  # counts → row %
            await pilot.pause()
            body = text_of(screen.query_one("#table", Static))
            assert "100.0" in body

            await pilot.press("q")

    asyncio.run(_run())


def test_dictionary_export_writes_both_files_to_the_chosen_directory(tmp_path):
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            app.load_path(write_frame(tmp_path))
            app.push_screen(DictionaryScreen())
            await pilot.pause()

            screen = app.screen
            out = tmp_path / "exports"
            out.mkdir()
            box = screen.query_one("#outdir", Input)
            box.value = str(out)

            screen.post_message(Input.Submitted(box, str(out)))
            await pilot.pause()

            assert (out / "lfs-dictionary.md").exists()
            assert (out / "lfs-dictionary.csv").exists()
            note = text_of(screen.query_one("#note", Static))
            assert "written" in note

            await pilot.press("q")

    asyncio.run(_run())


def test_dictionary_export_to_a_missing_directory_says_so(tmp_path):
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            app.load_path(write_frame(tmp_path))
            app.push_screen(DictionaryScreen())
            await pilot.pause()

            screen = app.screen
            box = screen.query_one("#outdir", Input)
            missing = str(tmp_path / "nope")
            screen.post_message(Input.Submitted(box, missing))
            await pilot.pause()

            note = text_of(screen.query_one("#note", Static))
            assert "No such directory" in note

            await pilot.press("q")

    asyncio.run(_run())
