# test_spellforge_bootstrap.py
#
# Spellforge Bootstrap Verification Suite
# =========================================
# These tests verify that Spellforge did its job correctly after a bootstrap run.
# They don't test application logic — they test that the project environment
# was set up correctly and all expected files, directories, and configs exist.
#
# Run from your project root with:
#   pytest tests/test_spellforge_bootstrap.py -v
#
# All tests should be green immediately after a Spellforge run.

import os
import stat
import tomllib
from pathlib import Path

# ── Project root — the directory Spellforge bootstrapped ─────────────────────
# All tests resolve paths relative to this. Assumes tests/ sits inside the
# project root, so we go one level up from this file's directory.
PROJECT_ROOT = Path(__file__).parent.parent


# =============================================================================
# GIT
# =============================================================================


class TestGit:
	"""Verify the git repository was initialised correctly."""

	def test_git_directory_exists(self):
		"""A .git directory must exist — proves git init ran."""
		assert (PROJECT_ROOT / ".git").is_dir(), \
			".git directory not found — did git init run?"

	def test_git_head_exists(self):
		"""HEAD file must exist inside .git — proves it is a valid repo."""
		assert (PROJECT_ROOT / ".git" / "HEAD").exists(), \
			".git/HEAD not found — git repo may be corrupt or incomplete"

	def test_precommit_hook_exists(self):
		"""pre-commit hook must exist — this is what runs detect-secrets on commit."""
		hook = PROJECT_ROOT / ".git" / "hooks" / "pre-commit"
		assert hook.exists(), \
			".git/hooks/pre-commit not found — secret scanning hook was not installed"

	def test_precommit_hook_is_executable(self):
		"""pre-commit hook must be executable — otherwise git will silently skip it."""
		hook = PROJECT_ROOT / ".git" / "hooks" / "pre-commit"
		assert hook.exists(), "pre-commit hook does not exist — cannot check permissions"
		assert os.access(hook, os.X_OK), \
			"pre-commit hook exists but is not executable — run: chmod +x .git/hooks/pre-commit"

	def test_precommit_hook_calls_detect_secrets(self):
		"""pre-commit hook content must reference detect-secrets."""
		hook = PROJECT_ROOT / ".git" / "hooks" / "pre-commit"
		assert hook.exists(), "pre-commit hook does not exist"
		content = hook.read_text()
		assert "detect-secrets" in content, \
			"pre-commit hook does not call detect-secrets — secret scanning is not active"


# =============================================================================
# VIRTUAL ENVIRONMENT
# =============================================================================


class TestVirtualEnvironment:
	"""Verify the Python virtual environment was created correctly."""

	def test_venv_directory_exists(self):
		"""The .venv directory must exist at the project root."""
		assert (PROJECT_ROOT / ".venv").is_dir(), \
			".venv directory not found — did Spellforge create the virtual environment?"

	def test_venv_python_exists(self):
		"""The venv's python3 binary must exist and be executable."""
		python = PROJECT_ROOT / ".venv" / "bin" / "python3"
		assert python.exists(), f"venv python3 not found at {python}"
		assert os.access(python, os.X_OK), f"venv python3 is not executable: {python}"

	def test_venv_pip_exists(self):
		"""The venv's pip binary must exist and be executable."""
		pip = PROJECT_ROOT / ".venv" / "bin" / "pip"
		assert pip.exists(), f"venv pip not found at {pip}"
		assert os.access(pip, os.X_OK), f"venv pip is not executable: {pip}"

	def test_venv_ruff_exists(self):
		"""Ruff must be installed inside the venv."""
		ruff = PROJECT_ROOT / ".venv" / "bin" / "ruff"
		assert ruff.exists(), \
			"ruff binary not found in venv — was it installed by Spellforge?"

	def test_venv_pytest_exists(self):
		"""pytest must be installed inside the venv."""
		pytest_bin = PROJECT_ROOT / ".venv" / "bin" / "pytest"
		assert pytest_bin.exists(), \
			"pytest binary not found in venv — was it installed by Spellforge?"


# =============================================================================
# SECRETS SCANNING
# =============================================================================


class TestSecretsScanning:
	"""Verify detect-secrets was set up correctly."""

	def test_secrets_baseline_exists(self):
		"""The .secrets.baseline file must exist — required for the pre-commit hook."""
		assert (PROJECT_ROOT / ".secrets.baseline").exists(), \
			".secrets.baseline not found — run: detect-secrets scan > .secrets.baseline"

	def test_secrets_baseline_is_valid_json(self):
		""".secrets.baseline must be valid JSON — detect-secrets will reject a corrupt file."""
		import json
		baseline = PROJECT_ROOT / ".secrets.baseline"
		assert baseline.exists(), ".secrets.baseline does not exist"
		try:
			data = json.loads(baseline.read_text())
			assert "results" in data, \
				".secrets.baseline is valid JSON but missing 'results' key — may be corrupt"
		except json.JSONDecodeError as e:
			assert False, f".secrets.baseline is not valid JSON: {e}"


# =============================================================================
# PYPROJECT.TOML
# =============================================================================


class TestPyprojectToml:
	"""Verify pyproject.toml exists and contains the expected configuration."""

	def test_pyproject_exists(self):
		"""pyproject.toml must exist at the project root."""
		assert (PROJECT_ROOT / "pyproject.toml").exists(), \
			"pyproject.toml not found — Spellforge should have created this"

	def test_pyproject_has_ruff_section(self):
		"""pyproject.toml must contain a [tool.ruff] section."""
		content = (PROJECT_ROOT / "pyproject.toml").read_text()
		assert "[tool.ruff]" in content, \
			"[tool.ruff] section missing from pyproject.toml — Ruff is not configured"

	def test_pyproject_has_pytest_section(self):
		"""pyproject.toml must contain a [tool.pytest.ini_options] section."""
		content = (PROJECT_ROOT / "pyproject.toml").read_text()
		assert "[tool.pytest.ini_options]" in content, \
			"[tool.pytest.ini_options] section missing — pytest is not configured"

	def test_pyproject_enforces_coverage_threshold(self):
		"""pyproject.toml must enforce the 80% coverage minimum."""
		content = (PROJECT_ROOT / "pyproject.toml").read_text()
		assert "cov-fail-under=80" in content, \
			"80% coverage threshold not found in pyproject.toml — quality guardrail is missing"

	def test_pyproject_is_valid_toml(self):
		"""pyproject.toml must be valid TOML — a syntax error silently breaks everything."""
		pyproject = PROJECT_ROOT / "pyproject.toml"
		assert pyproject.exists(), "pyproject.toml does not exist"
		try:
			tomllib.loads(pyproject.read_text())
		except tomllib.TOMLDecodeError as e:
			assert False, f"pyproject.toml is not valid TOML: {e}"

	def test_pyproject_has_project_section(self):
		"""pyproject.toml must have a [project] section with a name."""
		pyproject = PROJECT_ROOT / "pyproject.toml"
		data = tomllib.loads(pyproject.read_text())
		assert "project" in data, "[project] section missing from pyproject.toml"
		assert "name" in data["project"], \
			"[project] section exists but has no 'name' field"


# =============================================================================
# GITIGNORE
# =============================================================================


class TestGitignore:
	"""Verify .gitignore exists and contains the critical entries."""

	def test_gitignore_exists(self):
		""".gitignore must exist — without it sensitive files can be committed."""
		assert (PROJECT_ROOT / ".gitignore").exists(), \
			".gitignore not found — Spellforge should have created this"

	def test_gitignore_ignores_venv(self):
		""".gitignore must exclude the virtual environment."""
		content = (PROJECT_ROOT / ".gitignore").read_text()
		assert ".venv/" in content, \
			".venv/ not in .gitignore — the virtual environment could be committed"

	def test_gitignore_ignores_pycache(self):
		""".gitignore must exclude Python bytecode cache."""
		content = (PROJECT_ROOT / ".gitignore").read_text()
		assert "__pycache__/" in content, \
			"__pycache__/ not in .gitignore — compiled Python files could be committed"

	def test_gitignore_ignores_env_files(self):
		""".gitignore must exclude .env files to prevent secret leakage."""
		content = (PROJECT_ROOT / ".gitignore").read_text()
		assert ".env" in content, \
			".env not in .gitignore — environment variables/secrets could be committed"


# =============================================================================
# CLAUDE CODE
# =============================================================================


class TestClaudeCode:
	"""Verify Claude Code and its supporting files were set up correctly."""

	def test_claude_md_exists(self):
		"""CLAUDE.md must exist — this is what tells Claude Code your project standards."""
		assert (PROJECT_ROOT / "CLAUDE.md").exists(), \
			"CLAUDE.md not found — Claude Code has no project context to work from"

	def test_claude_md_has_content(self):
		"""CLAUDE.md must not be empty — an empty file gives Claude Code nothing to work from."""
		claude_md = PROJECT_ROOT / "CLAUDE.md"
		assert claude_md.exists(), "CLAUDE.md does not exist"
		content = claude_md.read_text().strip()
		assert len(content) > 100, \
			"CLAUDE.md exists but appears to be mostly empty — Claude Code context is missing"

	def test_claude_settings_exists(self):
		"""Claude Code settings file must exist."""
		settings = PROJECT_ROOT / ".claude" / "settings.local.json"
		assert settings.exists(), \
			".claude/settings.local.json not found — Claude Code permissions are not configured"

	def test_post_edit_hook_exists(self):
		"""The post-edit hook that triggers Ruff on file save must exist."""
		hook = PROJECT_ROOT / ".claude" / "hooks" / "post_edit.sh"
		assert hook.exists(), \
			".claude/hooks/post_edit.sh not found — auto-lint on file edit is not set up"

	def test_post_edit_hook_is_executable(self):
		"""The post-edit hook must be executable — otherwise Claude Code will not run it."""
		hook = PROJECT_ROOT / ".claude" / "hooks" / "post_edit.sh"
		assert hook.exists(), "post_edit.sh does not exist — cannot check permissions"
		assert os.access(hook, os.X_OK), \
			"post_edit.sh exists but is not executable — run: chmod +x .claude/hooks/post_edit.sh"


# =============================================================================
# DIRECTORY STRUCTURE
# =============================================================================


class TestDirectoryStructure:
	"""Verify the full expected project directory structure is in place."""

	def test_tests_directory_exists(self):
		"""tests/ directory must exist — pytest discovers tests here."""
		assert (PROJECT_ROOT / "tests").is_dir(), \
			"tests/ directory not found — Spellforge should have scaffolded this"

	def test_docs_directory_exists(self):
		"""docs/ directory must exist — project documentation lives here."""
		assert (PROJECT_ROOT / "docs").is_dir(), \
			"docs/ directory not found — Spellforge should have scaffolded this"

	def test_tests_init_exists(self):
		"""tests/__init__.py must exist so pytest treats tests/ as a package."""
		assert (PROJECT_ROOT / "tests" / "__init__.py").exists(), \
			"tests/__init__.py not found — pytest may not discover tests correctly"

	def test_tests_conftest_exists(self):
		"""tests/conftest.py must exist — shared fixtures are defined here."""
		assert (PROJECT_ROOT / "tests" / "conftest.py").exists(), \
			"tests/conftest.py not found — shared test fixtures are not available"

	def test_prd_exists(self):
		"""docs/prd.md must exist — Claude Code reads this to understand the project."""
		assert (PROJECT_ROOT / "docs" / "prd.md").exists(), \
			"docs/prd.md not found — Claude Code has no product requirements to reference"

	def test_as_built_guide_exists(self):
		"""docs/as-built-project-guide.md must exist."""
		assert (PROJECT_ROOT / "docs" / "as-built-project-guide.md").exists(), \
			"docs/as-built-project-guide.md not found — Spellforge should have created this"
