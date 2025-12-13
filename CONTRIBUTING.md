# Contributing to DeskCloud MCP

Thank you for your interest in contributing! This document provides guidelines
for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/deskcloud-mcp.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest`
6. Commit: `git commit -m "Add your feature"`
7. Push: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/deskcloud/deskcloud-mcp.git
cd deskcloud-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio httpx ruff black

# Copy environment template
cp .env.example .env
# Edit .env with your configuration

# Run the server
uvicorn app.main:app --reload --port 8000
```

## Running with Docker

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d
```

## Code Style

We use the following tools to maintain code quality:

- **[Black](https://github.com/psf/black)** for code formatting
- **[Ruff](https://github.com/astral-sh/ruff)** for linting
- **Type hints** are encouraged for all functions
- **Docstrings** for public functions and classes

```bash
# Format code
black .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_sessions.py

# Run with coverage
pytest --cov=app --cov-report=html
```

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Update documentation if needed
- Add tests for new functionality
- Ensure all tests pass before submitting
- Follow the existing code style
- Write clear commit messages

### PR Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have updated the documentation accordingly

## Reporting Issues

When reporting issues, please include:

- Description of the bug or feature request
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Your environment (OS, Python version, Docker version)
- Relevant error messages and logs

Use the issue templates provided in the repository.

## Project Structure

```
deskcloud-mcp/
├── app/                    # Main application code
│   ├── api/               # REST API routes
│   ├── mcp/               # MCP server implementation
│   ├── services/          # Business logic
│   ├── db/                # Database models and repositories
│   └── core/              # Core utilities
├── docker/                # Docker configuration
├── docs/                  # Documentation
├── frontend/              # Web interface
├── tests/                 # Test suite
└── requirements.txt       # Dependencies
```

## Areas for Contribution

We welcome contributions in these areas:

- **Bug fixes** - Help us squash bugs
- **Documentation** - Improve docs, add examples
- **Tests** - Increase test coverage
- **Features** - New MCP tools, API endpoints
- **Performance** - Optimizations and improvements
- **Accessibility** - Make the frontend more accessible

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Questions?

- Open a [Discussion](https://github.com/deskcloud/deskcloud-mcp/discussions) for questions
- Check existing issues before opening a new one
- Join our community discussions

## License

By contributing to DeskCloud MCP, you agree that your contributions will be
licensed under the MIT License.

