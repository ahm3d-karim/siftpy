"""tui/app.py — the Textual shell.

Stage 0 gave us the frame. Stage 1 makes the menu real: the cursor moves over
every entry, a pointer shows where it is, and "Open a data file" loads a file
through core.loader. Entries that belong to later stages say so instead of
sitting disabled — a menu where the cursor cannot move reads as a broken app.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Input, ListItem, ListView, Static

from siftpy.core.loader import FileMeta, LoadError, read_file

__version__ = "0.1.0"

POINTER = "▸"

BANNER = r"""
    _  __ _            
 __(_)/ _| |_ _ __ _  _
(_-< |  _|  _| '_ \ || |
/__/_|_|  \__| .__/\_, |
             |_|   |__/
"""


@dataclass(frozen=True)
class MenuEntry:
    label: str
    stage: int
    built: bool = False
    needs_file: bool = False


MENU: list[MenuEntry] = [
    MenuEntry("Open a data file", stage=1, built=True),
    MenuEntry("Column profile (this file)", stage=2, needs_file=True),
    MenuEntry("Label dictionary", stage=2, needs_file=True),
    MenuEntry("Weights & weighted stats", stage=3, needs_file=True),
    MenuEntry("LLM suggestions (BYOK)", stage=4, needs_file=True),
    MenuEntry("Cross-tab builder", stage=5, needs_file=True),
    MenuEntry("Export: cleaning script", stage=6, needs_file=True),
    MenuEntry("Settings", stage=4),
]

# kept for the Stage 0 test that counts entries
MENU_ITEMS = [(e.label, e.stage) for e in MENU]


def menu_label(index: int, pointed: bool, entry: MenuEntry) -> str:
    """One menu row. Pure, so the pointer behaviour is testable without a TUI.

    Built entries carry no stage tag; the rest say which stage switches them on.
    """
    mark = f"{POINTER} " if pointed else "  "
    if entry.built:
        return f"{mark}{entry.label}"
    return f"{mark}{entry.label}  [dim](stage {entry.stage})[/dim]"


class SiftApp(App):
    TITLE = "siftpy"
    SUB_TITLE = "survey-microdata profiler"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("o", "open_file", "Open file"),
        ("escape", "hide_input", "Cancel"),
    ]

    CSS = """
    #banner { color: $accent; padding: 0 2; }
    #status { color: $text-muted; padding: 0 2; }
    #menu { height: auto; margin: 1 2; }
    ListView { height: auto; max-height: 12; }
    ListItem { padding: 0 1; }
    ListView > ListItem.--highlight { background: $accent 25%; }
    #path-input { margin: 1 2; display: none; }
    #path-input.visible { display: block; }
    #notice { padding: 0 2; }
    """

    def __init__(self) -> None:
        super().__init__()
        self.df = None
        self.meta: FileMeta | None = None

    # ---------- layout ----------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(BANNER, id="banner")
            yield Static(self._status_text(), id="status")
            yield ListView(*self._menu_entries(), id="menu")
            yield Input(placeholder="path to a .dta / .sav / .csv file", id="path-input")
            yield Static(self._hint_text(), id="notice")
        yield Footer()

    def _menu_entries(self) -> list[ListItem]:
        items = []
        for i, entry in enumerate(MENU):
            item = ListItem(Static(menu_label(i, i == 0, entry)), id=f"item-{i}")
            items.append(item)
        return items

    def _status_text(self) -> str:
        if self.meta is None:
            return "no file open"
        return self.meta.summary()

    def _hint_text(self) -> str:
        if self.meta is None:
            return "↑/↓ move · enter select · o open a file · q quit"
        return "↑/↓ move · enter select · o open another file · q quit"

    # ---------- pointer ----------

    def _point_at(self, index: int | None) -> None:
        """Move the ▸ marker. One row shows it, every other row is cleared."""
        for i, entry in enumerate(MENU):
            pointer = i == index
            item = self.query_one(f"#item-{i}", ListItem)
            item.query_one(Static).update(menu_label(i, pointer, entry))

    @on(ListView.Highlighted)
    def _on_highlighted(self, event: ListView.Highlighted) -> None:
        self._point_at(event.list_view.index)

    # ---------- actions ----------

    @on(ListView.Selected)
    def _on_selected(self, event: ListView.Selected) -> None:
        entry = MENU[event.list_view.index or 0]
        if entry.label == "Open a data file":
            self.action_open_file()
            return
        if not entry.built:
            if entry.needs_file and self.meta is None:
                self._notice("[yellow]Open a file first[/yellow] — stage "
                             f"{entry.stage} builds on it.")
            else:
                self._notice(f"[yellow]Stage {entry.stage}[/yellow] — not built yet.")
            return
        self._notice("")

    def action_open_file(self) -> None:
        box = self.query_one("#path-input", Input)
        box.add_class("visible")
        box.focus()

    def action_hide_input(self) -> None:
        box = self.query_one("#path-input", Input)
        box.remove_class("visible")
        self.query_one("#menu", ListView).focus()

    @on(Input.Submitted, "#path-input")
    def _load_submitted(self, event: Input.Submitted) -> None:
        if not event.value.strip():
            self._notice("Type a path, or press esc to cancel.")
            return
        self.load_path(event.value)

    def load_path(self, raw: str) -> bool:
        """Load a file into the session. Returns True on success.

        LoadError becomes a red notice; the app keeps running (Stage 1 rule).
        """
        try:
            df, meta = read_file(raw)
        except LoadError as exc:
            self._notice(f"[red]{exc}[/red]")
            return False
        self.df, self.meta = df, meta
        self.query_one("#status", Static).update(self._status_text())
        self._notice(self._hint_text())
        self.action_hide_input()
        return True

    def _notice(self, text: str) -> None:
        self.query_one("#notice", Static).update(text)


def run_tui() -> int:
    SiftApp().run()
    return 0
