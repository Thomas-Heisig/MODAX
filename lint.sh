#!/bin/bash
# Linting script for MODAX Python code

set -e

echo "==================================="
echo "Running code quality checks..."
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Run flake8
echo ""
echo "${YELLOW}Running flake8...${NC}"
if flake8 python-control-layer/*.py python-ai-layer/*.py --extend-ignore=C901,W504 --statistics; then
    echo "${GREEN}✓ flake8 passed${NC}"
else
    echo "${RED}✗ flake8 found issues${NC}"
    exit 1
fi

# Run pylint (informational only, don't fail on warnings)
echo ""
echo "${YELLOW}Running pylint...${NC}"
echo "Control Layer:"
pylint python-control-layer/*.py --rcfile=.pylintrc --exit-zero || true

echo ""
echo "AI Layer:"
pylint python-ai-layer/*.py --rcfile=.pylintrc --exit-zero || true

echo ""
echo "${GREEN}==================================="
echo "Code quality checks completed!"
echo "===================================${NC}"
