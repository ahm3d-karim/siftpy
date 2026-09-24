"""tui/screens.py — the working screens.

One module rather than one-per-menu-item on purpose: each screen is 40-60 lines
and they share the same shape (read the loaded frame, render, go back). Split it
the day one of them grows real state.

Screens read the frame from the app (`self.app.df` / `.meta` / `.weight`) so
nothing has to be passed around: the app owns the session, screens are views.
"""
from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Label, ListItem, ListView, Select, Static

from siftpy.core.crosstab import crosstab, table_text
from siftpy.core.export import ExportError, write_dictionary
from siftpy.core.profile import profile_frame
from siftpy.core.weights import candidates

BACK = [("escape", "app.pop_screen", "Back")]


class ProfileScreen(Screen):
    """Every column, with the numbers that decide whether you trust it."""

    BINDINGS = BACK

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static("", id="title")
        yield DataTable(id="table", zebra_stripes=True)
        yield Static("", id="note")
        yield Footer()

    def on_mount(self) -> None:
        app = self.app
        profiles = profile_frame(app.df, app.meta.var_labels)
        self.query_one("#title", Static).update(
            f"{app.meta.path.name} — {len(profiles)} columns · "
            f"{app.meta.n_rows:,} rows · {app.meta.n_labelled} labelled"
        )
        table = self.query_one(DataTable)
        for column in ("variable", "label", "type", "missing", "unique", "range / top", "flags"):
            table.add_column(column, key=column)
        for prof in profiles:
            table.add_row(
                prof.name,
                prof.label or "—",
                prof.dtype,
                f"{prof.n_missing} ({prof.missing_text})",
                str(prof.n_unique),
                prof.range_text,
                prof.flag_text() or "—",
                key=prof.name,
            )
        flagged = [p.name for p in profiles if p.flags]
        self.query_one("#note", Static).update(
            f"flagged: {', '.join(flagged)}" if flagged else "no column tripped a flag"
        )


class DictionaryScreen(Screen):
    """Labels and value labels — the file's own dictionary, readable."""

    BINDINGS = BACK + [("e", "export", "Export")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static("", id="title")
        yield DataTable(id="table", zebra_stripes=True)
        yield Input(placeholder="output directory", id="outdir")
        yield Static("", id="note")
        yield Footer()

    def on_mount(self) -> None:
        app = self.app
        profiles = profile_frame(app.df, app.meta.var_labels)
        self.query_one("#title", Static).update(
            f"Label dictionary — {len(app.meta.value_labels)} column(s) carry value labels"
        )
        table = self.query_one(DataTable)
        for column in ("variable", "label", "value labels"):
            table.add_column(column, key=column)
        for prof in profiles:
            mapping = app.meta.value_labels.get(prof.name, {})
            shown = ", ".join(f"{k}={v}" for k, v in list(mapping.items())[:4])
            if len(mapping) > 4:
                shown += f" … (+{len(mapping) - 4})"
            table.add_row(prof.name, prof.label or "—", shown or "—", key=prof.name)
        self.query_one("#note", Static).update(
            f"press e to export — writes {app.meta.path.stem}-dictionary.md and .csv"
        )
        self.query_one("#outdir", Input).value = str(app.meta.path.parent)

    def action_export(self) -> None:
        self.query_one("#outdir", Input).focus()

    @on(Input.Submitted, "#outdir")
    def _write(self, event: Input.Submitted) -> None:
        app = self.app
        profiles = profile_frame(app.df, app.meta.var_labels)
        try:
            md = write_dictionary(event.value, app.meta, profiles, fmt="md")
            csv_path = write_dictionary(event.value, app.meta, profiles, fmt="csv")
        except ExportError as exc:
            self.query_one("#note", Static).update(f"[red]{exc}[/red]")
            return
        self.query_one("#note", Static).update(f"[green]written[/green] {md.name} + {csv_path.name} → {md.parent}")
        self.query_one("#outdir", Input).blur()


def weight_label(index: int, active: str | None, cand=None) -> str:
    """One row of the weights list. Pure, so the marks are testable.

    index -1 is the "none" row; otherwise `cand` is a WeightCandidate.
    """
    if index < 0:
        mark = "▸" if active is None else " "
        return f"{mark} none        [dim]use the raw counts[/dim]"
    mark = "▸" if cand.name == active else " "
    return (
        f"{mark} {cand.name}  ({cand.confidence})  {cand.why()}\n"
        f"      [dim]{'; '.join(cand.evidence)}[/dim]"
    )


class WeightsScreen(Screen):
    """Candidates with their evidence; enter to use one, n for none."""

    BINDINGS = BACK + [("n", "clear_weight", "No weight")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static("", id="title")
        yield ListView(id="list")
        yield Static("", id="note")
        yield Footer()

    def on_mount(self) -> None:
        self._rows = candidates(self.app.df, self.app.meta.var_labels)
        items = [ListItem(Static(weight_label(-1, self.app.weight)), id="item-none")]
        for i, cand in enumerate(self._rows):
            items.append(ListItem(Static(weight_label(i, self.app.weight, cand)), id=f"item-{i}"))
        view = self.query_one("#list", ListView)
        view.mount(*items)
        # A list nobody focused is a list the cursor cannot move in: point it at
        # the current choice and hand it the keys.
        view.index = self._index_of_current()
        view.focus()
        self._title()

    def _index_of_current(self) -> int:
        """Row index of the active weight: 0 is "none", 1+n is candidate n."""
        if self.app.weight is None:
            return 0
        for i, cand in enumerate(self._rows):
            if cand.name == self.app.weight:
                return i + 1
        return 0

    def _title(self) -> None:
        chosen = self.app.weight or "none (unweighted)"
        self.query_one("#title", Static).update(f"Weight variable: {chosen}")
        self.query_one("#note", Static).update(
            "enter selects · n clears · point estimates only, no design-based standard errors"
            if self._rows
            else "no column looks like a weight — the file may ship one elsewhere"
        )

    def _refresh_labels(self) -> None:
        """Move the ▸ by rewriting labels — never re-mounting (duplicate ids)."""
        for i, cand in enumerate(self._rows):
            item = self.query_one(f"#item-{i}", ListItem)
            item.query_one(Static).update(weight_label(i, self.app.weight, cand))
        self.query_one("#item-none", ListItem).query_one(Static).update(
            weight_label(-1, self.app.weight)
        )

    @on(ListView.Selected)
    def _select(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        self.app.weight = None if item_id == "item-none" else self._rows[int(item_id.split("-")[1])].name
        self._title()
        self._refresh_labels()

    def action_clear_weight(self) -> None:
        self.app.weight = None
        self._title()
        self._refresh_labels()


class CrosstabScreen(Screen):
    """Two variables, optional weights, missing kept as a row."""

    BINDINGS = BACK + [("m", "toggle_normalize", "Counts/%")]

    def compose(self) -> ComposeResult:
        app = self.app
        options = [(str(c), str(c)) for c in app.df.columns]
        yield Header(show_clock=False)
        yield Vertical(
            Static("", id="title"),
            Select(options, prompt="row variable", id="row"),
            Select(options, prompt="column variable", id="col"),
            Static("", id="table"),
            Static("", id="note"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.normalize: str | None = None
        self._paint()

    def _paint(self) -> None:
        app = self.app
        row = self.query_one("#row", Select).value
        col = self.query_one("#col", Select).value
        weight = app.weight
        label = "counts" if self.normalize is None else f"{self.normalize} %"
        self.query_one("#title", Static).update(
            f"Cross-tab — {label} · weight: {weight or 'none'}"
        )
        if row is None or col is None:
            self.query_one("#table", Static).update("[dim]pick a row and a column[/dim]")
            self.query_one("#note", Static).update("m toggles counts / row % · esc back")
            return
        try:
            table = crosstab(app.df, str(row), str(col), weight=weight, normalize=self.normalize)
        except (KeyError, ValueError) as exc:
            self.query_one("#table", Static).update(f"[red]{exc}[/red]")
            return
        self.query_one("#table", Static).update(table_text(table))
        self.query_one("#note", Static).update(
            f"{len(table.index)}×{len(table.columns)} cells · missing shown as its own category · "
            "m toggles counts / row %"
        )

    @on(Select.Changed)
    def _changed(self, event: Select.Changed) -> None:
        self._paint()

    def action_toggle_normalize(self) -> None:
        cycle = {None: "row", "row": "col", "col": None}
        self.normalize = cycle[self.normalize]
        self._paint()
