#!/bin/bash
# Linting script for MODAX Python code

set -e

# Parse arguments
STRICT_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --strict)
            STRICT_MODE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--strict]"
            exit 1
            ;;
    esac
done

if [ "$STRICT_MODE" = true ]; then
    echo "==================================="
    echo "Running code quality checks (STRICT MODE)..."
    echo "==================================="
else
    echo "==================================="
    echo "Running code quality checks..."
    echo "Use --strict flag for strict mode"
    echo "==================================="
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if dev dependencies are installed
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "${YELLOW}⚠ $1 not found. Install with: pip install -r python-control-layer/dev-requirements.txt${NC}"
        return 1
    fi
    return 0
}

# Check tools availability
FLAKE8_AVAILABLE=false
PYLINT_AVAILABLE=false
MYPY_AVAILABLE=false

check_tool flake8 && FLAKE8_AVAILABLE=true
check_tool pylint && PYLINT_AVAILABLE=true
check_tool mypy && MYPY_AVAILABLE=true

if [ "$FLAKE8_AVAILABLE" = false ] && [ "$PYLINT_AVAILABLE" = false ] && [ "$MYPY_AVAILABLE" = false ]; then
    echo "${RED}✗ No linting tools available. Cannot proceed.${NC}"
    exit 1
fi

# Run flake8
if [ "$FLAKE8_AVAILABLE" = true ]; then
    echo ""
    echo "${YELLOW}Running flake8...${NC}"
    if [ "$STRICT_MODE" = true ]; then
        FLAKE8_ARGS="--max-line-length=100 --extend-ignore=W504 --max-complexity=12"
    else
        FLAKE8_ARGS="--extend-ignore=C901,W504"
    fi
    
    if flake8 python-control-layer/*.py python-ai-layer/*.py $FLAKE8_ARGS --statistics; then
        echo "${GREEN}✓ flake8 passed${NC}"
    else
        echo "${RED}✗ flake8 found issues${NC}"
        if [ "$STRICT_MODE" = true ]; then
            exit 1
        fi
    fi
fi

# Run mypy
if [ "$MYPY_AVAILABLE" = true ]; then
    echo ""
    echo "${YELLOW}Running mypy...${NC}"
    if mypy python-control-layer python-ai-layer --config-file=mypy.ini; then
        echo "${GREEN}✓ mypy passed${NC}"
    else
        echo "${YELLOW}⚠ mypy found type issues${NC}"
        if [ "$STRICT_MODE" = true ]; then
            echo "${RED}✗ Type errors in strict mode${NC}"
            exit 1
        else
            echo "${BLUE}Note: Run with --strict to enforce type checking${NC}"
        fi
    fi
fi

# Run pylint
if [ "$PYLINT_AVAILABLE" = true ]; then
    echo ""
    echo "${YELLOW}Running pylint...${NC}"
    
    if [ "$STRICT_MODE" = true ]; then
        # Strict mode: fail on errors
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
    else
        # Normal mode: informational only
        echo "Control Layer:"
        pylint python-control-layer/*.py --rcfile=.pylintrc --exit-zero || true

        echo ""
        echo "AI Layer:"
        pylint python-ai-layer/*.py --rcfile=.pylintrc --exit-zero || true
    fi
fi

echo ""
if [ "$STRICT_MODE" = true ]; then
    echo "${GREEN}==================================="
    echo "All strict code quality checks passed!"
    echo "===================================${NC}"
else
    echo "${GREEN}==================================="
    echo "Code quality checks completed!"
    echo "Run with --strict for strict mode"
    echo "===================================${NC}"
fi
