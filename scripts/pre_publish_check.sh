#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== DeskCloud MCP - Pre-publish checks ==="

# 1) Disallow env files
if ls .env* >/dev/null 2>&1; then
  if [ -f ".env.example" ]; then
    # ok, but ensure no .env exists
    if [ -f ".env" ]; then
      echo "❌ FAIL: .env exists (remove before publishing)"
      exit 1
    fi
  else
    echo "❌ FAIL: Found .env* files"
    ls -1 .env* || true
    exit 1
  fi
else
  echo "✅ PASS: No .env files"
fi

# 2) Disallow docs/plans (business/internal)
if [ -d "docs/plans" ]; then
  echo "❌ FAIL: docs/plans exists (remove before publishing)"
  exit 1
fi

# 3) Disallow common local artifacts
if find . -name "__pycache__" -o -name ".DS_Store" | grep -q .; then
  echo "❌ FAIL: Found __pycache__/.DS_Store artifacts"
  find . -name "__pycache__" -o -name ".DS_Store" | head -n 50
  exit 1
fi

# 4) Basic packaging sanity
python -m pip --version >/dev/null
python -m build --version >/dev/null 2>&1 || echo "(note) python -m build not installed in this environment"

echo "✅ PASS: Pre-publish checks completed"
