# test_spellforge_config.py
#
# Spellforge Configuration Verification Tests
# =============================================
# Verifies that Ruff is configured correctly, CLAUDE.md contains the expected
# sections and coding standards, and the docs/ files were written with the
# right content structure.
#
# Run from your project root with:
#   pytest tests/test_spellforge_config.py -v

import tomllib
from pathlib import Path

# ── Project root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent


# =============================================================================
# RUFF CONFIGURATION
# Verifies that pyproject.toml has the correct Ruff settings matching
# Spellforge's coding standards — tabs, line length, rule selections.
# =============================================================================


class TestRuffConfiguration:
	"""Verify Ruff is configured correctly in pyproject.toml."""

	def _get_ruff_config(self) -> dict:
		"""Helper — load pyproject.toml and return the [tool.ruff] section."""
		pyproject = PROJECT_ROOT / "pyproject.toml"
		assert pyproject.exists(), "pyproject.toml does not exist"
		data = tomllib.loads(pyproject.read_text())
		assert "tool" in data and "ruff" in data["tool"], (
			"[tool.ruff] section missing from pyproject.toml"
		)
		return data["tool"]["ruff"]

	def test_ruff_uses_tabs_not_spaces(self):
		"""Ruff must be configured to enforce tabs — matches Spellforge coding standards."""
		ruff = self._get_ruff_config()
		fmt = ruff.get("format", {})
		assert fmt.get("indent-style") == "tab", (
			"Ruff indent-style is not 'tab' — spaces will be used instead of tabs"
		)

	def test_ruff_line_length_is_100(self):
		"""Ruff line length must be 100 — matches project coding standards."""
		ruff = self._get_ruff_config()
		assert ruff.get("line-length") == 100, (
			f"Ruff line-length is {ruff.get('line-length')} — expected 100"
		)

	def test_ruff_indent_width_is_4(self):
		"""Ruff indent width must be 4."""
		ruff = self._get_ruff_config()
		assert ruff.get("indent-width") == 4, (
			f"Ruff indent-width is {ruff.get('indent-width')} — expected 4"
		)

	def test_ruff_lint_selects_required_rules(self):
		"""Ruff must select E, F, I, and W rule sets."""
		ruff = self._get_ruff_config()
		lint = ruff.get("lint", {})
		selected = lint.get("select", [])
		for rule in ["E", "F", "I", "W"]:
			assert rule in selected, (
				f"Ruff rule set '{rule}' is not selected — linting coverage is incomplete"
			)

	def test_ruff_ignores_e501_line_length(self):
		"""E501 (line too long) must be ignored — developers are trusted on long strings."""
		ruff = self._get_ruff_config()
		lint = ruff.get("lint", {})
		ignored = lint.get("ignore", [])
		assert "E501" in ignored, (
			"E501 is not ignored — Ruff will flag long lines even where they are intentional"
		)

	def test_ruff_ignores_e303_blank_lines(self):
		"""E303 (too many blank lines) must be ignored — occasionally useful for readability."""
		ruff = self._get_ruff_config()
		lint = ruff.get("lint", {})
		ignored = lint.get("ignore", [])
		assert "E303" in ignored, (
			"E303 is not ignored — Ruff will flag blank lines used for readability"
		)

	def test_ruff_ignores_w191_tab_indentation(self):
		"""W191 must be ignored — we use tabs, so this warning would be constant noise."""
		ruff = self._get_ruff_config()
		lint = ruff.get("lint", {})
		ignored = lint.get("ignore", [])
		assert "W191" in ignored, (
			"W191 is not ignored — Ruff will warn about tabs even though tabs are required"
		)


# =============================================================================
# CLAUDE.MD
# Verifies that CLAUDE.md contains all the expected sections and key
# coding standards that Claude Code needs to work correctly.
# =============================================================================


class TestClaudeMd:
	"""Verify CLAUDE.md contains the expected sections and coding standards."""

	def _get_content(self) -> str:
		"""Helper — read CLAUDE.md content."""
		claude_md = PROJECT_ROOT / "CLAUDE.md"
		assert claude_md.exists(), "CLAUDE.md does not exist"
		return claude_md.read_text()

	def test_claude_md_has_project_documentation_section(self):
		"""CLAUDE.md must reference the docs/ files so Claude knows where to look."""
		assert "## Project Documentation" in self._get_content(), (
			"'## Project Documentation' section missing from CLAUDE.md"
		)

	def test_claude_md_references_as_built_guide(self):
		"""CLAUDE.md must reference docs/as-built-project-guide.md."""
		assert "docs/as-built-project-guide.md" in self._get_content(), (
			"docs/as-built-project-guide.md not referenced in CLAUDE.md"
		)

	def test_claude_md_has_coding_guidelines_section(self):
		"""CLAUDE.md must have a coding guidelines section."""
		assert "## Coding Guidelines" in self._get_content(), (
			"'## Coding Guidelines' section missing from CLAUDE.md"
		)

	def test_claude_md_specifies_tabs(self):
		"""CLAUDE.md must instruct Claude to use tabs for indentation."""
		assert "tabs" in self._get_content().lower(), (
			"Tab indentation requirement not mentioned in CLAUDE.md"
		)

	def test_claude_md_has_definition_of_done(self):
		"""CLAUDE.md must include a Definition of Done so Claude knows when work is complete."""
		assert "Definition of Done" in self._get_content(), (
			"'Definition of Done' missing from CLAUDE.md — Claude has no completion criteria"
		)

	def test_claude_md_specifies_80_percent_coverage(self):
		"""CLAUDE.md must specify the 80% coverage requirement."""
		assert "80%" in self._get_content(), "80% coverage requirement not mentioned in CLAUDE.md"

	def test_claude_md_has_error_handling_section(self):
		"""CLAUDE.md must have error handling guidelines."""
		assert (
			"## Error Handling" in self._get_content() or "Error Handling" in self._get_content()
		), "Error handling guidelines missing from CLAUDE.md"

	def test_claude_md_has_development_environment_section(self):
		"""CLAUDE.md must specify the development environment (macOS)."""
		assert "## Development Environment" in self._get_content(), (
			"'## Development Environment' section missing from CLAUDE.md"
		)

	def test_claude_md_specifies_macos(self):
		"""CLAUDE.md must specify macOS so Claude uses the right commands."""
		assert "macOS" in self._get_content(), (
			"macOS not specified in CLAUDE.md — Claude may suggest Linux/Windows commands"
		)

	def test_claude_md_has_as_built_maintenance_requirement(self):
		"""CLAUDE.md must require as-built guide updates before commits."""
		assert "as-built-project-guide.md" in self._get_content(), (
			"As-built guide maintenance requirement missing from CLAUDE.md"
		)

	def test_claude_md_has_working_practices_section(self):
		"""CLAUDE.md must have a Working Practices section for branch and PR discipline."""
		assert "## Working Practices" in self._get_content(), (
			"'## Working Practices' section missing from CLAUDE.md"
		)

	def test_claude_md_specifies_session_only_permissions(self):
		"""CLAUDE.md must instruct Claude to prefer 'this session only' permission grants."""
		assert "this session only" in self._get_content().lower(), (
			"'this session only' permission preference missing from CLAUDE.md"
		)

	def test_claude_md_requires_new_branch_per_task(self):
		"""CLAUDE.md must require a new branch before starting any task."""
		assert "new branch" in self._get_content().lower(), (
			"New branch requirement missing from CLAUDE.md"
		)

	def test_claude_md_requires_single_concern_prs(self):
		"""CLAUDE.md must prohibit bundling unrelated changes in one PR."""
		content = self._get_content().lower()
		assert "single" in content and ("feature" in content or "function" in content), (
			"Single-concern PR requirement missing from CLAUDE.md"
		)


# =============================================================================
# DOCS
# Verifies that as-built-project-guide.md was written correctly with the
# expected structure that Claude Code relies on.
# =============================================================================


class TestDocs:
	"""Verify docs/ files contain the expected structure."""

	def test_as_built_guide_has_design_intent_section(self):
		"""as-built-project-guide.md must have a Design Intent section."""
		abpg = PROJECT_ROOT / "docs" / "as-built-project-guide.md"
		assert abpg.exists(), "docs/as-built-project-guide.md does not exist"
		assert "## Design Intent" in abpg.read_text(), (
			"'## Design Intent' section missing from as-built-project-guide.md"
		)

	def test_as_built_guide_has_what_we_are_building_section(self):
		"""as-built-project-guide.md must have a 'What We Are Building' section."""
		abpg = PROJECT_ROOT / "docs" / "as-built-project-guide.md"
		assert abpg.exists(), "docs/as-built-project-guide.md does not exist"
		assert "### What We Are Building" in abpg.read_text(), (
			"'### What We Are Building' section missing from as-built-project-guide.md"
		)

	def test_as_built_guide_has_goals_section(self):
		"""as-built-project-guide.md must have a Goals section."""
		abpg = PROJECT_ROOT / "docs" / "as-built-project-guide.md"
		assert abpg.exists(), "docs/as-built-project-guide.md does not exist"
		assert "### Goals" in abpg.read_text(), (
			"'### Goals' section missing from as-built-project-guide.md"
		)

	def test_as_built_guide_has_directory_structure_section(self):
		"""as-built-project-guide.md must have a Directory Structure section."""
		abpg = PROJECT_ROOT / "docs" / "as-built-project-guide.md"
		assert abpg.exists(), "docs/as-built-project-guide.md does not exist"
		assert "## Directory Structure" in abpg.read_text(), (
			"'## Directory Structure' section missing from as-built-project-guide.md"
		)

	def test_as_built_guide_has_systems_section(self):
		"""as-built-project-guide.md must have a Systems section."""
		abpg = PROJECT_ROOT / "docs" / "as-built-project-guide.md"
		assert abpg.exists(), "docs/as-built-project-guide.md does not exist"
		assert "## Systems" in abpg.read_text(), (
			"'## Systems' section missing from as-built-project-guide.md"
		)

	def test_as_built_guide_has_architecture_decisions_section(self):
		"""as-built-project-guide.md must have an Architecture Decisions section."""
		abpg = PROJECT_ROOT / "docs" / "as-built-project-guide.md"
		assert abpg.exists(), "docs/as-built-project-guide.md does not exist"
		assert "## Architecture Decisions" in abpg.read_text(), (
			"'## Architecture Decisions' section missing from as-built-project-guide.md"
		)
