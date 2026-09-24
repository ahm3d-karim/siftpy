# siftpy

Survey-microdata profiler TUI. Open a `.dta` / `.sav` / `.csv` file in the
terminal and get the answers an RA actually needs: what the columns are, where
the missingness is, which variable is the weight, weighted cross-tabs, and a
reproducible cleaning script.

Built for the workflow where every dataset arrives as a mystery file and the
weight variable is tribal knowledge. Survey weights are first-class, and the
output is a recipe you can rerun, not a report you have to trust.

**Status: Stage 5 of 7.** Working today: open `.dta` / `.sav` / `.csv` with labels
intact, profile every column (missingness, cardinality, range or top values, and
flags for all-missing / constant / ID-shaped / high-cardinality), read the label
dictionary and export it to markdown + CSV into a folder you choose, pick the
weight variable from a ranked list of candidates with their evidence, and build
weighted or unweighted cross-tabs with missingness kept as its own category.
The LLM suggestions (stage 4) and the cleaning-script emitter (stage 6) are not
built yet and say so in the menu. The plan with per-stage done-when gates lives
outside the repo at `fde/siftpy-plan.md`.

## Run it

```bash
uv sync --extra test
uv run siftpy                  # or: .venv/Scripts/python.exe -m siftpy.cli
```

Keys: `↑/↓` move · `enter` select · `o` open a file · `m` counts/percent in a
cross-tab · `n` clear the weight · `e` export the dictionary · `esc` back · `q`
quit.

Or as a tool from GitHub:

```bash
uv tool install --from git+https://github.com/ahm3d-karim/siftpy siftpy-cli
siftpy
```

## Stack

Python 3.11+, [Textual](https://textual.textualize.io/) for the TUI, pandas and
pyreadstat for loading. An LLM is optional and BYOK — with no key configured the
app runs rules-only and never touches the network.

MIT.
