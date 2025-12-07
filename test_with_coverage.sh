#!/bin/bash
# Test runner with coverage reporting for MODAX

set -e

echo "==================================="
echo "Running tests with coverage..."
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Run Control Layer tests with coverage
echo ""
echo "${YELLOW}Running Control Layer tests...${NC}"
cd python-control-layer
coverage run --source=. -m unittest discover -s . -p 'test_*.py' -v
coverage report -m
coverage html -d ../coverage_reports/control_layer
echo "${GREEN}✓ Control Layer coverage report generated in coverage_reports/control_layer/${NC}"
cd ..

# Run AI Layer tests with coverage
echo ""
echo "${YELLOW}Running AI Layer tests...${NC}"
cd python-ai-layer
coverage run --source=. -m unittest discover -s . -p 'test_*.py' -v
coverage report -m
coverage html -d ../coverage_reports/ai_layer
echo "${GREEN}✓ AI Layer coverage report generated in coverage_reports/ai_layer/${NC}"
cd ..

echo ""
echo "${GREEN}==================================="
echo "All tests completed successfully!"
echo "Coverage reports available in:"
echo "  - coverage_reports/control_layer/index.html"
echo "  - coverage_reports/ai_layer/index.html"
echo "===================================${NC}"
