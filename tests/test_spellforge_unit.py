"""
Unit tests for spellforge.py content-generation and pure helper functions.

These call functions directly with tmp_path fixtures, unlike the validation
tests in test_spellforge_bootstrap.py / test_spellforge_config.py which read
the already-bootstrapped project state on disk.

Note: subprocess-heavy install/ensure/verify functions and interactive UI
(press_any_key, get_project_path, show_installation_menu) are not covered
here — they require real tools, a live venv, or a TTY.
"""

import json
import os
import sys
from pathlib import Path

import pytest

# spellforge.py lives in the repo root; add it to the import path.
sys.path.insert(0, str(Path(__file__).parent.parent))
import spellforge  # noqa: I001


# =============================================================================
# InstallChoices
# =============================================================================


class TestInstallChoices:
	"""InstallChoices must default all optional tools to False so users explicitly opt in."""

	def test_all_defaults_false(self):
		choices = spellforge.InstallChoices()
		assert not choices.eslint
		assert not choices.prettier
		assert not choices.watchdog
		assert not choices.bandit

	def test_package_manager_defaults_to_pip(self):
		"""Non-interactive callers (e.g. repair mode) must get pip unless told otherwise."""
		choices = spellforge.InstallChoices()
		assert choices.package_manager == spellforge.PACKAGE_MANAGER_PIP


# =============================================================================
# _detect_venv_package_manager
# =============================================================================


class TestDetectVenvPackageManager:
	"""Repair mode reads pyvenv.cfg to re-target the venv's original package manager."""

	def test_missing_pyvenv_cfg_defaults_to_pip(self, tmp_path):
		venv_path = tmp_path / ".venv"
		venv_path.mkdir()
		assert spellforge._detect_venv_package_manager(venv_path) == spellforge.PACKAGE_MANAGER_PIP

	def test_stdlib_venv_pyvenv_cfg_is_pip(self, tmp_path):
		venv_path = tmp_path / ".venv"
		venv_path.mkdir()
		(venv_path / "pyvenv.cfg").write_text("home = /usr/bin\nversion = 3.13.0\n")
		assert spellforge._detect_venv_package_manager(venv_path) == spellforge.PACKAGE_MANAGER_PIP

	def test_uv_pyvenv_cfg_is_detected(self, tmp_path):
		venv_path = tmp_path / ".venv"
		venv_path.mkdir()
		(venv_path / "pyvenv.cfg").write_text("home = /usr/bin\nuv = 0.5.0\nversion = 3.13.0\n")
		assert spellforge._detect_venv_package_manager(venv_path) == spellforge.PACKAGE_MANAGER_UV


# =============================================================================
# _isolated_pip_env
# =============================================================================


class TestIsolatedPipEnv:
	"""Pip isolation env must block user-site installs and strip redirect variables."""

	def test_pip_user_disabled(self):
		env = spellforge._isolated_pip_env()
		assert env["PIP_USER"] == "0", "PIP_USER=0 required to block user-site installs"

	def test_require_virtualenv_enforced(self):
		env = spellforge._isolated_pip_env()
		assert env["PIP_REQUIRE_VIRTUALENV"] == "true", (
			"PIP_REQUIRE_VIRTUALENV must be true so pip refuses to install outside the venv"
		)

	def test_pip_target_stripped(self):
		env = spellforge._isolated_pip_env()
		assert "PIP_TARGET" not in env, "PIP_TARGET redirects installs — must be stripped"

	def test_pip_prefix_stripped(self):
		env = spellforge._isolated_pip_env()
		assert "PIP_PREFIX" not in env, "PIP_PREFIX redirects installs — must be stripped"

	def test_inherits_existing_env(self):
		"""Returned env must include existing PATH so executables remain reachable."""
		env = spellforge._isolated_pip_env()
		assert "PATH" in env, "PATH must be preserved in the isolated pip env"


# =============================================================================
# write_settings_local
# =============================================================================


class TestWriteSettingsLocal:
	"""write_settings_local generates .claude/settings.local.json."""

	def test_file_is_created(self, tmp_path):
		(tmp_path / ".claude").mkdir()
		spellforge.write_settings_local(tmp_path)
		assert (tmp_path / ".claude" / "settings.local.json").exists()

	def test_file_is_valid_json(self, tmp_path):
		(tmp_path / ".claude").mkdir()
		spellforge.write_settings_local(tmp_path)
		content = (tmp_path / ".claude" / "settings.local.json").read_text()
		parsed = json.loads(content)
		assert isinstance(parsed, dict)

	def test_permissions_allow_list_present(self, tmp_path):
		(tmp_path / ".claude").mkdir()
		spellforge.write_settings_local(tmp_path)
		data = json.loads((tmp_path / ".claude" / "settings.local.json").read_text())
		assert "permissions" in data
		assert "allow" in data["permissions"]
		assert len(data["permissions"]["allow"]) > 0

	def test_no_hooks_section(self, tmp_path):
		"""Quality gate is pre-commit only — settings.local.json must not contain hooks."""
		(tmp_path / ".claude").mkdir()
		spellforge.write_settings_local(tmp_path)
		data = json.loads((tmp_path / ".claude" / "settings.local.json").read_text())
		assert "hooks" not in data, (
			"settings.local.json must not define hooks — quality gate lives in git pre-commit"
		)


# =============================================================================
# write_claude_md
# =============================================================================


class TestWriteClaudeMd:
	"""write_claude_md generates CLAUDE.md with all required sections."""

	def _content(self, tmp_path: Path) -> str:
		spellforge.write_claude_md(tmp_path)
		return (tmp_path / "CLAUDE.md").read_text()

	def test_file_is_created(self, tmp_path):
		spellforge.write_claude_md(tmp_path)
		assert (tmp_path / "CLAUDE.md").exists()

	def test_quality_gate_is_precommit(self, tmp_path):
		content = self._content(tmp_path)
		assert "pre-commit hook" in content
		assert "not after every Claude edit" in content

	def test_working_practices_section_present(self, tmp_path):
		assert "## Working Practices" in self._content(tmp_path)

	def test_this_session_only_documented(self, tmp_path):
		assert "this session only" in self._content(tmp_path).lower()

	def test_new_branch_policy_documented(self, tmp_path):
		assert "new branch" in self._content(tmp_path).lower()

	def test_single_concern_pr_policy_documented(self, tmp_path):
		content = self._content(tmp_path).lower()
		assert "single" in content and ("feature" in content or "function" in content)

	def test_overwrites_existing_file(self, tmp_path):
		(tmp_path / "CLAUDE.md").write_text("stale content")
		spellforge.write_claude_md(tmp_path)
		assert "stale content" not in (tmp_path / "CLAUDE.md").read_text()


# =============================================================================
# write_gitignore
# =============================================================================


class TestWriteGitignore:
	"""write_gitignore generates .gitignore with entries that protect secrets and venv."""

	def test_file_is_created(self, tmp_path):
		spellforge.write_gitignore(tmp_path)
		assert (tmp_path / ".gitignore").exists()

	def test_venv_excluded(self, tmp_path):
		spellforge.write_gitignore(tmp_path)
		assert ".venv/" in (tmp_path / ".gitignore").read_text()

	def test_env_excluded(self, tmp_path):
		spellforge.write_gitignore(tmp_path)
		assert ".env" in (tmp_path / ".gitignore").read_text()

	def test_secrets_baseline_not_excluded(self, tmp_path):
		""".secrets.baseline must be committed, not ignored."""
		spellforge.write_gitignore(tmp_path)
		assert ".secrets.baseline" not in (tmp_path / ".gitignore").read_text()

	def test_skips_if_file_exists(self, tmp_path):
		(tmp_path / ".gitignore").write_text("custom rules")
		spellforge.write_gitignore(tmp_path)
		assert (tmp_path / ".gitignore").read_text() == "custom rules"


# =============================================================================
# configure_pyproject
# =============================================================================


class TestConfigurePyproject:
	"""configure_pyproject generates pyproject.toml with ruff + pytest config."""

	def test_file_is_created(self, tmp_path):
		spellforge.configure_pyproject(tmp_path, "my_project")
		assert (tmp_path / "pyproject.toml").exists()

	def test_project_name_embedded(self, tmp_path):
		spellforge.configure_pyproject(tmp_path, "my_project")
		assert "my_project" in (tmp_path / "pyproject.toml").read_text()

	def test_ruff_section_present(self, tmp_path):
		spellforge.configure_pyproject(tmp_path, "my_project")
		assert "[tool.ruff]" in (tmp_path / "pyproject.toml").read_text()

	def test_pytest_section_present(self, tmp_path):
		spellforge.configure_pyproject(tmp_path, "my_project")
		assert "[tool.pytest" in (tmp_path / "pyproject.toml").read_text()

	def test_skips_if_ruff_already_present(self, tmp_path):
		original = "[tool.ruff]\nline-length = 100\n"
		(tmp_path / "pyproject.toml").write_text(original)
		spellforge.configure_pyproject(tmp_path, "my_project")
		assert (tmp_path / "pyproject.toml").read_text() == original

	def test_appends_to_existing_file_without_ruff(self, tmp_path):
		(tmp_path / "pyproject.toml").write_text('[project]\nname = "old"\n')
		spellforge.configure_pyproject(tmp_path, "my_project")
		content = (tmp_path / "pyproject.toml").read_text()
		assert "[project]" in content
		assert "[tool.ruff]" in content


# =============================================================================
# write_precommit_hook
# =============================================================================


class TestWritePrecommitHook:
	"""write_precommit_hook generates an executable pre-commit hook with ruff and secret scanning."""

	def _setup(self, tmp_path: Path):
		(tmp_path / ".git" / "hooks").mkdir(parents=True)
		spellforge.write_precommit_hook(tmp_path, "/usr/local/bin/detect-secrets")
		return tmp_path / ".git" / "hooks" / "pre-commit"

	def test_hook_is_created(self, tmp_path):
		assert self._setup(tmp_path).exists()

	def test_hook_is_executable(self, tmp_path):
		hook = self._setup(tmp_path)
		assert os.access(hook, os.X_OK), "pre-commit hook must be executable"

	def test_hook_is_bash_script(self, tmp_path):
		assert self._setup(tmp_path).read_text().startswith("#!/bin/bash")

	def test_hook_calls_ruff_format(self, tmp_path):
		content = self._setup(tmp_path).read_text()
		assert "ruff" in content and "format" in content

	def test_hook_calls_ruff_check(self, tmp_path):
		content = self._setup(tmp_path).read_text()
		assert "ruff" in content and "check" in content

	def test_hook_calls_detect_secrets(self, tmp_path):
		assert "detect-secrets" in self._setup(tmp_path).read_text()

	def test_fatal_if_git_hooks_missing(self, tmp_path):
		"""write_precommit_hook must fail fast when .git/hooks does not exist."""
		with pytest.raises(SystemExit):
			spellforge.write_precommit_hook(tmp_path, "/usr/local/bin/detect-secrets")


# =============================================================================
# create_directory_structure
# =============================================================================


class TestCreateDirectoryStructure:
	"""create_directory_structure creates the .claude/ and docs/ directories."""

	def test_claude_dir_created(self, tmp_path):
		spellforge.create_directory_structure(tmp_path)
		assert (tmp_path / ".claude").is_dir()

	def test_docs_dir_created(self, tmp_path):
		spellforge.create_directory_structure(tmp_path)
		assert (tmp_path / "docs").is_dir()

	def test_idempotent_when_dirs_already_exist(self, tmp_path):
		"""Must not raise if directories are already present."""
		(tmp_path / ".claude").mkdir()
		(tmp_path / "docs").mkdir()
		spellforge.create_directory_structure(tmp_path)


# =============================================================================
# create_tests_directory
# =============================================================================


class TestCreateTestsDirectory:
	"""create_tests_directory creates tests/ with __init__, conftest, and a placeholder test."""

	def test_tests_dir_created(self, tmp_path):
		spellforge.create_tests_directory(tmp_path)
		assert (tmp_path / "tests").is_dir()

	def test_init_created(self, tmp_path):
		spellforge.create_tests_directory(tmp_path)
		assert (tmp_path / "tests" / "__init__.py").exists()

	def test_conftest_created(self, tmp_path):
		spellforge.create_tests_directory(tmp_path)
		assert (tmp_path / "tests" / "conftest.py").exists()

	def test_placeholder_test_created(self, tmp_path):
		spellforge.create_tests_directory(tmp_path)
		test_files = list((tmp_path / "tests").glob("test_*.py"))
		assert test_files, "at least one test_*.py file must be created"

	def test_skips_if_tests_dir_exists(self, tmp_path):
		"""Must not overwrite an existing tests/ directory."""
		(tmp_path / "tests").mkdir()
		(tmp_path / "tests" / "my_test.py").write_text("# keep me")
		spellforge.create_tests_directory(tmp_path)
		assert (tmp_path / "tests" / "my_test.py").read_text() == "# keep me"


# =============================================================================
# write_agent_docs
# =============================================================================


class TestWriteAgentDocs:
	"""write_agent_docs creates prd.md and as-built-project-guide.md under docs/."""

	def test_prd_created(self, tmp_path):
		(tmp_path / "docs").mkdir()
		spellforge.write_agent_docs(tmp_path)
		assert (tmp_path / "docs" / "prd.md").exists()

	def test_abpg_created(self, tmp_path):
		(tmp_path / "docs").mkdir()
		spellforge.write_agent_docs(tmp_path)
		assert (tmp_path / "docs" / "as-built-project-guide.md").exists()

	def test_prd_has_required_sections(self, tmp_path):
		(tmp_path / "docs").mkdir()
		spellforge.write_agent_docs(tmp_path)
		content = (tmp_path / "docs" / "prd.md").read_text()
		assert "## Goals" in content
		assert "## Features" in content

	def test_abpg_has_required_sections(self, tmp_path):
		(tmp_path / "docs").mkdir()
		spellforge.write_agent_docs(tmp_path)
		content = (tmp_path / "docs" / "as-built-project-guide.md").read_text()
		assert "## Directory Structure" in content
		assert "## Systems" in content

	def test_skips_existing_prd(self, tmp_path):
		(tmp_path / "docs").mkdir()
		(tmp_path / "docs" / "prd.md").write_text("custom prd")
		spellforge.write_agent_docs(tmp_path)
		assert (tmp_path / "docs" / "prd.md").read_text() == "custom prd"

	def test_skips_existing_abpg(self, tmp_path):
		(tmp_path / "docs").mkdir()
		(tmp_path / "docs" / "as-built-project-guide.md").write_text("custom guide")
		spellforge.write_agent_docs(tmp_path)
		assert (tmp_path / "docs" / "as-built-project-guide.md").read_text() == "custom guide"


# =============================================================================
# TOOL_MANIFEST
# =============================================================================


class TestToolManifest:
	"""TOOL_MANIFEST must have the right shape and correct required/optional flags."""

	def test_all_entries_have_five_fields(self):
		for entry in spellforge.TOOL_MANIFEST:
			assert len(entry) == 5, f"Entry {entry[0]!r} must have exactly 5 fields"

	def test_required_tools_include_core_set(self):
		required = {name for name, req, *_ in spellforge.TOOL_MANIFEST if req}
		for tool in (
			"Git",
			f"Python {spellforge.PYTHON_TARGET_LABEL}",
			"Claude Code",
			"Ruff",
			"detect-secrets",
		):
			assert tool in required, f"{tool!r} must be marked required in TOOL_MANIFEST"

	def test_optional_tools_include_frontend_set(self):
		optional = {name for name, req, *_ in spellforge.TOOL_MANIFEST if not req}
		assert "ESLint" in optional
		assert "Prettier" in optional

	def test_ruff_description_not_stale(self):
		"""Ruff entry must not claim it runs after every Claude edit — that hook was removed."""
		for name, _, _, _, why in spellforge.TOOL_MANIFEST:
			if name == "Ruff":
				assert "every Claude Code edit" not in why, (
					"Ruff TOOL_MANIFEST entry still references the removed post-edit hook"
				)


# =============================================================================
# Print helpers
# =============================================================================


class TestPrintHelpers:
	"""Print helpers must run without raising. Output content is not tested here."""

	def test_banner_runs(self, capsys):
		spellforge.banner()

	def test_step_runs(self, capsys):
		spellforge.step("🔍", "test step")

	def test_info_runs(self, capsys):
		spellforge.info("informational")

	def test_success_runs(self, capsys):
		spellforge.success("success")

	def test_warning_runs(self, capsys):
		spellforge.warning("warning")

	def test_error_runs(self, capsys):
		spellforge.error("error")


# =============================================================================
# fatal
# =============================================================================


class TestFatal:
	"""fatal() must exit with code 1."""

	def test_exits_with_code_1(self):
		with pytest.raises(SystemExit) as exc_info:
			spellforge.fatal("test fatal message")
		assert exc_info.value.code == 1
