# Open Source Release Checklist

> ⚠️ **Context**: See [`MASTER_ROADMAP.md`](./MASTER_ROADMAP.md) for project overview.

**Author:** Pablo Schaffner  
**Date:** December 2025  
**Status:** Pre-Release Preparation  
**Purpose:** Prepare the codebase for public open source release

---

## Table of Contents

1. [Overview](#overview)
2. [Repository Strategy](#repository-strategy)
3. [Files to Remove](#files-to-remove)
4. [Files to Create](#files-to-create)
5. [Code Audit](#code-audit)
6. [Documentation Updates](#documentation-updates)
7. [GitHub Repository Setup](#github-repository-setup)
8. [Pre-Publish Verification](#pre-publish-verification)
9. [Subtree Compatibility](#subtree-compatibility)
10. [PyPI Publishing](#pypi-publishing)
11. [Docker Hub Publishing](#docker-hub-publishing)
12. [Post-Publish Tasks](#post-publish-tasks)
13. [Checklist Summary](#checklist-summary)

---

## Overview

### What We're Doing

Preparing the codebase for public release as `deskcloud-mcp` (MIT license). This repo will serve as:

1. **Standalone open source project** - Self-hostable MCP server
2. **PyPI package** - `pip install deskcloud-mcp` / `uvx deskcloud-mcp`
3. **Docker images** - `deskcloud/session` for isolated sessions
4. **Subtree for premium repo** - Core synced into `deskcloud-platform`

### Key Principles

- **No business strategy leaks** - Remove pricing, roadmap, premium plans
- **Self-hosting focused** - README should help users run their own instance
- **Clean history** - New repo without sensitive commit history
- **Contributor-friendly** - Clear contribution guidelines
- **Brand-forward** - Name creates association with deskcloud.app

---

## Repository Strategy

### Naming

| Repository | Name | Visibility |
|------------|------|------------|
| **Open Source** | `deskcloud-mcp` | Public |
| **Premium** | `deskcloud-platform` | Private |

### Published Artifacts

| Artifact | Registry | Install Command |
|----------|----------|-----------------|
| `deskcloud-mcp` | PyPI | `pip install deskcloud-mcp` |
| `deskcloud/session` | Docker Hub | Auto-pulled by pip package |
| `deskcloud/mcp` | Docker Hub | `docker run deskcloud/mcp` |

### Two-Repository Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Repository Strategy                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PUBLIC: deskcloud-mcp                                                      │
│  ══════════════════════                                                     │
│  • MIT License                                                              │
│  • Published to PyPI + Docker Hub                                           │
│  • Self-hosting instructions                                                │
│  • Community contributions welcome                                          │
│  • NO pricing, premium features, business plans                             │
│                                                                             │
│                    │                                                        │
│                    │ git subtree                                            │
│                    ▼                                                        │
│                                                                             │
│  PRIVATE: deskcloud-platform                                                │
│  ═══════════════════════════                                                │
│  • Premium features (Connect Agent, Recording, etc.)                        │
│  • Frontend (Next.js dashboard)                                             │
│  • docs/plans/ folder (moved here)                                          │
│  • Business logic                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Publishing Approach

```bash
# Don't push this repo directly - create fresh repo without history
# This avoids exposing any sensitive commits

# 1. Create clean export (no .git history)
git archive --format=tar HEAD | tar -x -C /path/to/clean-export

# 2. Remove private files
rm -rf /path/to/clean-export/docs/plans

# 3. Initialize fresh repo
cd /path/to/clean-export
git init
git add .
git commit -m "Initial open source release"

# 4. Push to public repo
git remote add origin git@github.com:YOUR_ORG/mcp-computer-use.git
git push -u origin main
```

---

## Files to Remove

### Before Publishing - MUST Remove

| Path | Reason |
|------|--------|
| `docs/plans/` | Contains business strategy, pricing, premium roadmap |
| `.env` | May contain secrets |
| `.env.local` | May contain secrets |
| `.env.production` | May contain secrets |
| `*.log` | May contain sensitive data |
| `.DS_Store` | macOS artifacts |
| `__pycache__/` | Python bytecode |
| `.pytest_cache/` | Test cache |
| `.mypy_cache/` | Type checker cache |

### Files to Review Before Publishing

| Path | Action |
|------|--------|
| `README.md` | Rewrite for public audience |
| `.gitignore` | Ensure secrets patterns included |
| `app/config.py` | Check for hardcoded values |
| `docker-compose.yml` | Remove any internal service refs |

---

## Files to Create

### Required for Open Source Release

```
mcp-computer-use/
├── LICENSE                        # MIT License (if not present)
├── CONTRIBUTING.md                # How to contribute
├── CODE_OF_CONDUCT.md             # Community standards
├── SECURITY.md                    # Vulnerability reporting
├── CHANGELOG.md                   # Version history
├── .env.example                   # Environment variable template
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md          # Bug report template
│   │   └── feature_request.md     # Feature request template
│   ├── PULL_REQUEST_TEMPLATE.md   # PR checklist
│   └── workflows/
│       ├── ci.yml                 # Run tests on PR
│       └── lint.yml               # Code quality checks
└── docs/
    ├── SELF_HOSTING.md            # Detailed self-hosting guide
    └── API.md                     # API documentation
```

### File Contents

#### LICENSE (MIT)

```
MIT License

Copyright (c) 2025 [Your Name/Org]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

#### CONTRIBUTING.md

```markdown
# Contributing to MCP Computer Use

Thank you for your interest in contributing! This document provides guidelines
for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/mcp-computer-use.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest`
6. Commit: `git commit -m "Add your feature"`
7. Push: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment template
cp .env.example .env
# Edit .env with your configuration

# Run the server
python -m app.main
```

## Code Style

- We use [Black](https://github.com/psf/black) for code formatting
- We use [Ruff](https://github.com/astral-sh/ruff) for linting
- Type hints are encouraged
- Docstrings for public functions

```bash
# Format code
black .

# Lint code
ruff check .
```

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Update documentation if needed
- Add tests for new functionality
- Ensure all tests pass
- Follow the existing code style

## Reporting Issues

- Use the issue templates
- Include reproduction steps
- Include error messages and logs
- Specify your environment (OS, Python version, etc.)

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Questions?

Open a [Discussion](https://github.com/YOUR_ORG/mcp-computer-use/discussions) for questions.
```

#### CODE_OF_CONDUCT.md

```markdown
# Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

## Our Standards

Examples of behavior that contributes to a positive environment:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior:

* The use of sexualized language or imagery
* Trolling, insulting/derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information without permission
* Other conduct which could reasonably be considered inappropriate

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the project maintainers. All complaints will be reviewed and
investigated and will result in a response that is deemed necessary and
appropriate to the circumstances.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org/),
version 2.0.
```

#### SECURITY.md

```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by emailing:

**security@[yourdomain].com**

Please do NOT open a public GitHub issue for security vulnerabilities.

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes

### Response Timeline

- **24 hours**: Initial acknowledgment
- **72 hours**: Assessment and severity determination
- **7 days**: Fix development (for critical issues)
- **30 days**: Public disclosure (after fix is released)

## Security Best Practices

When self-hosting this project:

1. **Never expose VNC ports publicly** - Use a reverse proxy with authentication
2. **Use HTTPS** - Encrypt all traffic
3. **Rotate API keys** - Regularly rotate your Anthropic API keys
4. **Limit access** - Use firewall rules to restrict access
5. **Keep updated** - Regularly update to the latest version
```

#### .env.example

```bash
# =============================================================================
# MCP Computer Use - Environment Configuration
# =============================================================================
# Copy this file to .env and fill in your values
# DO NOT commit .env to version control

# -----------------------------------------------------------------------------
# Server Configuration
# -----------------------------------------------------------------------------
HOST=0.0.0.0
PORT=8000
DEBUG=false

# -----------------------------------------------------------------------------
# Anthropic API (BYOK - Bring Your Own Key)
# -----------------------------------------------------------------------------
# Get your API key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-...

# -----------------------------------------------------------------------------
# Database (Optional - defaults to SQLite)
# -----------------------------------------------------------------------------
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/mcp_computer_use

# For SQLite (default):
# DATABASE_URL=sqlite:///./data/sessions.db

# -----------------------------------------------------------------------------
# Display Configuration
# -----------------------------------------------------------------------------
# Starting display number for X11 sessions
DISPLAY_START=100

# Screen resolution
SCREEN_WIDTH=1920
SCREEN_HEIGHT=1080

# -----------------------------------------------------------------------------
# Session Limits
# -----------------------------------------------------------------------------
MAX_CONCURRENT_SESSIONS=10
SESSION_TIMEOUT_MINUTES=60

# -----------------------------------------------------------------------------
# VNC Configuration
# -----------------------------------------------------------------------------
VNC_START_PORT=5900
NOVNC_START_PORT=6080

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------
# Secret key for JWT tokens (generate with: openssl rand -hex 32)
SECRET_KEY=your-secret-key-here

# CORS allowed origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

#### .github/ISSUE_TEMPLATE/bug_report.md

```markdown
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Describe the Bug
A clear and concise description of what the bug is.

## To Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Screenshots/Logs
If applicable, add screenshots or log output to help explain your problem.

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python Version: [e.g., 3.11]
- Docker Version: [e.g., 24.0.5]
- Browser (if applicable): [e.g., Chrome 120]

## Additional Context
Add any other context about the problem here.
```

#### .github/ISSUE_TEMPLATE/feature_request.md

```markdown
---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Is your feature request related to a problem?
A clear and concise description of what the problem is.

## Describe the Solution You'd Like
A clear and concise description of what you want to happen.

## Describe Alternatives You've Considered
A clear and concise description of any alternative solutions or features you've considered.

## Additional Context
Add any other context or screenshots about the feature request here.
```

#### .github/PULL_REQUEST_TEMPLATE.md

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Related Issues
Closes #(issue number)
```

#### .github/workflows/ci.yml

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint with ruff
        run: |
          ruff check .

      - name: Check formatting with black
        run: |
          black --check .

      - name: Run tests
        run: |
          pytest -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Code Audit

### Automated Scans to Run

```bash
# =============================================================================
# Run these commands to find potential issues before publishing
# =============================================================================

# 1. Search for hardcoded domains/URLs
echo "=== Checking for hardcoded domains ==="
rg -i "deskcloud\.app|deskcloud\.cc" --type py
rg -i "render\.com|vercel\.com|vercel\.app" --type py
rg -i "api\.(deskcloud|example)" --type py

# 2. Search for potential secrets/credentials
echo "=== Checking for potential secrets ==="
rg -i "api[_-]?key\s*=\s*['\"][^'\"]+['\"]" --type py
rg -i "secret[_-]?key\s*=\s*['\"][^'\"]+['\"]" --type py
rg -i "password\s*=\s*['\"][^'\"]+['\"]" --type py
rg -i "token\s*=\s*['\"][^'\"]+['\"]" --type py
rg -i "sk-ant-" --type py  # Anthropic API key pattern

# 3. Search for premium/business references
echo "=== Checking for premium references ==="
rg -i "premium|pro tier|paid|subscription|pricing" --type py
rg -i "deskcloud connect|connect agent" --type py
rg -i "video recording|session recording" --type py

# 4. Search for internal comments
echo "=== Checking for internal TODOs ==="
rg -i "TODO.*premium|TODO.*paid|TODO.*business" --type py
rg -i "FIXME|HACK|XXX" --type py

# 5. Search for localhost/internal IPs
echo "=== Checking for internal IPs ==="
rg "localhost|127\.0\.0\.1|0\.0\.0\.0" --type py
rg "192\.168\.|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2[0-9]|3[0-1])\." --type py

# 6. Use trufflehog for comprehensive secret scanning
echo "=== Running trufflehog ==="
pip install trufflehog3
trufflehog3 --no-history .

# 7. Check for large binary files
echo "=== Checking for large files ==="
find . -type f -size +1M -not -path "./.git/*"
```

### Manual Review Required

| File/Area | What to Check |
|-----------|---------------|
| `app/config.py` | No hardcoded production values |
| `app/api/routes/*.py` | No premium endpoint stubs |
| `README.md` | No deskcloud.app mentions, no pricing |
| `docker-compose.yml` | No internal service references |
| Comments in code | No business strategy notes |
| Error messages | No internal architecture leaks |

---

## Documentation Updates

### README.md - Complete Rewrite

The public README should be structured as:

```markdown
# MCP Computer Use

> Open source MCP server for AI-controlled virtual desktops

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

MCP Computer Use is an open-source implementation of the Model Context Protocol
(MCP) that enables AI assistants like Claude to control virtual desktop
environments. Perfect for:

- 🤖 **AI Automation** - Let Claude browse the web and use desktop apps
- 🧪 **Testing** - Automated UI testing with AI
- 📚 **Training** - Create demonstrations and tutorials
- 🔬 **Research** - Study AI agent behavior

## Features

- ✅ **MCP Protocol** - Works with Cursor IDE and Claude Desktop
- ✅ **Isolated Sessions** - Each session gets its own virtual desktop
- ✅ **Multi-Session** - Run multiple concurrent sessions
- ✅ **Live Viewing** - Watch AI in real-time via VNC
- ✅ **BYOK** - Bring your own Anthropic API key
- ✅ **Self-Hostable** - Run on your own infrastructure

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/YOUR_ORG/mcp-computer-use.git
cd mcp-computer-use
cp .env.example .env
# Edit .env with your Anthropic API key
docker-compose up
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/YOUR_ORG/mcp-computer-use.git
cd mcp-computer-use

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your configuration

# Run
python -m app.main
```

### Connect to Cursor IDE

Add to your Cursor settings:

```json
{
  "mcp": {
    "servers": {
      "computer-use": {
        "url": "http://localhost:8000/mcp"
      }
    }
  }
}
```

## Documentation

- [Self-Hosting Guide](docs/SELF_HOSTING.md)
- [API Reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

To report security vulnerabilities, see [SECURITY.md](SECURITY.md).

## License

MIT License - see [LICENSE](LICENSE)
```

### Remove from README

- ❌ Any mention of deskcloud.app
- ❌ Pricing information
- ❌ Premium feature teasers
- ❌ Business roadmap
- ❌ Links to paid services

---

## GitHub Repository Setup

### Repository Settings

| Setting | Value |
|---------|-------|
| **Visibility** | Public |
| **Description** | "Open source MCP server for AI-controlled virtual desktops" |
| **Topics** | `mcp`, `claude`, `ai-agents`, `computer-use`, `automation`, `anthropic` |
| **Website** | Link to documentation |
| **Wiki** | Disabled (use docs/ folder) |
| **Issues** | Enabled |
| **Discussions** | Enabled |
| **Sponsorships** | Optional |

### Branch Protection (after publishing)

| Rule | Setting |
|------|---------|
| **Protected branch** | `main` |
| **Require PR** | Yes |
| **Require reviews** | 1 |
| **Require status checks** | CI must pass |
| **Include administrators** | Optional |

### Labels to Create

| Label | Color | Description |
|-------|-------|-------------|
| `bug` | `#d73a4a` | Something isn't working |
| `enhancement` | `#a2eeef` | New feature or request |
| `documentation` | `#0075ca` | Documentation improvements |
| `good first issue` | `#7057ff` | Good for newcomers |
| `help wanted` | `#008672` | Extra attention is needed |
| `question` | `#d876e3` | Further information is requested |
| `wontfix` | `#ffffff` | This will not be worked on |

---

## Pre-Publish Verification

### Verification Checklist

```bash
#!/bin/bash
# pre-publish-check.sh

echo "=== MCP Computer Use - Pre-Publish Verification ==="

# 1. Check for .env files
echo "Checking for .env files..."
if ls .env* 2>/dev/null; then
    echo "❌ FAIL: .env files found - remove before publishing"
    exit 1
else
    echo "✅ PASS: No .env files"
fi

# 2. Check for docs/plans
echo "Checking for docs/plans..."
if [ -d "docs/plans" ]; then
    echo "❌ FAIL: docs/plans exists - remove before publishing"
    exit 1
else
    echo "✅ PASS: No docs/plans folder"
fi

# 3. Check for required files
echo "Checking for required files..."
for file in LICENSE README.md CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md .env.example; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done

# 4. Check for secrets
echo "Checking for potential secrets..."
if rg -q "sk-ant-" --type py 2>/dev/null; then
    echo "❌ FAIL: Potential Anthropic API key found"
    exit 1
else
    echo "✅ PASS: No obvious API keys"
fi

# 5. Test installation
echo "Testing installation..."
python -m venv /tmp/test-venv
source /tmp/test-venv/bin/activate
pip install -r requirements.txt -q
if [ $? -eq 0 ]; then
    echo "✅ PASS: Dependencies install correctly"
else
    echo "❌ FAIL: Dependency installation failed"
fi
deactivate
rm -rf /tmp/test-venv

# 6. Run tests
echo "Running tests..."
pytest -q
if [ $? -eq 0 ]; then
    echo "✅ PASS: Tests pass"
else
    echo "❌ FAIL: Tests failed"
fi

echo "=== Verification Complete ==="
```

---

## Subtree Compatibility

### For Smooth Syncing to Premium Repo

| Consideration | Implementation |
|---------------|----------------|
| **Module imports** | Use relative imports: `from .services import ...` |
| **Configuration** | Environment-based only, no hardcoded paths |
| **Dependencies** | Core deps in `requirements.txt`, premium adds extras |
| **Entry point** | Clear module structure: `python -m app.main` |
| **No premium code** | Don't add premium stubs that need removal |

### Premium Repo Structure

```
deskcloud-platform/
├── core/                          # git subtree from mcp-computer-use
│   ├── app/
│   ├── docs/                      # Public docs only
│   ├── requirements.txt
│   └── ...
├── docs/
│   └── plans/                     # Moved here from public repo
├── frontend/                      # Next.js app
├── backend-premium/               # Premium API extensions
├── connect-agent/                 # Desktop agent
└── requirements-premium.txt       # Additional deps
```

### Subtree Commands

```bash
# Initial setup in premium repo
git subtree add --prefix=core git@github.com:puntorigen/deskcloud-mcp.git main --squash

# Pull updates from public repo
git subtree pull --prefix=core git@github.com:puntorigen/deskcloud-mcp.git main --squash

# Push fixes back to public repo (if fixing core bugs in premium repo)
git subtree push --prefix=core git@github.com:puntorigen/deskcloud-mcp.git main
```

---

## PyPI Publishing

### Package Structure

```
deskcloud-mcp/
├── src/
│   └── deskcloud_mcp/          # Package (underscore for Python)
│       ├── __init__.py
│       ├── __main__.py         # Entry point
│       ├── server.py           # MCP server
│       ├── container.py        # Docker/Podman management
│       └── ...
├── pyproject.toml              # Package config
├── README.md
└── LICENSE
```

### pyproject.toml

```toml
[project]
name = "deskcloud-mcp"
version = "0.1.0"
description = "MCP server for AI-controlled virtual desktops"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
keywords = ["mcp", "claude", "ai", "automation", "desktop", "anthropic"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "mcp>=0.1.0",
    "anthropic>=0.18.0",
    "docker>=7.0.0",
    "Pillow>=10.0.0",
    "httpx>=0.25.0",
]

[project.scripts]
deskcloud-mcp = "deskcloud_mcp.__main__:main"

[project.urls]
Homepage = "https://deskcloud.app"
Repository = "https://github.com/puntorigen/deskcloud-mcp"
Documentation = "https://github.com/puntorigen/deskcloud-mcp#readme"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/deskcloud_mcp"]
```

### Publishing to PyPI

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ deskcloud-mcp

# If all good, upload to PyPI
twine upload dist/*
```

### GitHub Actions for PyPI

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*
```

---

## Docker Hub Publishing

### Images to Publish

| Image | Purpose | Dockerfile |
|-------|---------|------------|
| `deskcloud/session` | Individual session container | `docker/Dockerfile.session` |
| `deskcloud/mcp` | All-in-one server | `docker/Dockerfile.mcp` |

### Session Container (deskcloud/session)

```dockerfile
# docker/Dockerfile.session
FROM ubuntu:22.04

# Install X11, VNC, browser, and tools
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    firefox \
    python3 \
    python3-pip \
    xdotool \
    scrot \
    && rm -rf /var/lib/apt/lists/*

# Install Python tools
RUN pip3 install pyautogui pillow

# Setup VNC password (optional, can be overridden)
RUN mkdir -p ~/.vnc && x11vnc -storepasswd deskcloud ~/.vnc/passwd

# Copy entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports
EXPOSE 5900 6080

ENTRYPOINT ["/entrypoint.sh"]
```

### Building and Pushing

```bash
# Build session image
docker build -t deskcloud/session:latest -f docker/Dockerfile.session .

# Build all-in-one image
docker build -t deskcloud/mcp:latest -f docker/Dockerfile.mcp .

# Push to Docker Hub
docker push deskcloud/session:latest
docker push deskcloud/mcp:latest

# Tag with version
docker tag deskcloud/session:latest deskcloud/session:0.1.0
docker push deskcloud/session:0.1.0
```

### GitHub Actions for Docker Hub

```yaml
# .github/workflows/docker.yml
name: Build and Push Docker Images

on:
  release:
    types: [published]
  push:
    branches: [main]
    paths:
      - 'docker/**'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and push session image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile.session
          push: true
          tags: |
            deskcloud/session:latest
            deskcloud/session:${{ github.ref_name }}
      
      - name: Build and push mcp image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile.mcp
          push: true
          tags: |
            deskcloud/mcp:latest
            deskcloud/mcp:${{ github.ref_name }}
```

### Container Runtime Detection

The pip package should detect available container runtime:

```python
# src/deskcloud_mcp/container.py
import shutil
import subprocess

def get_container_runtime() -> str:
    """Detect available container runtime (Docker or Podman)."""
    
    # Try Docker first
    if shutil.which("docker"):
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return "docker"
        except subprocess.TimeoutExpired:
            pass
    
    # Try Podman as fallback
    if shutil.which("podman"):
        try:
            result = subprocess.run(
                ["podman", "info"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return "podman"
        except subprocess.TimeoutExpired:
            pass
    
    raise RuntimeError(
        "deskcloud-mcp requires Docker or Podman to run sessions.\n\n"
        "Install Docker: https://docs.docker.com/get-docker/\n"
        "Or Podman: https://podman.io/getting-started/installation"
    )
```

---

## Post-Publish Tasks

### Immediately After Publishing

- [ ] Verify GitHub repo is accessible
- [ ] Test `git clone` works
- [ ] Test `pip install deskcloud-mcp` works
- [ ] Test `docker pull deskcloud/session` works
- [ ] Test `uvx deskcloud-mcp` works
- [ ] Verify README renders correctly on PyPI
- [ ] Announce on social media (optional)
- [ ] Update any external links

### Ongoing Maintenance

- [ ] Monitor issues and discussions
- [ ] Respond to PRs
- [ ] Keep dependencies updated
- [ ] Security patches
- [ ] Sync subtree regularly
- [ ] Update Docker images when base images update
- [ ] Publish new PyPI versions for releases

---

## Checklist Summary

### 🔴 Critical (Must Do)

- [ ] Remove `docs/plans/` folder
- [ ] Remove any `.env` files
- [ ] Scan for hardcoded secrets (run trufflehog)
- [ ] Scan for deskcloud.app/premium references
- [ ] Rewrite README.md for public audience
- [ ] Create LICENSE file (MIT)
- [ ] Create .env.example
- [ ] Rename to `deskcloud-mcp` package structure

### 🟡 Important (Should Do)

- [ ] Create CONTRIBUTING.md
- [ ] Create CODE_OF_CONDUCT.md
- [ ] Create SECURITY.md
- [ ] Create .github/ISSUE_TEMPLATE/
- [ ] Create .github/PULL_REQUEST_TEMPLATE.md
- [ ] Create .github/workflows/ci.yml
- [ ] Create .github/workflows/publish.yml (PyPI)
- [ ] Create .github/workflows/docker.yml (Docker Hub)
- [ ] Update .gitignore
- [ ] Create pyproject.toml for PyPI
- [ ] Create docker/Dockerfile.session
- [ ] Create docker/Dockerfile.mcp

### 🟢 Nice to Have

- [ ] Create CHANGELOG.md
- [ ] Add code coverage badges
- [ ] Set up GitHub Discussions
- [ ] Create social preview image for repo
- [ ] Add PyPI/Docker badges to README
- [ ] Create social preview image
- [ ] Write SELF_HOSTING.md guide
- [ ] Add more comprehensive tests

---

## Related Plans

- [MASTER_ROADMAP.md](./MASTER_ROADMAP.md) - Project overview and context
- [nextjs_landing_dashboard.md](./nextjs_landing_dashboard.md) - Premium frontend (private repo)
- [remote_agent_client.md](./remote_agent_client.md) - Connect Agent (private repo)

---

*This document should be followed before publishing the open source version. After publishing, move this file to the private repository.*

