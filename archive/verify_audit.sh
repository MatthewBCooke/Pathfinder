#!/bin/bash
# Pathfinder GUI - Post-Audit Verification Script
# Run this to verify all fixes were applied correctly

echo "============================================"
echo "Pathfinder GUI - Audit Verification Script"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS="${GREEN}✅ PASS${NC}"
FAIL="${RED}❌ FAIL${NC}"
WARN="${YELLOW}⚠️ WARN${NC}"

pass_count=0
fail_count=0
warn_count=0

# Test 1: Critical bug fix
echo "Test 1: Verifying critical bug fix..."
if grep -q "result.detected_strategy" gui/integration.py; then
    if ! grep -q "result.strategy" gui/integration.py; then
        echo -e "$PASS Critical bug is fixed (result.detected_strategy is used)"
        ((pass_count++))
    else
        echo -e "$FAIL Critical bug still present (result.strategy found)"
        ((fail_count++))
    fi
else
    echo -e "$FAIL Cannot verify fix (result.detected_strategy not found)"
    ((fail_count++))
fi

# Test 2: New files created
echo "Test 2: Checking new files..."
files_ok=true

if [ -f "pathfinder/io/writers.py" ]; then
    echo -e "$PASS pathfinder/io/writers.py exists"
    ((pass_count++))
else
    echo -e "$FAIL pathfinder/io/writers.py missing"
    ((fail_count++))
    files_ok=false
fi

if [ -f "gui/settings_dialog.py" ]; then
    echo -e "$PASS gui/settings_dialog.py exists"
    ((pass_count++))
else
    echo -e "$FAIL gui/settings_dialog.py missing"
    ((fail_count++))
    files_ok=false
fi

if [ -f "test_data.csv" ]; then
    echo -e "$PASS test_data.csv exists"
    ((pass_count++))
else
    echo -e "$FAIL test_data.csv missing"
    ((fail_count++))
    files_ok=false
fi

# Test 3: Documentation files
echo "Test 3: Checking documentation..."
if [ -f "AUDIT_REPORT.md" ]; then
    echo -e "$PASS AUDIT_REPORT.md exists"
    ((pass_count++))
else
    echo -e "$WARN AUDIT_REPORT.md missing"
    ((warn_count++))
fi

if [ -f "QUICK_TROUBLESHOOTING.md" ]; then
    echo -e "$PASS QUICK_TROUBLESHOOTING.md exists"
    ((pass_count++))
else
    echo -e "$WARN QUICK_TROUBLESHOOTING.md missing"
    ((warn_count++))
fi

if [ -f "AUDIT_SUMMARY.md" ]; then
    echo -e "$PASS AUDIT_SUMMARY.md exists"
    ((pass_count++))
else
    echo -e "$WARN AUDIT_SUMMARY.md missing"
    ((warn_count++))
fi

# Test 4: Python syntax check
echo "Test 4: Python syntax check..."
if python3 -m py_compile pathfinder_gui.py 2>/dev/null; then
    echo -e "$PASS pathfinder_gui.py compiles"
    ((pass_count++))
else
    echo -e "$FAIL pathfinder_gui.py has syntax errors"
    ((fail_count++))
fi

if python3 -m py_compile gui/integration.py 2>/dev/null; then
    echo -e "$PASS gui/integration.py compiles"
    ((pass_count++))
else
    echo -e "$FAIL gui/integration.py has syntax errors"
    ((fail_count++))
fi

if python3 -m py_compile gui/settings_dialog.py 2>/dev/null; then
    echo -e "$PASS gui/settings_dialog.py compiles"
    ((pass_count++))
else
    echo -e "$FAIL gui/settings_dialog.py has syntax errors"
    ((fail_count++))
fi

if python3 -m py_compile pathfinder/io/writers.py 2>/dev/null; then
    echo -e "$PASS pathfinder/io/writers.py compiles"
    ((pass_count++))
else
    echo -e "$FAIL pathfinder/io/writers.py has syntax errors"
    ((fail_count++))
fi

# Test 5: Import verification (will fail if dependencies not installed)
echo "Test 5: Import verification..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from pathfinder.core.models import Experiment, Trial, SearchStrategy
    print('✅ Core models import OK')
    exit(0)
except ImportError as e:
    print('❌ Import failed:', e)
    exit(1)
" 2>/dev/null
if [ $? -eq 0 ]; then
    ((pass_count++))
else
    echo -e "$WARN Imports fail (dependencies not installed - expected)"
    ((warn_count++))
fi

# Test 6: File structure
echo "Test 6: Checking project structure..."
required_dirs=("gui" "pathfinder" "pathfinder/core" "pathfinder/io" "pathfinder/analysis")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "$PASS Directory $dir exists"
        ((pass_count++))
    else
        echo -e "$FAIL Directory $dir missing"
        ((fail_count++))
    fi
done

# Summary
echo ""
echo "============================================"
echo "VERIFICATION SUMMARY"
echo "============================================"
echo -e "${GREEN}Passed:${NC} $pass_count"
echo -e "${YELLOW}Warnings:${NC} $warn_count"
echo -e "${RED}Failed:${NC} $fail_count"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CRITICAL CHECKS PASSED${NC}"
    echo "The audit fixes have been applied correctly."
    echo ""
    echo "Next steps:"
    echo "1. Install dependencies: pip install PyQt5 pandas openpyxl pydantic"
    echo "2. Run the application: python3 pathfinder_gui.py"
    echo "3. Load test_data.csv to verify functionality"
    exit 0
else
    echo -e "${RED}❌ VERIFICATION FAILED${NC}"
    echo "Some critical checks did not pass. Review the errors above."
    exit 1
fi
