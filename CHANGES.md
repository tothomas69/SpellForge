# Spellforge Hardening Pass — Changelog

A summary of changes applied to `spellforge.py` in this pass. The goal was to
fix the silent-failure mode that produced your `⚠ Ruff not found at
.../.venv/bin/ruff` error and to pin projects to Python 3.13.x instead of
inheriting whatever `python3` happened to resolve to.

## 0. pip / uv package manager choice (latest pass)

The installation menu now has a dedicated page where the user picks `pip`
(classic, always available once Python is) or `uv` (a much faster Rust-based
drop-in). The choice drives venv creation and every subsequent package
install:

- `create_venv()` dispatches to `python -m venv` or `uv venv --python
<python_bin>`, and now returns the venv's `python3` path (rather than a
  `pip` path) since a uv-created venv has no `pip` binary by design.
- `_pip_install()` was generalized into `_install_packages()`, which either
  runs the existing isolated `python -m pip install` flow or shells out to
  `uv pip install --python <venv_python>`.
- `verify_venv()` skips the pip-existence check under uv, since uv manages
  installs directly against the interpreter rather than through a pip binary
  in the venv.
- `ensure_uv()` installs uv via Homebrew if it's not already on PATH,
  following the same fatal-with-manual-instructions pattern as
  `ensure_python()` when Homebrew isn't available.
- Repair mode (`--repair`) is non-interactive and has no `InstallChoices` to
  read the original choice from, so `_detect_venv_package_manager()` reads
  the existing venv's `pyvenv.cfg` for uv's `uv = <version>` marker line
  (read _before_ any `--rebuild-venv` deletion) and re-targets the same
  manager instead of silently defaulting back to pip.

## 1. Secret-scanning hook rewrite

The pre-commit secret stage was rewritten after it repeatedly blocked
legitimate commits in a real project. The old design ran a whole-tree
`detect-secrets scan` and demanded the result equal the baseline exactly.
Three failure modes came out of that:

- **Self-reference loop.** The scan included `.secrets.baseline` itself. Once
  the baseline contained a hash, the next scan flagged that hash as a new
  finding, so `scan > .secrets.baseline` never converged.
- **Generated high-entropy strings.** Alembic migration files carry a random
  revision ID (e.g. `revision = "7c94f5e48cb0"`). The hex detector flags it,
  so every new migration blocked its own commit.
- **Exact-equality brittleness.** Any new high-entropy string anywhere in the
  tree (a UUID literal in a test, etc.) broke an otherwise-unrelated commit.

The fix, in `write_precommit_hook()` and `init_secrets_baseline()`:

- The hook now uses **`detect-secrets-hook --baseline <baseline>`** on the
  **staged files only** — the tool's purpose-built pre-commit entry point. It
  exits non-zero only on a genuinely new secret, not on any tree-wide diff.
- An `EXCLUDE_PATTERN` skips `.secrets.baseline` (kills the self-reference
  loop) and `alembic/versions/` migration files (kills the revision-ID false
  positive). The same pattern is applied when the baseline is first generated,
  so the baseline and the hook always agree.
- Inline `# pragma: allowlist secret` comments remain honored for one-off
  false positives, and the blocked-commit message now tells the user about
  that option as well as how to regenerate the baseline with the exclusions.
- A pre-existing wrapper/module fallback locates `detect-secrets-hook` next to
  the `detect-secrets` binary, with `$DETECT_SECRETS-hook` as a fallback.

Net effect: migrations, the baseline, and unrelated high-entropy strings no
longer block commits, while a real newly-introduced secret in a staged file
still does.

## 2. Python version pinning (3.13.x)

- New module-level constants near the top: `PYTHON_TARGET_MINOR = (3, 13)`,
  `PYTHON_TARGET_LABEL`, `PYTHON_TARGET_BIN_NAME` (`python3.13`),
  `PYTHON_TARGET_BREW_FORMULA` (`python@3.13`). Bumping the target is now a
  one-line change.
- Rewrote `ensure_python()`. It no longer accepts whatever `python3` is on
  PATH. New discovery order:
    1. `python3.13` on PATH
    2. `/opt/homebrew/opt/python@3.13/bin/python3.13` (Apple Silicon)
    3. `/usr/local/opt/python@3.13/bin/python3.13` (Intel)
    4. `brew --prefix python@3.13` lookup
    5. `brew install python@3.13` if brew is available
    6. Fatal with python.org / pyenv instructions if brew isn't available
- Rewrote `verify_python(python_bin)`. Now takes an explicit interpreter path
  and asserts `sys.version_info[:2] == (3, 13)`. Refuses to trust the
  binary's _name_ alone (wrapper shenanigans).
- Updated `requires-python` in the generated `pyproject.toml` from `">=3.11"`
  to `">=3.13,<3.14"`. Renders from the same constants so the two never
  drift apart.
- `verify_venv()` now also re-verifies the venv Python is 3.13 (defense in
  depth — `create_venv` should have already guaranteed this).

## 3. Stop silent reuse of wrong-version venvs

- `create_venv()` no longer blindly reuses an existing `.venv`. New
  `_venv_python_version()` helper reports the existing venv's actual major.
  minor; if it's not 3.13, Spellforge fatals with a clear "delete and rerun"
  message. The previous behavior — printing "skipping creation" and reusing
  whatever was there — was a major contributor to the failure mode you hit.

## 4. Hardened pip installs (the headline fix)

This is the change that prevents your specific failure from recurring.

- New helper `_isolated_pip_env()` returns an environment dict with:
    - `PIP_USER=0` (defeats `PIP_USER=1` from user environment)
    - `PIP_REQUIRE_VIRTUALENV=true` (extra paranoia)
    - `PIP_TARGET` and `PIP_PREFIX` removed (defeats redirected installs)
- New helper `_pip_install(pip_bin, packages, upgrade_pip_first=False)`
  invokes pip via `<venv>/bin/python3 -m pip install --no-user --isolated`
  instead of the venv's `pip` script directly. `--isolated` ignores user
  pip.conf entirely. `--no-user` overrides `user = true` in pip.conf.
- `run()` extended with optional `env=` parameter so the isolation env can
  be threaded through subprocess calls.
- All package installs (`install_base_packages`, `install_detect_secrets`
  pip fallback, `install_bandit`) routed through `_pip_install`. No more
  raw `pip_bin install` calls anywhere in the script.

## 5. Verification actually fatals now

`verify_packages()`:

- The dead `pass` after a missing-CLI-tool error is gone.
- Missing CLI tools and failed imports are aggregated into two lists.
- If either list is non-empty at the end, `fatal()` is called with a
  detailed message including the most likely root causes (network failure,
  user pip config, stale venv) and the diagnostic commands to run.
- This is the gate that was open before — your bootstrap could write a
  post-edit hook pointing at a non-existent ruff binary and exit clean.
  That door is now locked.

## 6. Guard the unguarded brew call

`install_detect_secrets()`: the `run(["brew", "install", "detect-secrets"])`
call now lives inside `if brew_available():`. Previously, on a machine
without Homebrew, this line crashed Spellforge with `FileNotFoundError`
instead of falling back to pip as intended. The pip-fallback branch now
also routes through `_pip_install` for isolation.

## 7. Repair mode

New `--repair PATH` flag for fixing an existing project without
re-bootstrapping it from scratch:

```bash
# Fix the current service_levels situation
python3 spellforge.py --repair /Users/tthomas/Documents/Coding/service_levels

# Or, if you suspect the venv itself is corrupt or wrong-version:
python3 spellforge.py --repair /Users/tthomas/Documents/Coding/service_levels --rebuild-venv
```

Repair mode runs ONLY: `ensure_python → verify_python → create_venv
(version-checked) → verify_venv → install_base_packages → verify_packages
→ write_post_edit_hook → verify_post_edit_hook`.

It does NOT touch: git history, pyproject.toml, CLAUDE.md, docs/, tests/,
settings.local.json, pre-commit hook, .gitignore, or anything else.

If watchdog is detected in the existing venv, it's automatically added to
the re-verification set.

## 8. Refactor

The monolithic `__main__` block was extracted into two functions:

- `do_fresh_install()` — the original interactive flow, unchanged in
  behavior.
- `do_repair(target_path, rebuild_venv=False)` — the new path.

`__main__` is now just an argparse dispatch. Bare `spellforge.py`
continues to launch the interactive fresh-install flow — backward-compatible.

## To use right now on service_levels

```bash
# Run from anywhere — the script is self-contained.
python3 /path/to/spellforge.py --repair /Users/tthomas/Documents/Coding/service_levels --rebuild-venv
```

The `--rebuild-venv` is recommended for your current situation since the
existing venv may have been created with the wrong Python version (or is
otherwise in a state where ruff didn't land). Repair mode will:

1. Ensure `python3.13` is installed (will `brew install python@3.13` if
   needed).
2. Delete the broken `.venv` (because of `--rebuild-venv`).
3. Create a fresh `.venv` with Python 3.13.
4. Install all base packages with strict pip isolation.
5. Verify every single package and CLI tool is actually present, fataling
   loudly if anything is missing.
6. Regenerate `.claude/hooks/post_edit.sh` with the correct ruff path.
7. Print a summary of what was repaired and what was preserved.
