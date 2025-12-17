#!/bin/bash
# Linting script for MODAX Python code - STRICT MODE

set -e

echo "==================================="
echo "Running code quality checks (STRICT MODE)..."
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if dev dependencies are installed
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "${RED}✗ $1 not found. Install with: pip install -r python-control-layer/dev-requirements.txt${NC}"
        exit 1
    fi
}

check_tool flake8
check_tool pylint
check_tool mypy

# Run flake8 - STRICT
echo ""
echo "${YELLOW}Running flake8 (strict)...${NC}"
if flake8 python-control-layer/*.py python-ai-layer/*.py \
    --max-line-length=100 \
    --extend-ignore=W504 \
    --max-complexity=12 \
    --statistics; then
    echo "${GREEN}✓ flake8 passed${NC}"
else
    echo "${RED}✗ flake8 found issues${NC}"
    exit 1
fi

# Run mypy - STRICT TYPE CHECKING
echo ""
echo "${YELLOW}Running mypy (strict type checking)...${NC}"
if mypy python-control-layer python-ai-layer --config-file=mypy.ini; then
    echo "${GREEN}✓ mypy passed (strict mode)${NC}"
else
    echo "${RED}✗ mypy found type errors${NC}"
    echo "${BLUE}Note: Fix type hints to pass strict checking${NC}"
    exit 1
fi

# Run pylint - STRICT (fail on errors)
echo ""
echo "${YELLOW}Running pylint (strict - fail on errors)...${NC}"
echo "Control Layer:"
if pylint python-control-layer/*.py --rcfile=.pylintrc --fail-on=E,F; then
    echo "${GREEN}✓ Control Layer pylint passed${NC}"
else
    echo "${RED}✗ Control Layer has pylint errors${NC}"
    exit 1
fi

echo ""
echo "AI Layer:"
if pylint python-ai-layer/*.py --rcfile=.pylintrc --fail-on=E,F; then
    echo "${GREEN}✓ AI Layer pylint passed${NC}"
else
    echo "${RED}✗ AI Layer has pylint errors${NC}"
    exit 1
fi

echo ""
echo "${GREEN}==================================="
echo "All strict code quality checks passed!"
echo "===================================${NC}"
