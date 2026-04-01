#!/usr/bin/env python3
"""
spellforge.py - Claude-powered project bootstrapper
Conjures a fully configured Python project from nothing: git, venv,
ruff, detect-secrets, Claude Code, hooks, and all config files.
Verbose + colorful output throughout.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# =============================================================================
# ANSI COLOR HELPERS
# These let us print colorful, formatted output to the terminal.
# =============================================================================


class C:
	"""Terminal color codes and helper print functions."""

	RESET = "\033[0m"
	BOLD = "\033[1m"
	RED = "\033[91m"
	GREEN = "\033[92m"
	YELLOW = "\033[93m"
	BLUE = "\033[92m"  # bright green - replaces washed-out blue
	MAGENTA = "\033[95m"
	CYAN = "\033[96m"
	WHITE = "\033[97m"


def banner():
	"""
	Clear the screen and print the Spellforge terminal banner.
	Styled to evoke the heraldic logo - runic border, fantasy serif feel,
	tool chips listed across the bottom.
	"""
	# Clear the screen and move cursor to top-left
	print("[2J[H", end="")
	# Top runic border
	print(f"""
{C.MAGENTA}{C.BOLD}        🔨  S P E L L F O R G E  🔨{C.RESET}
{C.WHITE}        Project Bootstrapper for Claude Code{C.RESET}
{C.BLUE}        git · venv · ruff · detect-secrets · claude code · hooks · pytest · .gitignore · CLAUDE.md · bandit{C.RESET}
""")


def step(emoji, message):
	"""Print a step header — makes it easy to follow progress."""
	print(f"\n{C.CYAN}{C.BOLD}{'─' * 60}{C.RESET}")
	print(f"{C.BOLD}{emoji}  {message}{C.RESET}")
	print(f"{C.CYAN}{'─' * 60}{C.RESET}")


def info(message):
	"""Print an informational message."""
	print(f"  {C.BLUE}ℹ{C.RESET}  {message}")


def success(message):
	"""Print a success message."""
	print(f"  {C.GREEN}✔{C.RESET}  {message}")


def warning(message):
	"""Print a warning message."""
	print(f"  {C.YELLOW}⚠{C.RESET}  {message}")


def error(message):
	"""Print an error message."""
	print(f"  {C.RED}✘{C.RESET}  {message}")


def fatal(message):
	"""Print a fatal error and exit the script."""
	print(f"\n{C.RED}{C.BOLD}💀 FATAL: {message}{C.RESET}\n")
	sys.exit(1)


# =============================================================================
# SHELL COMMAND RUNNER
# Wraps subprocess so we get consistent output and error handling.
# =============================================================================


def run(cmd, cwd=None, capture=False, check=True):
	"""
	Run a shell command.

	Args:
	    cmd: List of command parts e.g. ['git', 'init']
	    cwd: Working directory to run the command in
	    capture: If True, return stdout instead of printing it
	    check: If True, raise an error on non-zero exit code

	Returns:
	    CompletedProcess result object
	"""
	info(f"Running: {C.YELLOW}{' '.join(cmd)}{C.RESET}")
	result = subprocess.run(
		cmd,
		cwd=cwd,
		capture_output=capture,
		text=True,
		check=False,  # We handle errors manually for better messages
	)
	if check and result.returncode != 0:
		error(f"Command failed: {' '.join(cmd)}")
		if result.stderr:
			print(f"    {C.RED}{result.stderr.strip()}{C.RESET}")
		raise SystemExit(1)
	return result


# =============================================================================
# STEP 1 — ASK FOR TARGET PROJECT PATH
# =============================================================================


def get_project_path():
	"""
	Prompt the user for the target project directory.
	Creates it if it doesn't exist. Returns a resolved Path object.
	"""
	step("📁", "Project Location")

	print(f"""
  {C.WHITE}Where should your new project live?{C.RESET}
  {C.BLUE}You can enter an absolute path or a path relative to your home directory.{C.RESET}
  {C.BLUE}Example: ~/Developer/my_project  or  /Users/you/projects/my_project{C.RESET}
""")

	while True:
		# Prompt for input
		raw = input(f"  {C.BOLD}{C.MAGENTA}➜ Project path: {C.RESET}").strip()

		if not raw:
			warning("Path cannot be empty. Please try again.")
			continue

		# Expand ~ and resolve to absolute path
		path = Path(raw).expanduser().resolve()
		info(f"Resolved path: {C.YELLOW}{path}{C.RESET}")

		# If it already exists, confirm they want to use it
		if path.exists():
			if path.is_file():
				error("That path points to a file, not a directory. Please choose a directory.")
				continue
			warning(f"Directory already exists: {path}")
			confirm = (
				input(f"  {C.BOLD}Use this existing directory? (y/n): {C.RESET}").strip().lower()
			)
			if confirm != "y":
				info("OK, let's try a different path.")
				continue
			success(f"Using existing directory: {path}")

		else:
			# Directory doesn't exist — offer to create it
			confirm = (
				input(f"  {C.BOLD}Directory does not exist. Create it? (y/n): {C.RESET}")
				.strip()
				.lower()
			)
			if confirm != "y":
				info("OK, let's try a different path.")
				continue
			path.mkdir(parents=True, exist_ok=True)
			success(f"Created directory: {path}")

		return path


# =============================================================================
# STEP 2 — HOMEBREW
# Homebrew is our package manager for macOS. Almost everything else depends
# on it, so we check for it first and install if missing.
# =============================================================================


def brew_available() -> bool:
	"""
	Return True if Homebrew is installed and on PATH.
	Used by other functions to decide whether to use brew or fall back to
	an alternative install method. Corporate environments often block brew.
	"""
	return shutil.which("brew") is not None


def ensure_homebrew():
	"""
	Check if Homebrew is available and report its status.
	Homebrew is optional - if not present we fall back to alternative
	install methods for each tool. We never force-install brew because
	corporate environments may explicitly prohibit it.
	"""
	step("🍺", "Homebrew")

	if brew_available():
		result = run(["brew", "--version"], capture=True, check=False)
		success(f"Homebrew available: {result.stdout.strip().splitlines()[0]}")
		info("Will use Homebrew to install system tools.")

		# On Apple Silicon, brew lives in /opt/homebrew/bin - ensure it's on PATH
		brew_path = "/opt/homebrew/bin"
		if brew_path not in os.environ.get("PATH", ""):
			os.environ["PATH"] = brew_path + ":" + os.environ.get("PATH", "")
			info(f"Added {brew_path} to PATH for this session.")
	else:
		warning("Homebrew not found - will use fallback install methods for each tool.")
		info("This is fine for corporate environments where brew is not permitted.")
		info("To install Homebrew manually later: https://brew.sh")


# =============================================================================
# STEP 3 — GIT
# We need git for version control and for the pre-commit secret scanning hook.
# =============================================================================


def ensure_git():
	"""
	Check if git is installed.
	Install via Homebrew if available, otherwise prompt the user to install
	Xcode Command Line Tools which includes git on macOS.
	"""
	step("🗂️", "Git")

	if shutil.which("git"):
		result = run(["git", "--version"], capture=True, check=False)
		success(f"Git already installed: {result.stdout.strip()}")
		return

	if brew_available():
		warning("Git not found - installing via Homebrew...")
		run(["brew", "install", "git"])
		success("Git installed successfully!")
	else:
		# On macOS, git ships with Xcode Command Line Tools
		warning("Git not found and Homebrew is not available.")
		info("Attempting to install via Xcode Command Line Tools...")
		result = subprocess.run(
			["xcode-select", "--install"], capture_output=True, text=True, check=False
		)
		# xcode-select --install exits non-zero if already installed, that's fine
		info("If a dialog appeared, complete the installation then re-run Spellforge.")
		info("Alternatively, download git from: https://git-scm.com/download/mac")
		# Check if git is now available
		if not shutil.which("git"):
			fatal(
				"Git is required but could not be installed automatically. "
				"Please install git manually and re-run Spellforge."
			)
		success("Git is now available!")


def init_git_repo(project_path: Path):
	"""
	Initialize a git repository in the project directory, but only if
	one doesn't already exist. We never clobber an existing repo.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	git_dir = project_path / ".git"

	if git_dir.exists():
		# Already a git repo — leave it alone
		warning(f".git already exists in {project_path} - skipping git init.")
		return

	info("No .git directory found - initializing a new git repository...")
	run(["git", "init", str(project_path)])
	success("Git repository initialized!")


# =============================================================================
# STEP 4 — PYTHON + VIRTUAL ENVIRONMENT
# We use the system python3 (whatever is active via brew) and create a
# project-local venv so packages don't pollute the global environment.
# =============================================================================

# The base packages to install in every new project venv.
# datetime and os are Python builtins — no install needed for those.
BASE_PACKAGES = [
	"pandas",  # Data manipulation and analysis
	"requests",  # HTTP requests made simple
	"python-dotenv",  # Load .env files into environment variables
	"pydantic",  # Data validation using Python type hints
	"pypdf",  # Read and write PDF files
	"ruff",  # Fast Python linter and formatter (also used by Claude hook)
	"pytest",  # Testing framework - required by Definition of Done
	"pytest-cov",  # Coverage reporting - enforces 80% minimum per CLAUDE.md
	"rich",  # Beautiful terminal output - colors, tables, progress bars
	"loguru",  # Simple powerful logging - timestamps, color by level, zero config
]


def ensure_python():
	"""
	Check that python3 is available.
	Install via Homebrew if available, otherwise direct the user to
	python.org — the official installer works fine on corporate machines.
	Returns the path to the python3 executable to use.
	"""
	step("🐍", "Python 3")

	if shutil.which("python3"):
		result = run(["python3", "--version"], capture=True, check=False)
		success(f"Python already installed: {result.stdout.strip()}")
		return shutil.which("python3")

	if brew_available():
		warning("python3 not found - installing via Homebrew...")
		run(["brew", "install", "python3"])
		success("Python 3 installed successfully!")
		return shutil.which("python3")

	# No brew - python3 must be installed manually
	fatal(
		"python3 not found and Homebrew is not available to install it.\n"
		"  Please install Python 3 from https://www.python.org/downloads/\n"
		"  Then re-run Spellforge."
	)


def create_venv(project_path: Path, python_bin: str):
	"""
	Create a Python virtual environment inside the project directory.
	Skips creation if the venv already exists.

	Args:
	    project_path: The resolved Path to the project root directory.
	    python_bin: Path to the python3 executable to use.

	Returns:
	    Path to the venv's pip executable (used for package installs).
	"""
	step("📦", "Python Virtual Environment")

	venv_path = project_path / ".venv"
	pip_bin = venv_path / "bin" / "pip"

	if venv_path.exists():
		warning(f".venv already exists at {venv_path} - skipping creation.")
	else:
		info(f"Creating virtual environment at {venv_path}...")
		run([python_bin, "-m", "venv", str(venv_path)])
		success("Virtual environment created!")

	return str(pip_bin)


def install_base_packages(pip_bin: str, project_path: Path):
	"""
	Install the base package set into the project venv.
	Uses pip from the venv so packages are isolated to this project.

	Args:
	    pip_bin: Path to the venv's pip executable.
	    project_path: Used for display/context only.
	"""
	step("📚", "Installing Base Packages")

	info(f"Packages to install: {C.YELLOW}{', '.join(BASE_PACKAGES)}{C.RESET}")

	# Upgrade pip first — old pip versions can cause install failures
	info("Upgrading pip to latest version...")
	run([pip_bin, "install", "--upgrade", "pip"])

	# Install all base packages in one pip call for speed
	info("Installing base packages...")
	run([pip_bin, "install"] + BASE_PACKAGES)

	success(f"All {len(BASE_PACKAGES)} base packages installed!")

	# Show what's installed so the user has a clear record
	info("Installed package versions:")
	result = run([pip_bin, "freeze"], capture=True, check=False)
	for line in result.stdout.strip().splitlines():
		# Only show our base packages, not pip's own deps
		if any(pkg.lower().replace("-", "_") in line.lower() for pkg in BASE_PACKAGES):
			print(f"    {C.GREEN}{line}{C.RESET}")


# =============================================================================
# STEP 5 — DETECT-SECRETS
# Scans commits for accidentally included secrets (API keys, passwords, etc.)
# Prefer the Homebrew version; fall back to pip if brew install fails.
# =============================================================================


def install_detect_secrets(pip_bin: str):
	"""
	Install detect-secrets for pre-commit secret scanning.
	Tries Homebrew first (preferred, system-wide). Falls back to pip
	into the venv if brew is unavailable or the install fails.

	Args:
	    pip_bin: Path to the venv pip, used as fallback install target.

	Returns:
	    Path string to the detect-secrets executable that was installed.
	"""
	step("🕵️", "detect-secrets (Secret Scanning)")

	# ── Try Homebrew first ────────────────────────────────────────────────────
	info("Attempting to install detect-secrets via Homebrew (preferred)...")
	brew_result = run(["brew", "install", "detect-secrets"], check=False)

	if brew_result.returncode == 0:
		detect_secrets_bin = shutil.which("detect-secrets")
		if detect_secrets_bin:
			success(f"detect-secrets installed via Homebrew: {detect_secrets_bin}")
			return detect_secrets_bin
		warning(
			"brew install succeeded but detect-secrets not found on PATH - falling back to pip."
		)
	else:
		warning("Homebrew install failed - falling back to pip install into venv.")

	# ── Fallback: install into the venv via pip ───────────────────────────────
	info("Installing detect-secrets into venv via pip...")
	run([pip_bin, "install", "detect-secrets"])

	# The venv bin directory is one level up from pip itself
	venv_bin_dir = Path(pip_bin).parent
	detect_secrets_bin = str(venv_bin_dir / "detect-secrets")

	if not Path(detect_secrets_bin).exists():
		fatal("detect-secrets install failed via both Homebrew and pip. Cannot continue.")

	success(f"detect-secrets installed via pip: {detect_secrets_bin}")
	return detect_secrets_bin


def init_secrets_baseline(project_path: Path, detect_secrets_bin: str):
	"""
	Create the initial .secrets.baseline file that detect-secrets uses
	to track known secrets in the repo. This is required before the
	pre-commit hook will work correctly.

	Args:
	    project_path: The resolved Path to the project root directory.
	    detect_secrets_bin: Path to the detect-secrets executable.
	"""
	baseline_path = project_path / ".secrets.baseline"

	if baseline_path.exists():
		warning(".secrets.baseline already exists - skipping baseline creation.")
		return

	info("Generating initial .secrets.baseline file...")
	result = run([detect_secrets_bin, "scan"], cwd=str(project_path), capture=True, check=False)

	if result.returncode != 0:
		warning(f"detect-secrets scan returned an error: {result.stderr.strip()}")
		warning("Continuing - you can run 'detect-secrets scan > .secrets.baseline' manually.")
		return

	# Write the JSON output from detect-secrets scan to the baseline file
	baseline_path.write_text(result.stdout)
	success(f".secrets.baseline created at {baseline_path}")


# =============================================================================
# STEP 6 — RUFF CONFIGURATION
# Ruff is our linter and formatter. We write a pyproject.toml into the project
# root so ruff knows how to check this project's code.
# =============================================================================

# Full pyproject.toml content written to the project root.
# Includes:
#   [project]      — package metadata and declared dependencies
#   [tool.ruff]    — linter/formatter settings matching CLAUDE.md coding standards
#   [tool.pytest]  — test discovery and coverage enforcement
PYPROJECT_CONTENT = """
[project]
name = "{project_name}"
version = "0.1.0"
description = ""
requires-python = ">=3.11"
dependencies = [
    "pandas",
    "requests",
    "python-dotenv",
    "pydantic",
    "pypdf",
]

[tool.ruff]
# Use tabs for indentation — matches project coding standards
indent-width = 4
line-length  = 100

[tool.ruff.format]
# Enforce tabs, not spaces, as required by coding guidelines
indent-style = "tab"

[tool.ruff.lint]
# E/W = pycodestyle, F = pyflakes, I = isort import sorting
select = ["E", "F", "I", "W"]

# Rules we deliberately ignore:
#   E501 — line too long (we trust developers on long strings/comments)
#   E303 — too many blank lines (occasionally useful for readability)
ignore = ["E501", "E303", "W191", "E101"]

[tool.pytest.ini_options]
# Discover all tests/ directories recursively
testpaths = ["tests"]
# Enforce 80% minimum coverage on every run — matches Definition of Done
addopts = "--cov=. --cov-report=term-missing --cov-fail-under=80"
# AI NOTE: This coverage config is for the projects Spellforge creates, not for Spellforge itself.
# Spellforge is a bootstrapper script — it has no application code to cover.
""".strip()


def configure_pyproject(project_path: Path, project_name: str):
	"""
	Write the full pyproject.toml into the project root, including:
	  - [project] metadata section with declared dependencies
	  - [tool.ruff] linter/formatter settings
	  - [tool.pytest.ini_options] test discovery and coverage enforcement

	If pyproject.toml already exists and contains [tool.ruff], skips.
	If it exists but lacks [tool.ruff], appends only the tool sections.

	Args:
	    project_path:  The resolved Path to the project root directory.
	    project_name:  The project name to embed in the [project] section.
	"""
	step("🔍", "pyproject.toml - Project Config + Ruff + Pytest")

	pyproject_path = project_path / "pyproject.toml"

	# Substitute the project name into the template
	rendered = PYPROJECT_CONTENT.format(project_name=project_name)

	if pyproject_path.exists():
		existing = pyproject_path.read_text()
		if "[tool.ruff]" in existing:
			warning("pyproject.toml already contains [tool.ruff] - skipping.")
			return
		# File exists but no ruff config — append just the tool sections
		info("pyproject.toml exists - appending ruff + pytest config...")
		tool_section = rendered[rendered.index("[tool.ruff]") :]
		with pyproject_path.open("a") as f:
			f.write(f"\n\n{tool_section}\n")
	else:
		# Fresh project — write the full file including [project] metadata
		info("Creating pyproject.toml with project metadata + ruff + pytest config...")
		pyproject_path.write_text(rendered + "\n")

	success(f"pyproject.toml written: {pyproject_path}")
	info(f"  Project name : {project_name}")
	info("  Ruff         : tabs, line length 100, pycodestyle + pyflakes + isort")
	info("  Pytest       : tests/ directory, 80% coverage enforced")


# =============================================================================
# STEP 7 — CLAUDE CODE
# Install Claude Code globally via npm. Claude Code requires Node.js,
# so we install that via Homebrew first if it's missing.
# =============================================================================


def ensure_node():
	"""
	Check if Node.js (and npm) is available.
	Install via Homebrew if available, otherwise direct the user to nodejs.org.
	Claude Code is an npm package and requires Node to run.
	"""
	if shutil.which("node"):
		result = run(["node", "--version"], capture=True, check=False)
		success(f"Node.js already installed: {result.stdout.strip()}")
		return

	if brew_available():
		warning("Node.js not found - installing via Homebrew...")
		run(["brew", "install", "node"])
		success("Node.js installed!")
		return

	# No brew - node must be installed manually
	fatal(
		"Node.js not found and Homebrew is not available to install it.\n"
		"  Node.js is required to install Claude Code.\n"
		"  Please install Node.js from https://nodejs.org/\n"
		"  Then re-run Spellforge."
	)


def install_claude_code():
	"""
	Install Claude Code globally via npm.
	Claude Code is the CLI tool that powers AI-assisted development.
	Skips installation if 'claude' is already on PATH.
	"""
	step("🤖", "Claude Code")

	# ── Ensure Node.js is available first ────────────────────────────────────
	ensure_node()

	# ── Check if claude is already installed ─────────────────────────────────
	if shutil.which("claude"):
		result = run(["claude", "--version"], capture=True, check=False)
		success(f"Claude Code already installed: {result.stdout.strip()}")
		return

	info("Installing Claude Code globally via npm...")
	run(["npm", "install", "-g", "@anthropic-ai/claude-code"])
	success("Claude Code installed!")
	info("Run 'claude' in your project directory to start a session.")


# =============================================================================
# STEP 8 — PROJECT DIRECTORY STRUCTURE
# Create the .claude/ and docs/ directory trees that Claude Code and
# the as-built project guide system expect to find.
# =============================================================================


def create_directory_structure(project_path: Path):
	"""
	Create the standard directory structure for a Claude-powered project:

	    .claude/
	        hooks/        ← post_edit.sh lives here
	    docs/
	        prd.md                    ← Product Requirements Doc
	        as-built-project-guide.md ← as-built project guide architecture document

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	step("📂", "Project Directory Structure")

	# Define all directories we need to create
	directories = [
		project_path / ".claude" / "hooks",
		project_path / "docs",
	]

	for directory in directories:
		if directory.exists():
			warning(f"Directory already exists - skipping: {directory}")
		else:
			directory.mkdir(parents=True, exist_ok=True)
			success(f"Created: {directory}")


# =============================================================================
# STEP 9 — WRITE PROJECT FILES
# Write settings.local.json, post_edit.sh, CLAUDE.md, and docs/ docs.
# All hardcoded paths are replaced with the actual project path at write time.
# =============================================================================


def write_settings_local(project_path: Path):
	"""
	Write .claude/settings.local.json with dynamic paths and a clean
	set of permitted Claude Code commands for a generic Python project.
	The hook path is set to the actual project location at write time.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	step("⚙️", "Claude Code Settings (settings.local.json)")

	settings_path = project_path / ".claude" / "settings.local.json"
	hook_path = str(project_path / ".claude" / "hooks" / "post_edit.sh")

	settings = {
		"permissions": {
			"allow": [
				# Git operations — pushing, committing, staging
				"Bash(git remote:*)",
				"Bash(git push:*)",
				"Bash(git add:*)",
				"Bash(git commit:*)",
				"Bash(ssh-add:*)",
				# Python operations — running scripts and pip management
				"Bash(python3:*)",
				"Bash(python:*)",
				"Bash(pip install:*)",
				"Bash(pip show:*)",
				"Bash(source:*)",
				# Utility commands used in development
				"Bash(curl:*)",
				"Bash(grep:*)",
				"Bash(pgrep:*)",
				"Bash(ls:*)",
				# Ruff linting — triggered by the post-edit hook
				"Bash(ruff check:*)",
				"Bash(ruff format:*)",
				# Allow fetching from GitHub raw content (common for scripts/configs)
				"WebFetch(domain:raw.githubusercontent.com)",
			]
		},
		"hooks": {
			"PostToolUse": [
				{
					# Trigger after any file write or edit operation
					"matcher": "Write|Edit|MultiEdit",
					"hooks": [
						{
							"type": "command",
							# Dynamic path — set to this project's actual location
							"command": hook_path,
							"statusMessage": "🔍 Ruff checking for lint...",
						}
					],
				}
			]
		},
	}

	if settings_path.exists():
		warning("settings.local.json already exists - overwriting with fresh config.")

	settings_path.write_text(json.dumps(settings, indent=2))
	success(f"Written: {settings_path}")
	info(f"Hook path set to: {C.YELLOW}{hook_path}{C.RESET}")


def write_post_edit_hook(project_path: Path):
	"""
	Write the post_edit.sh Claude Code hook into .claude/hooks/.
	This script runs automatically after Claude edits any Python file,
	formatting with ruff and surfacing any lint errors immediately.
	The venv ruff path is set dynamically based on project_path.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	step("🪝", "Post-Edit Hook (post_edit.sh)")

	hook_path = project_path / ".claude" / "hooks" / "post_edit.sh"
	ruff_bin = str(project_path / ".venv" / "bin" / "ruff")

	hook_content = f"""#!/bin/bash
# =============================================================================
# .claude/hooks/post_edit.sh — Claude Code post-edit hook
# =============================================================================
# Runs automatically after Claude edits a file. Formats and lints any Python
# file using Ruff so issues are caught during the session, not at commit time.
#
# Exit codes:
#   0 — success or non-Python file (no action needed)
#   1 — Ruff not found (venv issue)
#   2 — lint errors found (Claude will see the output and fix them)
# =============================================================================

# Read JSON input from stdin and extract the edited file path
file_path=$(cat | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {{}}).get('file_path', ''))
")

# Nothing to do if no file path was provided
if [ -z "$file_path" ]; then
  exit 0
fi

# Only act on Python files — skip everything else silently
if ! echo "$file_path" | grep -qE '\\.py$'; then
  exit 0
fi

RUFF="{ruff_bin}"

# Bail clearly if Ruff isn't where we expect it — likely a venv setup issue
if [ ! -x "$RUFF" ]; then
  echo "⚠ Ruff not found at $RUFF - is the venv set up?" >&2
  exit 1
fi

cd "$CLAUDE_PROJECT_DIR" || exit 1

# Format first (silent — formatting changes are not errors)
"$RUFF" format "$file_path" --quiet 2>/dev/null

# Lint and surface any errors to Claude so it can fix them immediately
lint_output=$("$RUFF" check "$file_path" 2>&1)
lint_exit=$?

if [ $lint_exit -ne 0 ]; then
  echo "$lint_output" >&2
  exit 2
fi

exit 0
"""

	if hook_path.exists():
		warning("post_edit.sh already exists - overwriting.")

	hook_path.write_text(hook_content)

	# Must be executable for Claude Code to run it as a hook
	hook_path.chmod(0o755)
	success(f"Written + chmod 755: {hook_path}")
	info(f"Ruff path in hook: {C.YELLOW}{ruff_bin}{C.RESET}")


def write_claude_md(project_path: Path):
	"""
	Write CLAUDE.md into the project root. This is the primary context
	file Claude Code reads at the start of every session. It references
	the docs/ documentation and sets coding standards.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	step("📝", "CLAUDE.md")

	claude_md_path = project_path / "CLAUDE.md"

	claude_md_content = """# Claude Code Project Context
This file provides essential context for Claude Code when working on this project.

## Project Documentation
The following files contain critical project information:
- @docs/prd.md - Product Requirements Document with goals, features, and technical requirements
- @docs/as-built-project-guide.md - Combined discovery and architecture guide. **Read this before implementing anything new** to find what already exists, understand architecture decisions, and follow established patterns.

## Development Environment
**Platform**: macOS
When suggesting commands, scripts, or configuration options, **ALWAYS** use macOS-compatible options. Avoid Linux-specific flags or Windows-specific commands.

### Definition of Done
Implementation is complete when:
- All acceptance criteria are met
- All tests pass - no exceptions, no skipped tests
- Minimum 80% code coverage on every file touched in the commit
- No formatter, linter, or type checker issues

### As-Built Project Guide Maintenance
**NEVER commit to git without first updating `docs/as-built-project-guide.md`** to reflect any changes:
- New systems, modules, or components added
- Systems removed or relocated
- New execution contexts or API endpoints
- New settings categories or key functions

This is a **hard requirement**. If you added, removed, or modified any server systems, components, API endpoints, or settings, the as-built project guide **MUST** be updated in the same commit.
**Before updating the as-built project guide**, read `docs/as-built-project-guide.md` for guidance on what to include and how to maintain consistency.
The as-built project guide is the primary discovery document for finding existing functionality. Keeping it current prevents duplicate implementations and helps integrate with existing patterns.

## Coding Guidelines
### Code Style
- **ALWAYS** use tabs for indentation, not spaces. Ruff is configured to enforce this.
- Focus above all on code readability. Code is read much more than written.
- **NEVER** use leet code or clever code solutions. Clean readable code is the goal.
- **NEVER** comment on what code is doing, instead comment why. If you have to comment what that indicates poor readability.
- **ALWAYS** minimize function/file length and nesting as much as possible.
- **ALWAYS** use descriptive names. There is no advantage to using "i" over "index".
- **ALWAYS** include units in names such as "timeoutSeconds" or "distanceMeters". This avoids unit confusion.
- **NEVER** use magic numbers.
- **ALWAYS** use documentation comments on functions and classes.
- **ALWAYS** keep comments current.
- **NEVER** change "AI NOTE:" comments. These comments are explicitly intended to guide AI agents where they often make mistakes.
- **ALWAYS** use early returns to minimize nesting.

### Assertions
- **ALWAYS** validate function inputs to ensure they meet requirements
- **ALWAYS** validate function outputs when processing could fail to produce correct output
- **ALWAYS** use descriptive assertion messages that explain what was expected

### Error Handling
- **ALWAYS** catch and handle recoverable errors at the appropriate level
- **NEVER** catch errors only to re-throw them to the next level
- Internal functions and classes should throw unrecoverable errors and let them bubble up
- UI components should catch all errors and display them to the user

## Time Handling
### Storage and Internal Processing
- **Use UTC for most internal storage** - Timestamps in the database, logs, and internal APIs should use UTC
- **Use floating time for location-independent events** - Some times have no timezone (e.g., "8:00 AM" means "8:00 AM wherever the user is at that moment"). These should be stored without timezone information.

### LLM Communication
- **ALWAYS normalize times to the user's timezone when presenting to the LLM**
- LLMs do not handle timezone conversions reliably. All times in system prompts, tool outputs, and context should be in the user's local timezone.
- Include the timezone explicitly when relevant (e.g., "3:00 PM PST" not just "3:00 PM")
"""

	if claude_md_path.exists():
		warning("CLAUDE.md already exists - overwriting.")

	claude_md_path.write_text(claude_md_content)
	success(f"Written: {claude_md_path}")


def write_agent_docs(project_path: Path):
	"""
	Create the docs/ documentation files that CLAUDE.md references.
	Writes two files:
	  - prd.md                    product requirements document
	  - as-built-project-guide.md combined discovery + architecture doc

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	step("📋", "Agent Documentation (docs/)")

	docs_path = project_path / "docs"

	# ── prd.md ────────────────────────────────────────────────────────────────
	prd_path = docs_path / "prd.md"
	if not prd_path.exists():
		prd_path.write_text(
			"# Product Requirements Document\n\n"
			"## What We Are Building\n\n"
			"> Describe what this project does in one sentence.\n\n"
			"## Problem We Are Solving\n\n"
			"- [ ] What pain point does this eliminate?\n"
			"- [ ] Who experiences this pain?\n"
			"- [ ] What does success look like for the user?\n\n"
			"## Goals\n\n"
			"- [ ] Define primary goals here\n\n"
			"## Features\n\n"
			"- [ ] List key features here\n\n"
			"## Technical Requirements\n\n"
			"- [ ] List technical requirements here\n\n"
			"## Out of Scope\n\n"
			"- [ ] List what is explicitly not included here\n\n"
			"## Definition of Done\n\n"
			"- All acceptance criteria met\n"
			"- All tests pass with minimum 80% coverage\n"
			"- No linter, formatter, or type checker issues\n"
			"- docs/as-built-project-guide.md updated to reflect changes\n"
		)
		success(f"Written: {prd_path}")
	else:
		warning(f"Already exists - skipping: {prd_path}")

	# ── as-built-project-guide.md ─────────────────────────────────────────────
	# Combines what were previously three separate files:
	#   project-guide.md + as-built.md + project-guide-instructions.md
	abpg_path = docs_path / "as-built-project-guide.md"
	if not abpg_path.exists():
		abpg_path.write_text(
			"# As-Built Project Guide\n\n"
			"> This document serves two purposes:\n"
			"> 1. **Discovery** - find what exists before building something new\n"
			"> 2. **Architecture** - document how systems are built and why\n"
			">\n"
			"> Update this file with every commit. Keep it minimal and scannable.\n\n"
			"---\n\n"
			"## How to Maintain This Document\n\n"
			"Before committing, ask: did I add, remove, or move any systems, "
			"components, or endpoints?\n"
			"If yes - update the relevant section below before committing.\n\n"
			"Include:\n"
			"- Folder-level structure (not individual files)\n"
			"- Major systems with their entry points and key functions\n"
			"- API endpoints with input shape and purpose\n"
			"- Architecture decisions and why they were made\n\n"
			"Do NOT include:\n"
			"- Individual file listings (LSP handles this)\n"
			"- Implementation details (read the code)\n"
			"- Generic framework conventions (project-specific only)\n\n"
			"---\n\n"
			"## Directory Structure\n\n"
			"_Document your folder layout here._\n\n"
			"## Systems\n\n"
			"_Document major modules, their entry points, and key functions here._\n\n"
			"## API Endpoints\n\n"
			"_Document endpoints here as they are added._\n\n"
			"## Architecture Decisions\n\n"
			"_Document significant technical decisions and the reasoning behind them._\n\n"
			"## Validation and Error Handling Standards\n\n"
			"_Document how this project handles errors and validates inputs._\n"
		)
		success(f"Written: {abpg_path}")
	else:
		warning(f"Already exists - skipping: {abpg_path}")


# =============================================================================
# STEP 10 — GIT PRE-COMMIT HOOK FOR SECRET SCANNING
# Installs a pre-commit hook that runs detect-secrets before every commit
# so secrets never accidentally make it into the git history.
# =============================================================================


def write_precommit_hook(project_path: Path, detect_secrets_bin: str):
	"""
	Write a git pre-commit hook that runs detect-secrets before every commit.
	The hook blocks the commit and shows a warning if new secrets are detected.

	Args:
	    project_path: The resolved Path to the project root directory.
	    detect_secrets_bin: Path to the detect-secrets executable.
	"""
	step("🔐", "Git Pre-Commit Secret Scanning Hook")

	hooks_dir = project_path / ".git" / "hooks"
	precommit_path = hooks_dir / "pre-commit"

	if not hooks_dir.exists():
		# Should not happen if git init ran, but guard just in case
		fatal(f".git/hooks directory not found at {hooks_dir} - was git init run?")

	precommit_content = """#!/bin/bash
# =============================================================================
# .git/hooks/pre-commit — Secret scanning hook
# =============================================================================
# Runs detect-secrets before every git commit to prevent secrets (API keys,
# passwords, tokens) from being accidentally committed to the repository.
#
# To update the baseline after intentionally adding a known value:
#   detect-secrets scan > .secrets.baseline
#
# Exit codes:
#   0 — no new secrets detected, commit proceeds
#   1 — new secrets detected, commit is blocked
# =============================================================================

DETECT_SECRETS="__DETECT_SECRETS_BIN__"
BASELINE=".secrets.baseline"

# Warn but allow commit if detect-secrets isn't installed
if [ ! -x "$DETECT_SECRETS" ]; then
  echo "⚠  detect-secrets not found at $DETECT_SECRETS" >&2
  echo "⚠  Secret scanning skipped - install detect-secrets to enable." >&2
  exit 0
fi

# Warn but allow commit if no baseline exists yet
if [ ! -f "$BASELINE" ]; then
  echo "⚠  No .secrets.baseline found." >&2
  echo "⚠  Run: detect-secrets scan > .secrets.baseline" >&2
  echo "⚠  Secret scanning skipped for this commit." >&2
  exit 0
fi

echo "🔐 Scanning for secrets..."

# Scan to a temp file and compare results to the baseline.
# We never write back to the baseline from the hook - that would cause
# an infinite loop: commit -> scan -> baseline changes -> needs commit.
# To update the baseline intentionally: detect-secrets scan > .secrets.baseline
TMPFILE=$(mktemp)
"$DETECT_SECRETS" scan > "$TMPFILE"
scan_exit=$?

if [ $scan_exit -ne 0 ]; then
  echo "\u26a0  detect-secrets scan failed - skipping check." >&2
  rm -f "$TMPFILE"
  exit 0
fi

# Compare only the results section - ignore version/plugin metadata changes
BASELINE_RESULTS=$(python3 -c \
  "import json,sys; print(json.dumps(json.load(open(sys.argv[1])).get('results',{}), sort_keys=True))" \
  "$BASELINE")
SCAN_RESULTS=$(python3 -c \
  "import json,sys; print(json.dumps(json.load(open(sys.argv[1])).get('results',{}), sort_keys=True))" \
  "$TMPFILE")
rm -f "$TMPFILE"

if [ "$BASELINE_RESULTS" != "$SCAN_RESULTS" ]; then
  echo "" >&2
  echo "\U0001f6a8 New secrets detected! Commit blocked." >&2
  echo "   Review with: detect-secrets audit .secrets.baseline" >&2
  echo "   To update baseline after confirming false positives:" >&2
  echo "   detect-secrets scan > .secrets.baseline && git add .secrets.baseline" >&2
  exit 1
fi

echo "\u2714  No new secrets detected."
exit 0
"""

	if precommit_path.exists():
		warning("pre-commit hook already exists - overwriting.")

	precommit_content = precommit_content.replace("__DETECT_SECRETS_BIN__", detect_secrets_bin)
	precommit_path.write_text(precommit_content)
	precommit_path.chmod(0o755)
	success(f"Written + chmod 755: {precommit_path}")


# =============================================================================
# STEP 11 — FINAL SUMMARY
# Print a clear summary of everything that was set up so the developer
# knows exactly what they have and what to do next.
# =============================================================================


def print_summary(project_path: Path):
	"""
	Print a final colorful summary of everything the script set up,
	plus next steps for the developer.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	venv_ruff = project_path / ".venv" / "bin" / "ruff"
	venv_python = project_path / ".venv" / "bin" / "python3"

	print(f"""
{C.GREEN}{C.BOLD}╔══════════════════════════════════════════════════════════╗
║              ✅  Project Bootstrap Complete!              ║
╚══════════════════════════════════════════════════════════╝{C.RESET}

{C.BOLD}Project location:{C.RESET}  {C.YELLOW}{project_path}{C.RESET}

{C.BOLD}What was set up:{C.RESET}
  {C.GREEN}✔{C.RESET}  Homebrew (package manager)
  {C.GREEN}✔{C.RESET}  Git + repository initialized
  {C.GREEN}✔{C.RESET}  Python 3 + virtual environment (.venv/)
  {C.GREEN}✔{C.RESET}  Base packages: pandas, requests, python-dotenv, pydantic, pypdf, ruff
  {C.GREEN}✔{C.RESET}  pyproject.toml ([project] + ruff + pytest config)
  {C.GREEN}✔{C.RESET}  .gitignore (venv, cache, secrets, editor files)
  {C.GREEN}✔{C.RESET}  tests/ directory (conftest.py + placeholder test)
  {C.GREEN}✔{C.RESET}  detect-secrets + .secrets.baseline
  {C.GREEN}✔{C.RESET}  Claude Code (global npm install)
  {C.GREEN}✔{C.RESET}  .claude/settings.local.json (permissions + hook)
  {C.GREEN}✔{C.RESET}  .claude/hooks/post_edit.sh (auto lint on file edit)
  {C.GREEN}✔{C.RESET}  CLAUDE.md (Claude Code project context)
  {C.GREEN}✔{C.RESET}  docs/ (prd.md, as-built-project-guide.md)
  {C.GREEN}✔{C.RESET}  .git/hooks/pre-commit (secret scanning before commit)

{C.BOLD}Next steps:{C.RESET}
  1. {C.CYAN}cd {project_path}{C.RESET}
  2. {C.CYAN}source .venv/bin/activate{C.RESET}   ← activate your virtual environment
  3. {C.CYAN}claude{C.RESET}                       ← start a Claude Code session
  4. Fill in {C.YELLOW}docs/prd.md{C.RESET} with your project goals
  5. Fill in {C.YELLOW}docs/as-built-project-guide.md{C.RESET} as you build

{C.BOLD}Useful paths:{C.RESET}
  Python:  {C.YELLOW}{venv_python}{C.RESET}
  Ruff:    {C.YELLOW}{venv_ruff}{C.RESET}

{C.MAGENTA}{C.BOLD}The spell is cast. Happy building! 🔮{C.RESET}
""")


# =============================================================================
# PROJECT NAME + PRD PROMPT
# Ask the user for their project name (used in pyproject.toml) and a brief
# description of what they are building (written into prd.md as a starting
# point so Claude Code has real context from day one).
# =============================================================================


def get_project_name(project_path: Path) -> str:
	"""
	Prompt the user for their project name. Defaults to the directory name
	so they can just hit Enter for the most common case.

	Args:
	    project_path: Used to suggest the directory name as a default.

	Returns:
	    The project name string to embed in pyproject.toml.
	"""
	step("🏷️", "Project Name")

	# Suggest the directory name as the default — usually correct
	default_name = project_path.name.lower().replace(" ", "_").replace("-", "_")
	info(f"Default project name: {C.YELLOW}{default_name}{C.RESET} (from directory name)")

	raw = input(f"  {C.BOLD}{C.MAGENTA}➜ Project name [{default_name}]: {C.RESET}").strip()

	# Empty input means accept the default
	project_name = raw if raw else default_name
	success(f"Project name set to: {C.GREEN}{project_name}{C.RESET}")
	return project_name


def prompt_prd(project_path: Path, project_name: str):
	"""
	Ask the user for a short description of what they are building and
	write it into docs/prd.md as a starting point. Claude Code reads
	this file at the start of every session, so even a rough description
	dramatically improves the quality of AI assistance.

	Args:
	    project_path:  The resolved Path to the project root directory.
	    project_name:  Inserted as the PRD heading.
	"""
	step("📄", "Product Requirements Document (docs/prd.md)")

	print(f"""
  {C.WHITE}What are you building?{C.RESET}
  {C.BLUE}A sentence or two is enough - Claude Code will read this at the start{C.RESET}
  {C.BLUE}of every session to understand the project's purpose and direction.{C.RESET}
  {C.BLUE}You can expand it later. Press Enter to leave it as a placeholder.{C.RESET}
""")

	description = input(f"  {C.BOLD}{C.MAGENTA}➜ Project description: {C.RESET}").strip()

	prd_path = project_path / "docs" / "prd.md"

	if description:
		# Write a real PRD seed with the user's description
		prd_content = f"""# Product Requirements Document - {project_name}

## What We Are Building

{description}

## Problem We Are Solving

- [ ] What pain point does this eliminate?
- [ ] Who experiences this pain?
- [ ] What does success look like for the user?

## Goals

- [ ] Define primary goals here

## Features

- [ ] List key features here

## Technical Requirements

- [ ] List technical requirements here

## Out of Scope

- [ ] List what is explicitly not included here

## Definition of Done

- All acceptance criteria met
- All tests pass with minimum 80% coverage
- No linter, formatter, or type checker issues
- docs/as-built-project-guide.md updated to reflect changes
"""
		prd_path.write_text(prd_content)
		success(f"prd.md written with your description: {prd_path}")
		info("Expand this file as the project takes shape.")
	else:
		# Leave the placeholder that write_agent_docs already created
		warning("No description provided - prd.md left as placeholder.")
		info(f"Fill it in later at: {C.YELLOW}{prd_path}{C.RESET}")


# =============================================================================
# GITIGNORE
# A .gitignore tailored for Python + Claude Code projects. Prevents venv,
# caches, secrets, and editor files from being committed accidentally.
# =============================================================================

# Standard ignores for Python + Claude Code + macOS development
GITIGNORE_CONTENT = """
# Python virtual environment — never commit this
.venv/
venv/
env/

# Compiled Python files
__pycache__/
*.py[cod]
*.pyo

# Environment variables — may contain secrets
.env
.env.*
!.env.example

# Secrets baseline is committed so it can be diffed, but not the audit log
.secrets.audit

# Test artifacts and coverage reports
.pytest_cache/
.coverage
htmlcov/
coverage.xml

# Distribution / packaging
dist/
build/
*.egg-info/

# macOS system files
.DS_Store
.AppleDouble

# Editor and IDE files
.idea/
.vscode/
*.swp
*.swo

# Logs
*.log
logs/
""".strip()


def write_gitignore(project_path: Path):
	"""
	Write a .gitignore into the project root tailored for Python +
	Claude Code projects. Skips if one already exists.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	step("🙈", ".gitignore")

	gitignore_path = project_path / ".gitignore"

	if gitignore_path.exists():
		warning(".gitignore already exists - skipping.")
		return

	gitignore_path.write_text(GITIGNORE_CONTENT + "\n")
	success(f"Written: {gitignore_path}")
	info("Ignoring: .venv/, __pycache__/, .env, .DS_Store, test artifacts, editor files")


def verify_gitignore(project_path: Path):
	"""
	Confirm .gitignore exists and contains the minimum required entries
	for a safe Python + Claude Code project.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	gitignore_path = project_path / ".gitignore"

	if not gitignore_path.exists():
		fatal(f".gitignore verification failed - file not found: {gitignore_path}")

	content = gitignore_path.read_text()

	# These are the entries we absolutely must have to avoid committing secrets/venv
	required_entries = [".venv/", "__pycache__/", ".env"]
	missing = [entry for entry in required_entries if entry not in content]

	if missing:
		fatal(
			".gitignore verification failed - missing critical entries:\n"
			+ "\n".join(f"  - {e}" for e in missing)
		)

	success(f"✔ Verified .gitignore ({len(content.splitlines())} lines, required entries present)")


# =============================================================================
# TESTS DIRECTORY
# Create a tests/ directory with a conftest.py and a placeholder test file
# so pytest can discover tests immediately without extra configuration.
# =============================================================================


def create_tests_directory(project_path: Path):
	"""
	Create the tests/ directory with:
	  - __init__.py      so Python treats it as a package
	  - conftest.py      pytest configuration and shared fixtures
	  - test_placeholder.py  a passing placeholder so pytest runs green immediately

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	step("🧪", "Tests Directory")

	tests_path = project_path / "tests"

	if tests_path.exists():
		warning("tests/ directory already exists - skipping.")
		return

	tests_path.mkdir()
	success(f"Created: {tests_path}")

	# __init__.py — makes tests/ a proper Python package
	(tests_path / "__init__.py").write_text(
		"# Tests package - pytest discovers tests in this directory\n"
	)
	success("Written: tests/__init__.py")

	# conftest.py — shared fixtures live here; empty for now but ready to use
	conftest_content = (
		"# conftest.py - shared pytest fixtures\n"
		"#\n"
		"# Define fixtures here that should be available to all tests.\n"
		"# pytest automatically discovers and loads this file.\n"
		"#\n"
		"# Example fixture:\n"
		"#   @pytest.fixture\n"
		"#   def sample_data():\n"
		'#       return {"key": "value"}\n'
	)
	(tests_path / "conftest.py").write_text(conftest_content)
	success("Written: tests/conftest.py")

	# Placeholder test - gives pytest something to run so the suite starts green
	placeholder_content = (
		"# test_placeholder.py\n"
		"#\n"
		"# This file exists so pytest starts green from day one.\n"
		"# Replace it with real tests as you build the project.\n"
		"\n"
		"\n"
		"def test_project_is_set_up():\n"
		'    """Placeholder - proves pytest is configured and running correctly."""\n'
		"    # Replace this with real assertions as the project grows\n"
		'    assert True, "If this fails something is very wrong with pytest itself"\n'
	)
	(tests_path / "test_placeholder.py").write_text(placeholder_content)
	success("Written: tests/test_placeholder.py")


def verify_tests_directory(project_path: Path):
	"""
	Confirm the tests/ directory and its required files were created correctly.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	tests_path = project_path / "tests"

	if not tests_path.exists() or not tests_path.is_dir():
		fatal(f"Tests directory verification failed - {tests_path} not found.")

	required_files = ["__init__.py", "conftest.py", "test_placeholder.py"]
	for filename in required_files:
		file_path = tests_path / filename
		if not file_path.exists():
			fatal(f"Tests directory verification failed - missing: {file_path}")
		success(f"✔ Verified test file: tests/{filename}")


# =============================================================================
# STEP - FRONTEND LINTING AND FORMATTING (OPTIONAL)
# ESLint and Prettier are the standard frontend tooling pair for JS/TS projects.
#
#   ESLint   = linter    - catches bugs, bad patterns, and code quality issues
#   Prettier = formatter - enforces consistent visual style (spacing, quotes etc.)
#
# Both fall under the broad concept of "linting" but do different jobs.
# Together they cover everything Ruff does for Python, but for frontend files.
# This step is optional - pure Python projects do not need them.
# =============================================================================


def install_bandit(pip_bin: str, project_path: Path):
	"""
	Install bandit into the project venv via pip.
	Bandit scans Python source for common security vulnerabilities -
	hardcoded passwords, unsafe eval(), SQL injection patterns, weak crypto.

	Args:
	    pip_bin:      Path to the venv pip executable.
	    project_path: The resolved Path to the project root directory.
	"""
	step("🔐", "Bandit (Security Scanner)")
	info("Installing bandit into venv via pip...")
	run([pip_bin, "install", "bandit"])

	# Write a pyproject.toml bandit config section - skips test files
	# since test code intentionally uses patterns bandit would flag
	info("Adding bandit configuration to pyproject.toml...")
	pyproject_path = project_path / "pyproject.toml"
	bandit_config = (
		"\n\n[tool.bandit]\n"
		"# Skip test files - they intentionally use patterns bandit flags\n"
		'exclude_dirs = ["tests", ".venv"]\n'
		"# Only report medium severity and above - low is too noisy for most projects\n"
		'skips = ["B101"]  # B101 = assert used - fine in non-production code\n'
	)
	if pyproject_path.exists():
		with pyproject_path.open("a") as f:
			f.write(bandit_config)
		success(f"Bandit config appended to {pyproject_path}")

	verify_bandit(pip_bin)


def verify_bandit(pip_bin: str):
	"""
	Confirm bandit is installed in the venv and runnable.
	Only called if the user opted in during the installation menu.

	Args:
	    pip_bin: Path to the venv pip, used to locate the bandit binary.
	"""
	bandit_bin = str(Path(pip_bin).parent / "bandit")
	if not Path(bandit_bin).exists():
		fatal(f"Bandit verification failed - binary not found at {bandit_bin}")

	result = run([bandit_bin, "--version"], capture=True, check=False)
	if result.returncode != 0:
		fatal("Bandit verification failed - '--version' returned an error.")

	success(f"✔ Verified Bandit: {result.stdout.strip().splitlines()[0]}")


def verify_eslint():
	"""
	Confirm ESLint is installed and runnable.
	Only called if the user opted in during the frontend tooling prompt.
	"""
	if not shutil.which("eslint"):
		fatal("ESLint verification failed - 'eslint' not found on PATH after install.")

	result = run(["eslint", "--version"], capture=True, check=False)
	if result.returncode != 0:
		fatal("ESLint verification failed - 'eslint --version' returned an error.")

	success(f"✔ Verified ESLint: {result.stdout.strip()}")


def verify_prettier():
	"""
	Confirm Prettier is installed and runnable.
	Only called if the user opted in during the frontend tooling prompt.
	"""
	if not shutil.which("prettier"):
		fatal("Prettier verification failed - 'prettier' not found on PATH after install.")

	result = run(["prettier", "--version"], capture=True, check=False)
	if result.returncode != 0:
		fatal("Prettier verification failed - 'prettier --version' returned an error.")

	success(f"✔ Verified Prettier: v{result.stdout.strip()}")


# =============================================================================
# VERIFICATION FUNCTIONS
# Each verify_* function runs immediately after its corresponding install/write
# step. If anything is wrong we call fatal() and stop — better to fail loudly
# now than silently build on a broken foundation.
# =============================================================================


def verify_homebrew():
	"""
	Report Homebrew status. Not fatal if missing - tools have fallbacks.
	"""
	if brew_available():
		result = run(["brew", "--version"], capture=True, check=False)
		success(f"✔ Homebrew available: {result.stdout.strip().splitlines()[0]}")
	else:
		warning("Homebrew not available - fallback install methods will be used.")


def verify_git():
	"""
	Confirm git is on PATH and functional.
	Without git we cannot init repos or install pre-commit hooks.
	"""
	if not shutil.which("git"):
		fatal("Git verification failed - 'git' not found on PATH after install.")
	result = run(["git", "--version"], capture=True, check=False)
	if result.returncode != 0:
		fatal("Git verification failed - 'git --version' returned an error.")
	success(f"✔ Verified Git: {result.stdout.strip()}")


def verify_git_repo(project_path: Path):
	"""
	Confirm a .git directory exists inside the project, proving git init ran.
	Also checks that HEAD exists - a sign of a properly initialized repo.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	git_dir = project_path / ".git"
	head_file = git_dir / "HEAD"

	if not git_dir.exists():
		fatal(f"Git repo verification failed - no .git directory found in {project_path}")
	if not head_file.exists():
		fatal(f"Git repo verification failed - .git/HEAD missing in {project_path}")

	success(f"✔ Verified git repo: {git_dir}")


def verify_python():
	"""
	Confirm python3 is on PATH and returns a valid version string.
	We need python3 to create the venv and run project code.
	"""
	if not shutil.which("python3"):
		fatal("Python verification failed - 'python3' not found on PATH after install.")
	result = run(["python3", "--version"], capture=True, check=False)
	if result.returncode != 0:
		fatal("Python verification failed - 'python3 --version' returned an error.")
	success(f"✔ Verified Python: {result.stdout.strip()}")


def verify_venv(project_path: Path):
	"""
	Confirm the virtual environment was created correctly by checking
	that both the python3 and pip executables exist and are runnable.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	venv_python = project_path / ".venv" / "bin" / "python3"
	venv_pip = project_path / ".venv" / "bin" / "pip"

	for binary in [venv_python, venv_pip]:
		if not binary.exists():
			fatal(f"Venv verification failed - {binary} does not exist.")
		if not os.access(binary, os.X_OK):
			fatal(f"Venv verification failed - {binary} is not executable.")

	# Run a trivial python expression inside the venv to confirm it works
	result = run(
		[str(venv_python), "-c", "import sys; print(sys.version)"], capture=True, check=False
	)
	if result.returncode != 0:
		fatal("Venv verification failed - venv python3 could not execute a test expression.")

	success(f"✔ Verified venv: {project_path / '.venv'}")
	info(f"  Venv Python: {result.stdout.strip().splitlines()[0]}")


def verify_packages(project_path: Path):
	"""
	Confirm every base package can actually be imported from inside the venv.
	A successful pip install doesn't always mean imports work - this catches
	broken wheels, missing C extensions, and other silent failures.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	venv_python = str(project_path / ".venv" / "bin" / "python3")

	# Map pip package names to their importable module names —
	# these don't always match (e.g. python-dotenv → dotenv)
	# Maps pip package name to its importable Python module name.
	# CLI-only tools (ruff, pytest) are verified via binary check instead.
	import_names = {
		"pandas": "pandas",
		"requests": "requests",
		"python-dotenv": "dotenv",  # pip name != import name
		"pydantic": "pydantic",
		"pypdf": "pypdf",
		"rich": "rich",
		"loguru": "loguru",
	}

	# Only verify watchdog if user opted to install it
	if "watchdog" in BASE_PACKAGES:
		import_names["watchdog"] = "watchdog"

	# CLI tools that cannot be imported - verify via binary existence instead
	cli_tools = {
		"ruff": str(project_path / ".venv" / "bin" / "ruff"),
		"pytest": str(project_path / ".venv" / "bin" / "pytest"),
		"pytest-cov": str(project_path / ".venv" / "bin" / "pytest"),
	}
	for tool, binary in cli_tools.items():
		if Path(binary).exists():
			success(f"✔ Verified CLI tool: {tool}")
		else:
			error(f"✘ CLI tool not found: {tool} at {binary}")
			pass  # non-fatal, pip may have installed it elsewhere

	all_passed = True
	for package, module in import_names.items():
		result = run([venv_python, "-c", f"import {module}"], capture=True, check=False)
		if result.returncode != 0:
			error(f"✘ Package import failed: {package} (tried: import {module})")
			all_passed = False
		else:
			success(f"✔ Verified import: {module}")

	if not all_passed:
		fatal("One or more base packages failed to import. Check pip install output above.")


def verify_detect_secrets(detect_secrets_bin: str):
	"""
	Confirm detect-secrets is installed and runnable.

	Args:
	    detect_secrets_bin: Path to the detect-secrets executable.
	"""
	if not Path(detect_secrets_bin).exists():
		fatal(f"detect-secrets verification failed - binary not found: {detect_secrets_bin}")
	if not os.access(detect_secrets_bin, os.X_OK):
		fatal(f"detect-secrets verification failed - binary not executable: {detect_secrets_bin}")

	result = run([detect_secrets_bin, "--version"], capture=True, check=False)
	if result.returncode != 0:
		fatal("detect-secrets verification failed - '--version' returned an error.")

	success(f"✔ Verified detect-secrets: {result.stdout.strip()}")


def verify_secrets_baseline(project_path: Path):
	"""
	Confirm the .secrets.baseline file exists and contains valid JSON.
	An invalid baseline will cause the pre-commit hook to error on every commit.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	baseline_path = project_path / ".secrets.baseline"

	if not baseline_path.exists():
		fatal(f"Secrets baseline verification failed - {baseline_path} does not exist.")

	# Try parsing it as JSON — detect-secrets requires valid JSON
	try:
		parsed = json.loads(baseline_path.read_text())
	except json.JSONDecodeError as parse_error:
		fatal(f"Secrets baseline verification failed - invalid JSON: {parse_error}")

	# The baseline should always have a 'version' and 'results' key
	for required_key in ["version", "results"]:
		if required_key not in parsed:
			fatal(f"Secrets baseline verification failed - missing key: '{required_key}'")

	success(f"✔ Verified .secrets.baseline (valid JSON, version: {parsed.get('version', '?')})")


def verify_ruff_config(project_path: Path):
	"""
	Confirm pyproject.toml exists and contains the [tool.ruff] section.
	Also runs 'ruff check' on the project to make sure ruff can read the config.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	pyproject_path = project_path / "pyproject.toml"

	if not pyproject_path.exists():
		fatal(f"Ruff config verification failed - pyproject.toml not found at {pyproject_path}")

	content = pyproject_path.read_text()
	if "[tool.ruff]" not in content:
		fatal("Ruff config verification failed - [tool.ruff] section missing from pyproject.toml")

	# Run ruff against the project dir to confirm it can read the config without errors
	ruff_bin = project_path / ".venv" / "bin" / "ruff"
	result = run(
		[str(ruff_bin), "check", str(project_path), "--select", "E"], capture=True, check=False
	)

	# Exit code 1 means lint errors found (fine — no source files yet)
	# Exit code 2+ means ruff itself errored (config problem)
	if result.returncode >= 2:
		error(f"Ruff config verification failed - ruff exited with code {result.returncode}")
		if result.stderr:
			print(f"    {C.RED}{result.stderr.strip()}{C.RESET}")
		fatal("Ruff could not read its configuration. Check pyproject.toml.")

	success(f"✔ Verified ruff config: {pyproject_path}")


def verify_claude_code():
	"""
	Confirm Claude Code is installed and on PATH by running 'claude --version'.
	"""
	if not shutil.which("claude"):
		fatal("Claude Code verification failed - 'claude' not found on PATH after install.")

	result = run(["claude", "--version"], capture=True, check=False)
	if result.returncode != 0:
		fatal("Claude Code verification failed - 'claude --version' returned an error.")

	success(f"✔ Verified Claude Code: {result.stdout.strip()}")


def verify_directory_structure(project_path: Path):
	"""
	Confirm the expected .claude/ and docs/ directory trees exist.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	required_dirs = [
		project_path / ".claude" / "hooks",
		project_path / "docs",
	]

	for directory in required_dirs:
		if not directory.exists():
			fatal(f"Directory structure verification failed - missing: {directory}")
		if not directory.is_dir():
			fatal(f"Directory structure verification failed - not a directory: {directory}")
		success(f"✔ Verified directory: {directory}")


def verify_settings_local(project_path: Path):
	"""
	Confirm settings.local.json exists, is valid JSON, and contains
	the required 'permissions' and 'hooks' top-level keys.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	settings_path = project_path / ".claude" / "settings.local.json"

	if not settings_path.exists():
		fatal(f"settings.local.json verification failed - file not found: {settings_path}")

	try:
		parsed = json.loads(settings_path.read_text())
	except json.JSONDecodeError as parse_error:
		fatal(f"settings.local.json verification failed - invalid JSON: {parse_error}")

	for required_key in ["permissions", "hooks"]:
		if required_key not in parsed:
			fatal(f"settings.local.json verification failed - missing key: '{required_key}'")

	# Confirm the hook command path actually points to our post_edit.sh
	hook_path = project_path / ".claude" / "hooks" / "post_edit.sh"
	hooks = parsed.get("hooks", {}).get("PostToolUse", [])
	hook_commands = [h.get("command", "") for entry in hooks for h in entry.get("hooks", [])]

	if not any(str(hook_path) in cmd for cmd in hook_commands):
		fatal(
			f"settings.local.json verification failed - hook command doesn't reference {hook_path}"
		)

	success("✔ Verified settings.local.json (valid JSON, hooks + permissions present)")


def verify_post_edit_hook(project_path: Path):
	"""
	Confirm post_edit.sh exists, is executable, and references the correct
	ruff binary path for this project's venv.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	hook_path = project_path / ".claude" / "hooks" / "post_edit.sh"
	ruff_bin = project_path / ".venv" / "bin" / "ruff"

	if not hook_path.exists():
		fatal(f"post_edit.sh verification failed - file not found: {hook_path}")

	if not os.access(hook_path, os.X_OK):
		fatal(f"post_edit.sh verification failed - file is not executable: {hook_path}")

	# Confirm the hook contains a reference to this project's ruff binary
	content = hook_path.read_text()
	if str(ruff_bin) not in content:
		fatal(
			f"post_edit.sh verification failed - ruff path '{ruff_bin}' "
			f"not found in hook script. The hook may point to the wrong project."
		)

	success("✔ Verified post_edit.sh (exists, executable, correct ruff path)")


def verify_claude_md(project_path: Path):
	"""
	Confirm CLAUDE.md exists and contains the key section headings that
	Claude Code depends on to understand the project context.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	claude_md_path = project_path / "CLAUDE.md"

	if not claude_md_path.exists():
		fatal(f"CLAUDE.md verification failed - file not found: {claude_md_path}")

	content = claude_md_path.read_text()

	# These headings are referenced by Claude Code during every session
	required_sections = [
		"## Project Documentation",
		"## Development Environment",
		"## Coding Guidelines",
		"### Definition of Done",
		"### As-Built Project Guide Maintenance",
	]

	missing = [section for section in required_sections if section not in content]
	if missing:
		fatal(
			"CLAUDE.md verification failed - missing sections:\n"
			+ "\n".join(f"  - {s}" for s in missing)
		)

	success(f"✔ Verified CLAUDE.md ({len(required_sections)} required sections present)")


def verify_agent_docs(project_path: Path):
	"""
	Confirm both docs/ documentation files exist and are non-empty.
	These are referenced by CLAUDE.md and must be present for Claude Code
	to find project context during sessions.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	required_files = [
		project_path / "docs" / "prd.md",
		project_path / "docs" / "as-built-project-guide.md",
	]

	for doc_path in required_files:
		if not doc_path.exists():
			fatal(f"Agent docs verification failed - missing: {doc_path}")
		if doc_path.stat().st_size == 0:
			fatal(f"Agent docs verification failed - file is empty: {doc_path}")
		success(f"✔ Verified agent doc: {doc_path.name}")


def verify_precommit_hook(project_path: Path):
	"""
	Confirm the git pre-commit hook exists, is executable, and references
	the detect-secrets binary so secret scanning will actually run.

	Args:
	    project_path: The resolved Path to the project root directory.
	"""
	hook_path = project_path / ".git" / "hooks" / "pre-commit"

	if not hook_path.exists():
		fatal(f"Pre-commit hook verification failed - file not found: {hook_path}")

	if not os.access(hook_path, os.X_OK):
		fatal(f"Pre-commit hook verification failed - file is not executable: {hook_path}")

	# Confirm detect-secrets is referenced so we know scanning will actually run
	content = hook_path.read_text()
	if "detect-secrets" not in content:
		fatal("Pre-commit hook verification failed - 'detect-secrets' not referenced in hook.")

	success("✔ Verified pre-commit hook (exists, executable, detect-secrets referenced)")


# =============================================================================
# ENTRY POINT
# =============================================================================

# =============================================================================
# INSTALLATION MENU
# Shown immediately after the banner so the user knows exactly what Spellforge
# is about to do before a single package is installed. Required tools are
# displayed but cannot be deselected. Optional tools prompt for y/n with a
# clear description of what they do and why they are useful.
# The function returns an InstallChoices object that the entry point reads
# to decide which optional steps to run.
# =============================================================================


class InstallChoices:
	"""
	Holds the user's installation choices from the upfront menu.
	Passed through the entry point so each optional step can check
	whether it should run without prompting again.
	"""

	def __init__(self):
		# Optional tools - default False until user opts in
		self.eslint = False  # Frontend linter for JS/TS files
		self.prettier = False  # Frontend formatter for JS/TS/HTML/CSS/MD
		self.watchdog = False  # Filesystem monitoring library
		self.bandit = False  # Security vulnerability scanner


# Full tool manifest - shown in the installation menu.
# Each entry: (display_name, required, category, description, why_needed)
TOOL_MANIFEST = [
	(
		"Homebrew",
		True,
		"Package Manager",
		"The macOS package manager (used if available)",
		"Used to install git and Node.js if not already present. Falls back to alternative methods if not available - safe for corporate environments.",
	),
	(
		"Git",
		True,
		"Version Control",
		"Distributed version control system",
		"Tracks all changes, enables collaboration, and anchors the pre-commit secret scanning hook.",
	),
	(
		"Python 3",
		True,
		"Runtime",
		"Python language runtime",
		"The project runs on Python. The venv and all packages require it.",
	),
	(
		"Python venv + packages",
		True,
		"Runtime",
		"Isolated environment with: pandas, requests, python-dotenv, pydantic, pypdf, ruff, pytest, pytest-cov",
		"Keeps project dependencies isolated so they never conflict with other projects on your machine.",
	),
	(
		"Ruff",
		True,
		"Python Linter/Formatter",
		"Extremely fast Python linter and formatter",
		"Enforces the coding standards in CLAUDE.md. Runs automatically after every Claude Code edit.",
	),
	(
		"detect-secrets",
		True,
		"Security",
		"Scans commits for accidentally included secrets",
		"Blocks API keys, passwords, and tokens from ever entering your git history.",
	),
	(
		"Claude Code",
		True,
		"AI Assistant",
		"Anthropic's AI-powered coding assistant CLI",
		"The core reason Spellforge exists. Configured with hooks, permissions, and project context.",
	),
	(
		"pytest + pytest-cov",
		True,
		"Testing",
		"Testing framework with coverage enforcement",
		"Required by the Definition of Done in CLAUDE.md. Enforces 80% minimum code coverage.",
	),
	(
		"ESLint",
		False,
		"Frontend Linter (Optional)",
		"Linter for JavaScript and TypeScript files",
		"Catches bugs, unsafe patterns, and code quality issues in .js .ts .jsx .tsx .vue files.",
	),
	(
		"Prettier",
		False,
		"Frontend Formatter (Optional)",
		"Formatter for JS, TS, HTML, CSS, JSON, YAML, Markdown and more",
		"Enforces consistent visual style across all non-Python files. Compliments ESLint.",
	),
	(
		"Watchdog",
		False,
		"Filesystem Monitor (Optional)",
		"Python library for watching filesystem events in real time",
		"Useful for auto-reloading scripts, triggering pipelines on file changes, or watching data drops.",
	),
	(
		"Bandit",
		False,
		"Security Scanner (Optional)",
		"Static analysis tool that scans Python code for common security vulnerabilities",
		"Catches hardcoded passwords, unsafe SQL queries, dangerous functions like eval(), and weak crypto before they reach production.",
	),
]


def show_installation_menu() -> InstallChoices:
	"""
	Display the full installation menu immediately after the banner.
	Required tools are shown with a lock icon - no choice needed.
	Optional tools prompt the user for y/n with a clear description.

	Returns:
	    InstallChoices object populated with the user's selections.
	"""
	choices = InstallChoices()

	print(f"""
{C.CYAN}{C.BOLD}  Installation Menu
  {"=" * 58}{C.RESET}
  {C.WHITE}Here is everything Spellforge will set up.{C.RESET}
  {C.BLUE}Required tools are installed automatically.{C.RESET}
  {C.BLUE}Optional tools are your choice - each is explained below.{C.RESET}
""")

	# ── Display required tools (read-only, no prompt) ─────────────────────────
	print(f"  {C.BOLD}{'─' * 58}{C.RESET}")
	print(f"  {C.BOLD}  REQUIRED  (installed automatically){C.RESET}")
	print(f"  {C.BOLD}{'─' * 58}{C.RESET}")

	for name, required, category, description, why in TOOL_MANIFEST:
		if not required:
			continue
		print(
			f"  {C.YELLOW}★{C.RESET} {C.BOLD}{name:<22}{C.RESET} {C.YELLOW}{category:<26}{C.RESET} {why}"
		)

	# ── Prompt for optional tools ─────────────────────────────────────────────
	print(f"  {C.BOLD}{'─' * 58}{C.RESET}")
	print(f"  {C.BOLD}  OPTIONAL  (your choice){C.RESET}")
	print(f"  {C.BOLD}{'─' * 58}{C.RESET}")

	for name, required, category, description, why in TOOL_MANIFEST:
		if required:
			continue

		print(f"  {C.MAGENTA}⚙{C.RESET}  {C.BOLD}{name:<22}{C.RESET} {C.YELLOW}{category}{C.RESET}")
		print(f"     {C.BLUE}{why}{C.RESET}")

		answer = (
			input(f"     {C.BOLD}{C.MAGENTA}>>> Install {name}? (y/n): {C.RESET}").strip().lower()
		)

		# Store the choice on the InstallChoices object by tool name
		if name == "ESLint":
			choices.eslint = answer == "y"
		elif name == "Prettier":
			choices.prettier = answer == "y"
		elif name == "Watchdog":
			choices.watchdog = answer == "y"
		elif name == "Bandit":
			choices.bandit = answer == "y"

		status = (
			f"{C.GREEN}yes - will install{C.RESET}"
			if answer == "y"
			else f"{C.YELLOW}no - skipping{C.RESET}"
		)
		print(f"     {status}")
		print()

	# ── Print a confirmation summary before anything runs ─────────────────────
	print()
	print(f"  {C.BOLD}{'─' * 58}{C.RESET}")
	print(f"  {C.BOLD}  Your installation plan:{C.RESET}")
	print(f"  {C.BOLD}{'─' * 58}{C.RESET}")

	for name, required, category, _, _ in TOOL_MANIFEST:
		if required:
			print(f"  {C.GREEN}✔{C.RESET}  {name} {C.BLUE}(required){C.RESET}")
		else:
			# Look up the user's choice for this optional tool
			chosen = (
				(name == "ESLint" and choices.eslint)
				or (name == "Prettier" and choices.prettier)
				or (name == "Watchdog" and choices.watchdog)
				or (name == "Bandit" and choices.bandit)
			)
			icon = f"{C.GREEN}✔{C.RESET}" if chosen else f"{C.YELLOW}✗{C.RESET}"
			status = "will install" if chosen else "skipping"
			print(f"  {icon}  {name} {C.YELLOW}({status}){C.RESET}")

	print()
	input(f"  {C.BOLD}{C.MAGENTA}>>> Press Enter to begin installation... {C.RESET}")

	return choices


if __name__ == "__main__":
	banner()

	# ── Installation menu - shown before anything runs ────────────────────────
	choices = show_installation_menu()

	# ── Project path + name ───────────────────────────────────────────────────
	project_path = get_project_path()
	info(f"Project root set to: {C.GREEN}{C.BOLD}{project_path}{C.RESET}")
	project_name = get_project_name(project_path)

	# ── Homebrew ──────────────────────────────────────────────────────────────
	ensure_homebrew()
	verify_homebrew()

	# ── Git install + repo init ───────────────────────────────────────────────
	ensure_git()
	verify_git()
	init_git_repo(project_path)
	verify_git_repo(project_path)

	# ── Python + venv + packages ──────────────────────────────────────────────
	python_bin = ensure_python()
	verify_python()
	pip_bin = create_venv(project_path, python_bin)
	verify_venv(project_path)

	# Add watchdog to install list if user opted in
	if choices.watchdog:
		info("Adding watchdog to install list (user opted in)...")
		BASE_PACKAGES.append("watchdog")

	install_base_packages(pip_bin, project_path)
	verify_packages(project_path)

	# ── detect-secrets ────────────────────────────────────────────────────────
	detect_secrets_bin = install_detect_secrets(pip_bin)
	verify_detect_secrets(detect_secrets_bin)
	init_secrets_baseline(project_path, detect_secrets_bin)
	verify_secrets_baseline(project_path)

	# ── pyproject.toml (project metadata + ruff + pytest) ────────────────────
	configure_pyproject(project_path, project_name)
	verify_ruff_config(project_path)

	# ── Claude Code ───────────────────────────────────────────────────────────
	install_claude_code()
	verify_claude_code()

	# ── ESLint (optional) ─────────────────────────────────────────────────────
	if choices.eslint:
		step("🔍", "ESLint (Frontend Linter)")
		run(["npm", "install", "-g", "eslint"])
		eslint_config_path = project_path / "eslint.config.js"
		eslint_config_path.write_text(
			"// eslint.config.js - ESLint flat config (v9+)\n"
			"export default [\n"
			"  {\n"
			"    rules: {\n"
			'      "no-unused-vars": "error",\n'
			'      "no-undef":       "error",\n'
			'      "no-console":     "warn",\n'
			'      "eqeqeq":         "error",\n'
			'      "prefer-const":   "error",\n'
			'      "no-var":         "error",\n'
			"    }\n"
			"  }\n"
			"];\n"
		)
		success(f"Written: {eslint_config_path}")
		verify_eslint()

	# ── Bandit (optional) ────────────────────────────────────────────────────
	if choices.bandit:
		install_bandit(pip_bin, project_path)

	# ── Prettier (optional) ───────────────────────────────────────────────────
	if choices.prettier:
		step("✨", "Prettier (Frontend Formatter)")
		run(["npm", "install", "-g", "prettier"])
		prettierrc_path = project_path / ".prettierrc"
		prettierrc = {
			"tabWidth": 4,
			"useTabs": True,
			"singleQuote": False,
			"printWidth": 100,
			"trailingComma": "es5",
			"bracketSpacing": True,
			"semi": True,
		}
		prettierrc_path.write_text(json.dumps(prettierrc, indent=2))
		success(f"Written: {prettierrc_path}")
		prettierignore_path = project_path / ".prettierignore"
		prettierignore_path.write_text(
			"# Prettier ignore - generated and non-source files\n"
			".venv/\nnode_modules/\n__pycache__/\ndist/\nbuild/\n"
			"*.egg-info/\ncoverage/\n.coverage\n"
		)
		success(f"Written: {prettierignore_path}")
		verify_prettier()

	# ── Directory structure + all project files ───────────────────────────────
	create_directory_structure(project_path)
	verify_directory_structure(project_path)
	write_settings_local(project_path)
	verify_settings_local(project_path)
	write_post_edit_hook(project_path)
	verify_post_edit_hook(project_path)
	write_claude_md(project_path)
	verify_claude_md(project_path)
	write_agent_docs(project_path)
	verify_agent_docs(project_path)

	# ── PRD prompt ────────────────────────────────────────────────────────────
	prompt_prd(project_path, project_name)

	# ── .gitignore ────────────────────────────────────────────────────────────
	write_gitignore(project_path)
	verify_gitignore(project_path)

	# ── tests/ directory ──────────────────────────────────────────────────────
	create_tests_directory(project_path)
	verify_tests_directory(project_path)

	# ── Git pre-commit secret scanning hook ───────────────────────────────────
	write_precommit_hook(project_path, detect_secrets_bin)
	verify_precommit_hook(project_path)

	# ── Summary ───────────────────────────────────────────────────────────────
	print_summary(project_path)
