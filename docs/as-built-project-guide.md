# As-Built Project Guide

> **Maintenance instructions:** This is the combined discovery and architecture guide.
> Update this document with every commit that adds, removes, or relocates systems, components, or settings.
> Include only what is needed for **discovery** — folder-level layout, system entry points, key functions, and architecture decisions.
> Do not document implementation details or individual file exports; reading the code handles that.

## Directory Structure

```
spellforge/
├── spellforge.py            # Single-file bootstrapper (main entry point)
├── tests/
│   ├── test_spellforge_bootstrap.py  # Validates project state on disk (pre-commit hook, venv, etc.)
│   ├── test_spellforge_config.py     # Validates config file contents (pyproject.toml, CLAUDE.md)
│   └── test_spellforge_unit.py       # Unit tests: calls spellforge.py functions via tmp_path
├── pyproject.toml            # Project metadata, Ruff and pytest configuration
├── requirements.txt          # Runtime dependencies for spellforge.py itself
├── CLAUDE.md                 # Claude Code project context and coding guidelines
├── README.md                 # User-facing documentation
├── CHANGES.md                # Changelog for the most recent hardening pass
├── LICENSE                   # MIT license
├── .gitignore                # Git ignore rules
├── .secrets.baseline         # detect-secrets baseline file
├── .prettierrc               # Prettier config (generated when frontend tools opted in)
├── .prettierignore           # Prettier ignore list (generated when frontend tools opted in)
├── eslint.config.js          # ESLint flat config v9+ (generated when frontend tools opted in)
├── docs/
│   ├── prd.md                # Product Requirements Document
│   └── as-built-project-guide.md  # This file
├── images/                   # README assets
├── .claude/
│   └── settings.local.json   # Claude Code permissions (no hooks; quality gate lives in git pre-commit)
```

## Systems

### spellforge.py — Bootstrapper Entry Point

Single-file script that orchestrates all project setup. Two run modes, dispatched via argparse:

- `python spellforge.py` — Fresh interactive install (the default).
- `python spellforge.py --repair PATH [--rebuild-venv]` — Repair mode for an existing Spellforge-managed project. Re-validates Python, optionally rebuilds the venv, reinstalls base packages with strict pip isolation, and regenerates the post-edit hook. Does **not** touch git history, `pyproject.toml`, `CLAUDE.md`, `docs/`, `tests/`, or any other project config.

**Module-level constants:**
- `PYTHON_TARGET_MINOR`, `PYTHON_TARGET_LABEL`, `PYTHON_TARGET_BIN_NAME`, `PYTHON_TARGET_BREW_FORMULA` — Single source of truth for the pinned Python version (currently 3.13). Bumping the target is a one-line change.
- `BASE_PACKAGES` — The list of packages installed into every new project venv.

**Key classes:**
- `InstallChoices` — Dataclass holding user selections from the interactive menu (which optional tools to install)

**Key entry-point functions:**
- `do_fresh_install()` — The full interactive bootstrap flow.
- `do_repair(target_path, rebuild_venv=False)` — Repair flow; runs only Python/venv/base-packages/pre-commit-hook steps.
- `_parse_args()` — argparse dispatcher; `__main__` is just a thin shim over this.

**Key functions:**
- `show_installation_menu()` — Presents the interactive menu (paginated: required tools page → optional tools page → confirmation) and returns an `InstallChoices` instance
- `print_summary()` — Paginated final summary: page 1 shows what was installed, page 2 shows next steps, a "Testing setup required" notice (pytest is not automatic; user must replace placeholder, narrow `--cov`, and add CI), and useful paths
- `press_any_key(prompt)` — UI helper that waits for a single keypress (raw terminal mode) to advance between pages
- `banner()` — Clears the screen and prints the Spellforge header
- `ensure_*()` — Verify a tool is installed, install it if missing (e.g., `ensure_homebrew()`, `ensure_python()`)
- `install_*()` — Install a specific tool or dependency (e.g., `install_ruff()`, `install_detect_secrets()`)
- `write_*()` — Generate configuration files with correct paths baked in (e.g., `write_pyproject_toml()`, `write_claude_md()`)
- `verify_*()` — Post-install verification that a tool works correctly (e.g., `verify_git()`, `verify_ruff()`, `verify_packages()`)
- `create_*()` — Create project scaffolding (e.g., `create_virtualenv()`, `create_git_hooks()`)
- `_isolated_pip_env()`, `_pip_install()`, `_venv_python_version()` — Internal helpers that enforce strict pip isolation and version checks (see Architecture Decisions).

## Architecture Decisions

- **Single-file design** — The bootstrapper is one Python file. It runs once to set up a project and then its job is done. There is no reason to split it into modules.
- **Verify after every install step** — Each tool installation is immediately followed by a verification step to fail fast and provide clear error messages. `verify_packages()` aggregates failures and calls `fatal()` with diagnostics; the bootstrapper does **not** continue past missing CLI tools or failed imports.
- **Tab indentation enforced by Ruff** — All generated Python files and the bootstrapper itself use tabs, configured in pyproject.toml.
- **detect-secrets via Homebrew with pip fallback** — Homebrew is the preferred installation method, but if unavailable, detect-secrets is installed via pip into the project virtualenv. The brew call is gated by `brew_available()` so machines without brew fall through to pip cleanly.
- **Python version pinning (3.13.x)** — Spellforge refuses to bootstrap against an arbitrary `python3` on PATH. It searches for `python3.13` in standard locations (PATH, Apple Silicon and Intel brew keg paths, then `brew --prefix`), falling back to `brew install python@3.13` if needed. The target version is controlled by `PYTHON_TARGET_*` constants. Rationale: `brew install python3` tracks the latest formula (currently 3.14), which is too new for our typical dependency matrix.
- **Strict pip isolation** — All package installs go through `_pip_install()`, which invokes `<venv>/bin/python3 -m pip install --no-user --isolated` with an environment that sets `PIP_USER=0` and `PIP_REQUIRE_VIRTUALENV=true` and strips `PIP_TARGET` / `PIP_PREFIX`. This prevents user-level pip configuration from redirecting installs outside the project venv (the original silent-failure mode).
- **No silent reuse of wrong-version venvs** — `create_venv()` inspects an existing `.venv` via `_venv_python_version()`; if the venv's Python doesn't match `PYTHON_TARGET_MINOR`, Spellforge fatals with a "delete and rerun" message instead of proceeding.
- **Repair mode is scope-restricted by design** — `do_repair()` only re-runs the Python/venv/base-packages steps and regenerates the git pre-commit hook (re-pointing it at the current ruff/detect-secrets paths). It deliberately does not regenerate project config or scaffolding, so it's safe to run against a project with local edits.
- **Quality gate at pre-commit, not post-edit** — Ruff format + lint and detect-secrets scanning run as a single git pre-commit hook (`.git/hooks/pre-commit`), generated by `write_precommit_hook()`. Earlier versions ran ruff after every Claude file edit via a `PostToolUse` hook in `settings.local.json`; that was removed because it made editing sessions noticeably slow. Tests and coverage are not in the pre-commit hook — they run manually or in CI.
- **Coverage scoped to spellforge.py at 24% threshold** — `--cov=spellforge` measures only the source file (not the test files). The threshold is 24% rather than the usual 80% because ~75% of lines are in subprocess-heavy `install_*`, `ensure_*`, and `verify_*` functions that require live tools (Homebrew, pip, a real venv) and cannot be meaningfully unit-tested. The covered 24% is all of the content-generation (`write_*`, `create_*`) and pure helper functions — the logic that matters most to test. `test_spellforge_unit.py` covers these; the two other test files validate the on-disk project state.
- **Idempotent re-bootstrap** — Steps that mutate shared config files check whether their section already exists before appending (`write_pyproject_toml()` for `[tool.ruff]`, `install_bandit()` for `[tool.bandit]`). `verify_tests_directory()` accepts any `test_*.py` file rather than requiring the original `test_placeholder.py`, so re-bootstrapping a project whose placeholder has been replaced by real tests does not fail. Net effect: running `python spellforge.py` against an already-bootstrapped project is a safe no-op rather than a duplicate-config or verification crash.
