
<p align="center">
  <img src="images/spellforge_readme.png" width="200" alt="Spellforge Logo">
</p>

# 🪄 Spellforge

> *Because setting up a Python project from scratch is a curse. Spellforge breaks it.*
> 
Spellforge is a Claude-powered Python project bootstrapper that conjures fully configured, production-ready Python projects from thin air — complete with colorful terminal output, fail-fast verification, and your personal coding standards baked right in.

No more copy-pasting boilerplate. No more forgetting to set up your `.gitignore`. No more "wait, did I configure the venv?" Just run the spell and get to building.

---

## ✨ Features

- 🤖 **Claude AI integration** — uses the Anthropic API to intelligently scaffold project structure based on your description
- 🎨 **Colorful terminal output** — because staring at a wall of grey text is a crime
- ⚡ **Fail-fast verification** — catches problems immediately before they become mysterious bugs later
- 📐 **Opinionated defaults** — Tom's personal coding standards and best practices baked in, so every project starts right
- 🗂️ **Full project setup** — virtual environments, directory structure, `requirements.txt`, `.gitignore`, and more
- 🔁 **Repeatable** — run it a hundred times, get a consistently great project every time

---

## 🖼️ Demo

> 📸 *Screenshots coming soon — add your terminal recordings here!*

You can drop an animated GIF or screenshot of a Spellforge run here. Tools like [Terminalizer](https://github.com/faressoft/terminalizer) or [Asciinema](https://asciinema.org/) work great for this.

---

## 🚀 Installation & Usage

### Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/spellforge.git
cd spellforge
```

### 2. Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get your API key ready

Spellforge will ask for your Anthropic API key during setup — no environment variables needed. Just have it ready to paste when prompted. You can get one from the [Anthropic Console](https://console.anthropic.com/).

### 5. Run Spellforge

```bash
python spellforge.py
```

Follow the prompts, describe your project, and watch the magic happen. ✨

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

Built by T-Squared as a tool to scratch his own itch — because every great project deserves a great start.

