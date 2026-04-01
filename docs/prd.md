# Product Requirements Document - spellforge

## What We Are Building

Spellforge is a project bootstrapper — a setup automation tool that takes a blank directory and conjures a fully configured, production-ready Python development environment in a single run.

Instead of spending an hour manually installing tools, creating config files, setting up git hooks, and wiring everything together every time you start a new project, you run one command and Spellforge handles all of it:

Installs and verifies every tool in the right order
Writes all config files with the correct paths baked in
Sets up quality gates so bad code and secrets can't sneak into git
Gives Claude Code everything it needs to understand the project from day one

The target user is a developer who starts new Python projects regularly and wants every one of them to start from the same solid, consistent foundation — without doing the same setup work over and over.
In one sentence: Spellforge eliminates new project setup so you can start writing code immediately.

## Goals

- Single-command Python project setup that takes a blank directory to a fully configured development environment
- Consistent project foundations so every new project starts from the same solid baseline of tools, configs, and quality gates
- Claude Code integration out of the box, with CLAUDE.md, hooks, and project documentation generated automatically

## Features

- Homebrew, Git, Python, and virtualenv setup with dependency installation
- Ruff linting and formatting with a pre-commit hook that auto-formats staged files
- detect-secrets pre-commit hook to prevent secrets from being committed
- Claude Code installation and configuration, including CLAUDE.md and hook scripts
- pytest with 80% code coverage enforcement via pyproject.toml configuration
- Optional tools via interactive installation menu: ESLint, Prettier, Bandit, Watchdog
- Interactive installation menu (`show_installation_menu()`) letting the user choose which optional tools to include

## Technical Requirements

- macOS only (all commands and paths assume macOS)
- Python 3.11+
- Node.js (required for Claude Code)
- Homebrew (optional for detect-secrets, with pip fallback if Homebrew is unavailable)

## Out of Scope

- Windows or Linux support
- CI/CD pipeline generation
- Deployment configuration
- Project templates beyond Python
