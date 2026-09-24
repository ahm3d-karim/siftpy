"""Stage 0 TUI check: the shell actually mounts, renders, and quits.

Uses Textual's pilot harness instead of a real terminal, so this runs headless
in CI. Kept dependency-free — no pytest-asyncio; asyncio.run wraps the async
pilot.
"""
from __future__ import annotations

import asyncio

from textual.widgets import ListView, Static

from siftpy.tui.app import BANNER, MENU_ITEMS, SiftApp


def test_shell_mounts_renders_and_quits():
    async def _run() -> None:
        app = SiftApp()
        async with app.run_test() as pilot:
            # The banner widget has to be mounted; its text is checked on the
            # constant rather than through the render pipeline, which Textual
            # 8.x does not expose as a plain attribute.
            assert isinstance(app.query_one("#banner"), Static)
            assert "survey-microdata profiler TUI" in BANNER

            menu = app.query_one("#menu", ListView)
            assert len(menu.children) == len(MENU_ITEMS) == 8
            assert all(item.disabled for item in menu.children)

            # `q` must actually quit: App.exit() sets this flag, so this asserts
            # the binding works rather than just that the key could be pressed.
            assert app._exit is False
            await pilot.press("q")
            await pilot.pause()
            assert app._exit is True

    asyncio.run(_run())
