<p align="center">
  <img src="images/spellforge_readme.png" width="200" alt="SpellForge Logo">
</p>

# 🪄 SpellForge

> *Because setting up a Python project from scratch is a curse. SpellForge breaks it.*

SpellForge is a Claude-powered Python project bootstrapper that conjures fully configured, production-ready Python projects from thin air — complete with colorful terminal output, fail-fast verification and your personal coding standards baked right in.

No more copy-pasting boilerplate. No more forgetting to set up your `.gitignore`. No more "wait, did I configure the venv?" Just run the spell and get to building.

---

## ✨ What SpellForge Sets Up

SpellForge walks you through an interactive menu, then installs and configures everything automatically. Here's exactly what you get:

### 🔒 Required (always installed)

| Tool | What it does | Why it matters |
|------|-------------|----------------|
| **Git** | Version control | Initialises a repo and wires up the pre-commit hook automatically |
| **Python venv** | Isolated environment | Keeps your project dependencies clean and separate from system Python |
| **Ruff** | Linter + formatter | Blazing fast — replaces flake8, isort, and black in one tool. Enforces consistent code style on every save |
| **pytest + pytest-cov** | Testing + coverage | Enforces 80% minimum test coverage so quality doesn't quietly erode |
| **detect-secrets** | Secret scanner | Scans every commit for API keys, passwords, and tokens before they ever leave your machine |
| **requests** | HTTP library | The go-to for any API calls your project needs |
| **Claude Code** | AI coding assistant | Installed globally via npm — powers AI-assisted development right in your terminal |
| **CLAUDE.md** | AI context file | Pre-written instructions that tell Claude Code your coding standards, project structure, and rules |
| **Pre-commit hook** | Automatic secret scanning | Runs detect-secrets on every `git commit` — you can't accidentally push a leaked key |
| **.gitignore** | Git exclusions | Pre-configured to ignore venv, pycache, secrets baseline, IDE files, and more |
| **pyproject.toml** | Project config | Configures Ruff rules, pytest settings, and project metadata in one place |
| **Directory structure** | Scaffolded layout | Creates `src/`, `tests/`, `docs/` and wires them up correctly from day one |

### ⚙️ Optional (your choice)

| Tool | What it does | Why you might want it |
|------|-------------|----------------------|
| **Bandit** | Python security scanner | Catches hardcoded passwords, unsafe `eval()`, weak crypto, and dangerous SQL patterns before they reach production |
| **ESLint** | JavaScript/TypeScript linter | Catches bugs and bad patterns in `.js`, `.ts`, `.jsx`, `.tsx` files — essential if your project has a frontend |
| **Prettier** | Frontend formatter | Enforces consistent formatting across JS, TS, HTML, CSS, JSON, YAML, and Markdown |
| **Watchdog** | Filesystem monitor | Watches for file changes in real time — great for auto-reloading scripts or triggering pipelines on data drops |

### 🎨 SpellForge itself

- **Colorful terminal output** — progress is clear, errors are obvious, nothing is a wall of grey text
- **Fail-fast verification** — every step is verified before moving on so problems surface immediately
- **Interactive install menu** — see exactly what will be installed before anything runs
- **Homebrew aware** — uses Homebrew if available, falls back gracefully in corporate environments where it's blocked

---

## 🖼️ Demo

> 📸 *Screenshots coming soon *

---

## 🚀 Installation & Usage

### Prerequisites

- Python 3.13.x (Spellforge pins generated projects to 3.13 and will `brew install python@3.13` if it's missing — see [Why 3.13?](#-why-python-313))
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone the repo

```bash
git clone https://github.com/tothomas69/spellforge.git
cd spellforge
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get your API key ready

SpellForge will ask for your Anthropic API key during setup — no environment variables needed. Just have it ready to paste when prompted. You can get one from the [Anthropic Console](https://console.anthropic.com/).

### 4. Run SpellForge

```bash
python spellforge.py
```

Follow the prompts, describe your project, and watch the magic happen. ✨

### 5. Verify the bootstrap

After SpellForge runs, confirm everything was set up correctly by running the built-in verification suite:
```bash
pytest tests/ -v
```

All tests should be green. This suite checks that every tool was installed correctly, all config files are in place, and your Claude Code environment is properly configured.

---

## 🔧 Repair Mode

If a previously bootstrapped project gets into a bad state — wrong Python version in the venv, missing tools, a broken post-edit hook — you don't have to start over. Run SpellForge in repair mode:

```bash
# Re-validate and reinstall, keeping the existing venv
python spellforge.py --repair /path/to/your/project

# Or, if the venv itself is suspect, blow it away and rebuild
python spellforge.py --repair /path/to/your/project --rebuild-venv
```

Repair mode only touches the Python interpreter, virtualenv, base packages, and post-edit hook. It deliberately leaves your git history, `pyproject.toml`, `CLAUDE.md`, `docs/`, `tests/`, and any other project files untouched.

---

## 🐍 Why Python 3.13?

SpellForge pins every new project to Python 3.13 instead of using whatever `python3` happens to be on PATH. The reason: `brew install python3` resolves to the *current* formula (3.14 at the time of writing), which is too new for the typical dependency matrix — pandas, pydantic, and other native-extension packages lag behind major releases. 3.13 is the current stable release with broad wheel coverage.

If you need to bump the target version, change the `PYTHON_TARGET_MINOR` constant near the top of `spellforge.py` — every version check in the script reads from it.

---

## 🤝 Contributing

Pull requests are welcome! This is a solo side project so contributions might take a little time to review, but good ideas are always appreciated.

### How to contribute

1. **Fork** the repo
2. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-cool-idea
   ```
3. **Make your changes** — please keep code well-commented and readable
4. **Test your changes** to make sure nothing breaks
5. **Submit a pull request** with a clear description of what you changed and why

### Guidelines

- Keep it Pythonic — follow PEP 8
- Comment your code like you're explaining it to a future version of yourself
- If you're adding a new feature, consider whether it fits the "bootstrapper" philosophy
- Open an issue first if you're planning something big — saves everyone time!

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

In short: do whatever you want with it. Just keep the copyright notice. 🙂

---

## 🙋 About

Built by Tom as a tool to scratch his own itch — because every great project deserves a great start.