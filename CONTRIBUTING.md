# Contributing to ElectaVerse

Thank you for your interest in contributing to ElectaVerse! This guide will help you get started.

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+** — Backend runtime
- **Node.js 20+** — Frontend build tools
- **MySQL 8.0** — Primary database
- **Git** — Version control

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/anxmeshhh/Google-Prompt-Wars---Election-System.git
cd Google-Prompt-Wars---Election-System

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Configure your API keys

# Frontend setup
cd ../frontend
npm install
```

### Running Locally

```bash
# Terminal 1: Backend
cd backend && python app.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

## 📋 Code Standards

### Python (Backend)

- **Formatter**: Black (120 char line length)
- **Linter**: flake8 with max-complexity=15
- **Security**: bandit for vulnerability scanning
- **Type Hints**: Required on all public functions
- **Docstrings**: Required on all public classes and functions
- **Config**: `pyproject.toml` for tool configuration

### TypeScript/React (Frontend)

- **Linter**: ESLint with TypeScript plugin
- **Framework**: React 19 + Vite
- **Styling**: Vanilla CSS with design tokens

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add quiz leaderboard endpoint
fix: resolve JWT blacklist race condition
docs: update API documentation
test: add incident responder agent tests
refactor: extract validators to utils module
```

## 🧪 Testing

```bash
cd backend

# Run all tests with coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_simulation.py -v

# Run security scan
bandit -r . -x tests/ -ll
```

### Test Categories

| File | Tests | Focus |
|:---|:---|:---|
| `test_simulation.py` | 18 | Election clock, queues, incidents |
| `test_models.py` | 15 | Booth + Incident data models |
| `test_agents.py` | 18 | All 5 AI agents with mocked Gemini |
| `test_google_services.py` | 18 | GCS, Firebase, Cloud Logging |
| `test_security_hardening.py` | 20 | JWT, validators, headers |

## 🔒 Security

- Never commit API keys or credentials
- Use `.env` files for secrets (already in `.gitignore`)
- Report vulnerabilities via [SECURITY.md](SECURITY.md)
- All SQL queries use parameterized statements
- Input validation via `utils/validators.py`

## 📬 Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Write tests for new functionality
4. Ensure all tests pass: `pytest tests/ -v`
5. Ensure linting passes: `flake8 .`
6. Submit a PR with a clear description

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.
