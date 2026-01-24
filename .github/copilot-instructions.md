<!-- Copilot instructions for AI coding agents -->
# Repo guide for AI coding agents

Purpose
- Short, actionable guidance so an AI agent can be immediately productive in this multi-project workspace.

Quick orientation
- This workspace is a collection of many small projects and experiments (not a single monolith). Major top-level folders to consider first:
  - `AI Code Prompts/` — AI agents and prompt engineering experiments (e.g., Calendar Agent).
  - `Machine_Learning/` — General ML experiments and notebooks.
  - `Azure Coding Project/azure-ml-labs/` — Azure ML examples and infra; contains its own contributor docs: [Azure Coding Project/azure-ml-labs/readme.md](../Azure Coding Project/azure-ml-labs/readme.md).
  - `Jupyter Coding Projects/` — Collection of Jupyter notebooks; treat them as experiment-driven code.
  - `Coding Projects/` — Assorted scripts and small apps (Python, Web, etc.); check subfolders for README and entry scripts.
  - `Data_Sources/` & `Azure Data Scentist/` — Common locations for datasets and input files.
  - `Universal Coding.code-workspace` — VS Code workspace file with tasks (e.g. Swift build/run tasks).

How this repo is typically used
- Interactive exploration: many notebooks and data files. Prefer to run code interactively (Jupyter) for experiments.
- Per-subproject execution: Most folders are standalone. Look for a README, a top-level script (e.g., `main.py`, `run.sh`), or a `pyproject.toml`/`requirements.txt` before changing dependencies.

Developer workflows and commands
- Use the repo-local virtualenv: `.venv/` exists at the workspace root. Typical activation:
  - `source .venv/bin/activate` (macOS)
  - then run Python scripts with `python path/to/script.py`.
- Swift tasks are available in the VS Code workspace tasks: `swift build` and `swift run` (see `Universal Coding.code-workspace`).
- Not every subfolder has automated tests — run notebooks and scripts manually where present.

Project-specific conventions
- Experiments live in notebooks under `Jupyter Coding Projects/` and `Machine_Learning/`. When transforming a notebook into a script, keep data-loading cells grouped at the top and preserve preprocessing steps.
- Datasets and CSVs often live under `Azure Data Scentist/` and `Data_Sources/`. Avoid moving large raw data files; reference them by relative path.
- Many smaller utilities are organised by topic inside `Coding Projects/`. Follow existing naming (folders per topic) and add README when adding a new topic.

Integration and external dependencies
- Azure: several samples use Azure SDKs / Azure ML (search for `azure` import). If changing Azure code, keep credentials out of the repo and respect any README in `azure-ml-labs/`.
- Python dependencies are managed locally in `.venv`; some subprojects may include their own dependency files — prefer per-project dependency files.

What to change and what to avoid
- Safe changes: small bug fixes, documentation/README updates, per-subproject scripts, and refactors limited to a single subfolder.
- Avoid: modifying `.venv/`, moving large datasets, or making sweeping repo-wide dependency upgrades without running relevant notebooks/scripts.

-Useful file references
- VS Code workspace/tasks: [Universal Coding.code-workspace](../Universal Coding.code-workspace)
- Azure ML examples: [Azure Coding Project/azure-ml-labs/readme.md](../Azure Coding Project/azure-ml-labs/readme.md)

Agent behavior guidance
- Always locate and read the README (or top-level script) in the specific subfolder you plan to edit before making changes.
- When adding runnable examples, include a one-line run command and expected output in the subfolder README.
- For any code that uses Azure, leave placeholders for credentials and update only configuration templates, not secrets.
- If you introduce a new dependency, add a per-project `requirements.txt` or update an existing dependency file in that subfolder (do not add global changes to `.venv`).

When in doubt: ask the user which subproject they want to target and whether they can run experiments locally (notebooks, datasets, and credentials are often local).

If you need more context
- Ask to run quick repository scans (list files in a subfolder, open README, run a short script). Provide the exact paths you want analyzed.

---
Please review — tell me which subfolder to focus on and I will tailor next steps.
