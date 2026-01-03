# Contributing to PacketBuddy

First off, thank you for considering contributing to PacketBuddy! 🎉

PacketBuddy is an open-source project, and we love to receive contributions from our community. There are many ways to contribute, from writing tutorials or blog posts, improving the documentation, submitting bug reports and feature requests, or writing code which can be incorporated into PacketBuddy itself.

## 🤖 AI & Vibe Coding

We fully embrace the era of AI-driven development. **Vibe coders and AI-assisted developers are highly welcomed to contribute!**

PacketBuddy is designed to be **AI-ready at its best**. We maintain a hidden [`.agent/`](.agent/) directory containing high-level technical blueprints, architectural protocols, and maintenance guides specifically curated for LLMs and AI coding agents. This ensures that any AI tool you use—whether it's Cursor, Copilot, or a custom agent—has the immediate context needed to generate clean, compatible, and high-quality code.

If you're contributing with an AI sidekick, point it to the `.agent/` folder for instant project mastery.

## 💡 Ways to Contribute

### 1. **Report Bugs** 🐛

Found a bug? Help us fix it!

- Check if the bug was already reported in [Issues](../../issues)
- If not, [open a new issue](../../issues/new)
- Include:
  - Clear title and description
  - Steps to reproduce
  - Expected vs actual behavior
  - Your OS, Python version, and PacketBuddy version
  - Logs from `~/.packetbuddy/stderr.log` if relevant

### 2. **Suggest Features** ✨

Have an idea to make PacketBuddy better?

- Check [existing feature requests](../../issues?q=is%3Aissue+label%3Aenhancement)
- If it's new, [open a feature request](../../issues/new)
- Describe:
  - The problem it solves
  - How it should work
  - Why it's useful

### 3. **Improve Documentation** 📚

Help others use PacketBuddy!

- Fix typos or unclear explanations
- Add examples or tutorials
- Translate documentation
- Write blog posts or create videos

### 4. **Write Code** 💻

Ready to get your hands dirty?

- Pick an [issue labeled "good first issue"](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- Or browse [help wanted issues](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)
- See [Development Setup](#development-setup) below

## 🚀 Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- A NeonDB account (optional, for testing cloud sync)

### Setup Steps

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/packet-buddy.git
cd packet-buddy

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/packet-buddy.git

# 4. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Install dependencies (including dev dependencies)
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If we add this later

# 6. Run in development mode
python -m src.api.server

# 7. Open dashboard
open http://127.0.0.1:7373/dashboard
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_monitor.py
```

### Code Style

We follow PEP 8 with a few modifications:

```bash
# Format code with black
black src/

# Sort imports with isort
isort src/

# Check with flake8
flake8 src/

# Type checking with mypy
mypy src/
```

## 📝 Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/amazing-feature
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation if needed

### 3. Test Your Changes

```bash
# Run tests
pytest

# Test manually
python -m src.api.server
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add amazing feature"
```

**Commit Message Format:**

- `feat: new feature`
- `fix: bug fix`
- `docs: documentation changes`
- `style: formatting, missing semicolons, etc.`
- `refactor: code restructuring`
- `test: adding tests`
- `chore: maintenance tasks`

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/amazing-feature

# Go to GitHub and create a Pull Request
```

### 6. PR Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex areas
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
- [ ] Related issues linked

## 🎯 Project Structure

```
packet-buddy/
├── src/
│   ├── core/           # Core functionality
│   │   ├── monitor.py      # Network monitoring
│   │   ├── storage.py      # SQLite operations
│   │   ├── sync.py         # NeonDB sync
│   │   └── device.py       # Device management
│   ├── api/            # FastAPI server
│   │   ├── server.py       # Main server
│   │   └── routes.py       # API endpoints
│   ├── cli/            # Command-line interface
│   │   └── main.py         # CLI commands
│   └── utils/          # Utilities
│       ├── config.py       # Configuration
│       └── formatters.py   # Data formatting
├── dashboard/          # Web dashboard
│   ├── index.html          # Main HTML
│   ├── style.css           # Styles
│   └── app.js              # JavaScript
├── service/            # Auto-start configs
│   ├── macos/              # macOS LaunchAgent
│   └── windows/            # Windows Task Scheduler
└── tests/              # Tests (to be added)
```

## 🔍 Code Review Process

1. **Automated Checks**: CI/CD runs tests and linters
2. **Maintainer Review**: A maintainer reviews your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged
5. **Release**: Your contribution will be in the next release!

## 💬 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:

- Age, body size, disability
- Ethnicity, gender identity and expression
- Level of experience, education
- Nationality, personal appearance, race, religion
- Sexual identity and orientation

### Our Standards

**Positive behavior:**

- Being respectful and welcoming
- Being patient with beginners
- Accepting constructive criticism
- Focusing on what's best for the community
- Showing empathy

**Unacceptable behavior:**

- Trolling, insulting, or derogatory comments
- Public or private harassment
- Publishing others' private information
- Other unprofessional conduct

### Enforcement

Instances of unacceptable behavior may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

## 🎓 Beginner Resources

New to open source? No problem!

- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [First Timers Only](https://www.firsttimersonly.com/)
- [GitHub Flow Guide](https://guides.github.com/introduction/flow/)
- [Understanding Git](https://git-scm.com/book/en/v2)

## 📊 Development Priorities

### High Priority

- [ ] Add comprehensive test suite
- [ ] Improve error handling
- [ ] Add per-app tracking (requires root)
- [ ] Implement WebSocket for real-time updates
- [ ] Add bandwidth alerts

### Medium Priority

- [ ] Create mobile companion app
- [ ] Add email/Slack notifications
- [ ] Implement custom dashboard themes
- [ ] Add export to Google Sheets
- [ ] Build Docker container

### Low Priority

- [ ] Add more chart types
- [ ] Implement data compression for old records
- [ ] Add multi-language support
- [ ] Create browser extension

## ❓ Questions?

- **General Questions**: [GitHub Discussions](../../discussions)
- **Bug Reports**: [GitHub Issues](../../issues)
- **Real-time Chat**: [Discord](#) (if we create one)
- **Email**: <your-email@example.com>

## 🙏 Recognition

Contributors are recognized in:

- [AUTHORS.md](AUTHORS.md) file
- Release notes
- GitHub contributors page

Your contributions, no matter how small, are valued and appreciated!

---

**Thank you for making PacketBuddy better!** 🚀

Made with ❤️ by the PacketBuddy community
