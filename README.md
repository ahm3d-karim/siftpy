# siftpy

Survey-microdata profiler TUI. Open a `.dta` / `.sav` / `.csv` file in the
terminal and get the answers an RA actually needs: what the columns are, where
the missingness is, which variable is the weight, weighted cross-tabs, and a
reproducible cleaning script.

Built for the workflow where every dataset arrives as a mystery file and the
weight variable is tribal knowledge. Survey weights are first-class, and the
output is a recipe you can rerun, not a report you have to trust.

**Status: Stage 1.** The shell, the menu and the loader work: `o` opens a file
picker, `.dta` / `.sav` / `.csv` load with their variable and value labels kept
beside the frame, and a bad path becomes a readable notice instead of a
traceback. Menu entries for later stages say which stage turns them on. The
plan, with per-stage done-when gates, lives outside the repo at
`fde/siftpy-plan.md`.

## Run it

```bash
uv sync --extra test
uv run siftpy                  # or: .venv/Scripts/python.exe -m siftpy.cli
```

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
