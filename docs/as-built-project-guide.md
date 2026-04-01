# As-Built Project Guide

> **Maintenance instructions:** This is the combined discovery and architecture guide.
> Update this document with every commit that adds, removes, or relocates systems, components, or settings.
> Include only what is needed for **discovery** — folder-level layout, system entry points, key functions, and architecture decisions.
> Do not document implementation details or individual file exports; reading the code handles that.

## Directory Structure

```
spellforge/
├── spellforge.py            # Single-file bootstrapper (main entry point)
├── pyproject.toml            # Project metadata, Ruff and pytest configuration
├── CLAUDE.md                 # Claude Code project context and coding guidelines
├── .gitignore                # Git ignore rules
├── .secrets.baseline         # detect-secrets baseline file
├── docs/
│   ├── prd.md                # Product Requirements Document
│   └── as-built-project-guide.md  # This file
├── .claude/
│   └── hooks/                # Claude Code hook scripts
└── tests/                    # pytest test suite
```

## Systems

### spellforge.py — Bootstrapper Entry Point

Single-file script that orchestrates all project setup. Run directly with `python spellforge.py`.

**Key classes:**
- `InstallChoices` — Dataclass holding user selections from the interactive menu (which optional tools to install)

**Key functions:**
- `show_installation_menu()` — Presents the interactive menu and returns an `InstallChoices` instance
- `ensure_*()` — Verify a tool is installed, install it if missing (e.g., `ensure_homebrew()`, `ensure_python()`)
- `install_*()` — Install a specific tool or dependency (e.g., `install_ruff()`, `install_detect_secrets()`)
- `write_*()` — Generate configuration files with correct paths baked in (e.g., `write_pyproject_toml()`, `write_claude_md()`)
- `verify_*()` — Post-install verification that a tool works correctly (e.g., `verify_git()`, `verify_ruff()`)
- `create_*()` — Create project scaffolding (e.g., `create_virtualenv()`, `create_git_hooks()`)

## Architecture Decisions

- **Single-file design** — The bootstrapper is one Python file. It runs once to set up a project and then its job is done. There is no reason to split it into modules.
- **Verify after every install step** — Each tool installation is immediately followed by a verification step to fail fast and provide clear error messages.
- **Tab indentation enforced by Ruff** — All generated Python files and the bootstrapper itself use tabs, configured in pyproject.toml.
- **detect-secrets via Homebrew with pip fallback** — Homebrew is the preferred installation method, but if unavailable, detect-secrets is installed via pip into the project virtualenv.
