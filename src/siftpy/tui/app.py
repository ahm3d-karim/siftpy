"""tui/app.py — the Textual App: welcome banner + main menu (Stage 0 shell).

Menu items whose features aren't built yet are DISABLED with their stage number,
so the full nav skeleton exists from day one (per plan).
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, ListItem, ListView, Static

__version__ = "0.1.0"

BANNER = r"""
  ██████  ██ ███    ██ ███████ ████████ ██ ██▀███   ██ ▄█ ██████  ██
 ██    ██ ██ ████   ██ ██         ██    ██ ██  ▄██ ██ ██▄██ ██  ██ ██
 ██    ██ ██ ██ ██  ██ ███████    ██    ██ ██▄██████ ██ ██▀██ ██████  ██
 ██    ██ ██ ██  ██ ██      ██    ██    ██ ██▀  ██ ██ ██ ██ ▀ ██  ██
  ██████  ██ ██   ████ ███████    ██    ██ ██   ██  ██ ██ ██████  ██
 survey-microdata profiler TUI
"""

# (menu label, stage that enables it, built?)  — built flag flips as stages land
MENU_ITEMS = [
    ("Open a data file", 1),
    ("Column profile (this file)", 2),
    ("Label dictionary", 2),
    ("Weights & weighted stats", 3),
    ("LLM suggestions (BYOK)", 4),
    ("Cross-tab builder", 5),
    ("Export: cleaning script", 6),
    ("Settings", 4),
]


class SiftApp(App):
    TITLE = "siftpy"
    SUB_TITLE = "survey-microdata profiler"
    BINDINGS = [("q", "quit", "Quit")]

    CSS = """
    #banner { color: $accent; padding: 0 2; }
    #menu { height: auto; margin: 1 2; }
    ListView { height: auto; max-height: 14; }
    ListItem { padding: 0 1; }
    #hint { color: $text-muted; padding: 0 2; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(BANNER, id="banner")
            yield ListView(*self._menu_entries(), id="menu")
            yield Static(
                "↑/↓ move · enter select · q quit — disabled items land in their stage",
                id="hint",
            )
        yield Footer()

    @staticmethod
    def _menu_entries() -> list[ListItem]:
        items = []
        for label, stage in MENU_ITEMS:
            if stage == 0:  # stage 0 = built now
                items.append(ListItem(Static(label)))
            else:
                items.append(
                    ListItem(Static(f"{label}  [dim](stage {stage})[/dim]"), disabled=True)
                )
        return items

    def action_quit(self) -> None:
        self.exit()


def run_tui() -> int:
    app = SiftApp()
    app.run()
    return 0
