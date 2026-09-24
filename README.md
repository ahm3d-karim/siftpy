# siftpy

Survey-microdata profiler TUI. Open a `.dta` / `.sav` / `.csv` file in the
terminal and get the answers an RA actually needs: what the columns are, where
the missingness is, which variable is the weight, weighted cross-tabs, and a
reproducible cleaning script.

Built for the workflow where every dataset arrives as a mystery file and the
weight variable is tribal knowledge. Survey weights are first-class, and the
output is a recipe you can rerun, not a report you have to trust.

**Status: Stage 0 only.** The TUI shell (welcome banner, 8-item menu) and the
CLI entry point exist; every menu item is disabled and labelled with the stage
that turns it on. The plan, with per-stage done-when gates, lives outside the
repo at `fde/siftpy-plan.md`.

## Run it

```bash
uv sync --extra test
.venv/Scripts/python.exe -m siftpy.cli      # Windows
python -m siftpy.cli                        # after `uv sync` anywhere
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
