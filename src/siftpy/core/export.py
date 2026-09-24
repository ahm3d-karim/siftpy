"""export.py — write the label dictionary out, into a folder you chose.

Rule from the plan: never write anywhere silently. Every export takes an
explicit directory, and a bad directory is an error with a sentence, not a
stack trace.
"""
from __future__ import annotations

from pathlib import Path

from siftpy.core.loader import FileMeta
from siftpy.core.profile import ColumnProfile


class ExportError(Exception):
    """Export could not happen, with a reason a human can act on."""


def check_dir(directory: str | Path) -> Path:
    p = Path(directory).expanduser()
    if not str(directory).strip():
        raise ExportError("No output directory given.")
    if not p.exists():
        raise ExportError(f"No such directory: {p}")
    if not p.is_dir():
        raise ExportError(f"Not a directory: {p}")
    return p


def dictionary_csv(meta: FileMeta, profiles: list[ColumnProfile]) -> str:
    lines = ["variable,dtype,label,n_missing,pct_missing,n_unique,range_or_top,flags"]
    for prof in profiles:
        cells = [
            prof.name,
            prof.dtype,
            prof.label,
            str(prof.n_missing),
            f"{prof.pct_missing:.1f}",
            str(prof.n_unique),
            prof.range_text,
            "|".join(prof.flags),
        ]
        lines.append(",".join(_csv_cell(c) for c in cells))
    return "\n".join(lines) + "\n"


def dictionary_markdown(meta: FileMeta, profiles: list[ColumnProfile]) -> str:
    rows = [
        f"# Data dictionary — {meta.path.name}",
        "",
        f"{meta.fmt} · {meta.n_rows:,} rows × {meta.n_cols} columns · "
        f"{meta.n_labelled}/{meta.n_cols} columns carry a variable label",
        "",
        "| variable | type | label | missing | unique | range / top values | flags |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for prof in profiles:
        rows.append(
            f"| `{prof.name}` | {prof.dtype} | {prof.label or '—'} | "
            f"{prof.n_missing} ({prof.missing_text}) | {prof.n_unique} | "
            f"{prof.range_text} | {prof.flag_text()} |"
        )
    rows.append("")
    if meta.value_labels:
        rows += ["## Value labels", ""]
        for name, mapping in meta.value_labels.items():
            pairs = ", ".join(f"{k} = {v}" for k, v in list(mapping.items())[:20])
            rows.append(f"- `{name}`: {pairs}")
        rows.append("")
    return "\n".join(rows)


def write_dictionary(
    directory: str | Path, meta: FileMeta, profiles: list[ColumnProfile], fmt: str = "md"
) -> Path:
    """Write <stem>-dictionary.<fmt> into a directory that must already exist."""
    target_dir = check_dir(directory)
    if fmt not in {"md", "csv"}:
        raise ExportError(f"Unsupported export format {fmt!r} (use 'md' or 'csv')")
    body = dictionary_markdown(meta, profiles) if fmt == "md" else dictionary_csv(meta, profiles)
    path = target_dir / f"{meta.path.stem}-dictionary.{fmt}"
    path.write_text(body, encoding="utf-8")
    return path


def _csv_cell(value: str) -> str:
    text = str(value)
    return f'"{text.replace(chr(34), chr(34) * 2)}"' if any(c in text for c in ',"\n') else text
