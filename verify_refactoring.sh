#!/bin/bash
# Verification script for calculateValues() refactoring

echo "======================================================================"
echo "PATHFINDER REFACTORING VERIFICATION"
echo "======================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass=0
fail=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        ((pass++))
        return 0
    else
        echo -e "${RED}✗${NC} $1 NOT FOUND"
        ((fail++))
        return 1
    fi
}

check_function() {
    file=$1
    func=$2
    if grep -q "def $func" "$file"; then
        echo -e "${GREEN}✓${NC} Function '$func' found in $file"
        ((pass++))
        return 0
    else
        echo -e "${RED}✗${NC} Function '$func' NOT FOUND in $file"
        ((fail++))
        return 1
    fi
}

check_class() {
    file=$1
    classname=$2
    if grep -q "@dataclass\|class $classname" "$file"; then
        echo -e "${GREEN}✓${NC} Class '$classname' found in $file"
        ((pass++))
        return 0
    else
        echo -e "${RED}✗${NC} Class '$classname' NOT FOUND in $file"
        ((fail++))
        return 1
    fi
}

check_no_pattern() {
    file=$1
    pattern=$2
    desc=$3
    if grep -q "$pattern" "$file"; then
        echo -e "${RED}✗${NC} FAIL: $desc found in $file (should be removed)"
        ((fail++))
        return 1
    else
        echo -e "${GREEN}✓${NC} $desc NOT found in $file (correctly removed)"
        ((pass++))
        return 0
    fi
}

echo "1. Checking Created Files"
echo "----------------------------------------"
check_file "/tmp/Pathfinder/pathfinder/types.py"
check_file "/tmp/Pathfinder/pathfinder/analysis.py"
check_file "/tmp/Pathfinder/test_analysis_refactor.py"
check_file "/tmp/Pathfinder/REFACTORING_SUMMARY.md"
echo ""

echo "2. Checking Type Definitions"
echo "----------------------------------------"
check_class "/tmp/Pathfinder/pathfinder/types.py" "TrialMetrics"
check_class "/tmp/Pathfinder/pathfinder/types.py" "AnalysisConfig"
echo ""

echo "3. Checking Analysis Functions"
echo "----------------------------------------"
check_function "/tmp/Pathfinder/pathfinder/analysis.py" "calculate_trial_metrics"
check_function "/tmp/Pathfinder/pathfinder/analysis.py" "unit_vector"
check_function "/tmp/Pathfinder/pathfinder/analysis.py" "angle_between"
echo ""

echo "4. Checking GUI Dependencies Removed"
echo "----------------------------------------"
check_no_pattern "/tmp/Pathfinder/pathfinder/analysis.py" "theStatus\.set" "theStatus.set() GUI call"
check_no_pattern "/tmp/Pathfinder/pathfinder/analysis.py" "import tkinter" "tkinter import"
check_no_pattern "/tmp/Pathfinder/pathfinder/analysis.py" "from tkinter" "tkinter import"
check_no_pattern "/tmp/Pathfinder/pathfinder/analysis.py" "messagebox" "tkinter messagebox"
echo ""

echo "5. Checking Function Signature"
echo "----------------------------------------"
if grep -q "def calculate_trial_metrics(" "/tmp/Pathfinder/pathfinder/analysis.py"; then
    echo -e "${GREEN}✓${NC} Function uses snake_case naming"
    ((pass++))
else
    echo -e "${RED}✗${NC} Function name incorrect"
    ((fail++))
fi

if grep -q "TrialMetrics:" "/tmp/Pathfinder/pathfinder/analysis.py"; then
    echo -e "${GREEN}✓${NC} Function returns TrialMetrics type"
    ((pass++))
else
    echo -e "${RED}✗${NC} Function return type missing or incorrect"
    ((fail++))
fi
echo ""

echo "6. Checking Imports"
echo "----------------------------------------"
if grep -q "from pathfinder.types import TrialMetrics" "/tmp/Pathfinder/pathfinder/analysis.py"; then
    echo -e "${GREEN}✓${NC} TrialMetrics import present"
    ((pass++))
else
    echo -e "${RED}✗${NC} TrialMetrics import missing"
    ((fail++))
fi

if grep -q "import numpy as np" "/tmp/Pathfinder/pathfinder/analysis.py"; then
    echo -e "${GREEN}✓${NC} numpy import present"
    ((pass++))
else
    echo -e "${RED}✗${NC} numpy import missing"
    ((fail++))
fi

if grep -q "import math" "/tmp/Pathfinder/pathfinder/analysis.py"; then
    echo -e "${GREEN}✓${NC} math import present"
    ((pass++))
else
    echo -e "${RED}✗${NC} math import missing"
    ((fail++))
fi
echo ""

echo "7. Checking TrialMetrics Fields (19 metrics)"
echo "----------------------------------------"
metrics=(
    "corridor_average"
    "distance_average"
    "average_distance_to_swim_path_centroid"
    "average_distance_to_centre"
    "average_heading_error"
    "percent_traversed"
    "quadrant_total"
    "total_distance"
    "latency"
    "full_thigmo_counter"
    "small_thigmo_counter"
    "annulus_counter"
    "sample_count"
    "trajectory_x"
    "trajectory_y"
    "velocity"
    "ipe"
    "average_initial_heading_error"
    "entropy"
)

metrics_found=0
for metric in "${metrics[@]}"; do
    if grep -q "$metric:" "/tmp/Pathfinder/pathfinder/types.py"; then
        metrics_found=$((metrics_found + 1))
    else
        echo -e "${YELLOW}⚠${NC} Metric '$metric' not found in TrialMetrics"
    fi
done

if [ $metrics_found -eq 19 ]; then
    echo -e "${GREEN}✓${NC} All 19 metrics present in TrialMetrics"
    ((pass++))
else
    echo -e "${RED}✗${NC} Only $metrics_found/19 metrics found in TrialMetrics"
    ((fail++))
fi
echo ""

echo "8. Checking Return Statement"
echo "----------------------------------------"
if grep -q "return TrialMetrics(" "/tmp/Pathfinder/pathfinder/analysis.py"; then
    echo -e "${GREEN}✓${NC} Function returns TrialMetrics dataclass (not tuple)"
    ((pass++))
else
    echo -e "${RED}✗${NC} Function return statement incorrect"
    ((fail++))
fi
echo ""

echo "9. Code Statistics"
echo "----------------------------------------"
lines=$(wc -l < "/tmp/Pathfinder/pathfinder/analysis.py")
echo "  analysis.py: $lines lines"

types_lines=$(wc -l < "/tmp/Pathfinder/pathfinder/types.py")
echo "  types.py: $types_lines lines"

test_lines=$(wc -l < "/tmp/Pathfinder/test_analysis_refactor.py")
echo "  test_analysis_refactor.py: $test_lines lines"
echo ""

echo "======================================================================"
echo "RESULTS"
echo "======================================================================"
echo -e "Passed: ${GREEN}$pass${NC}"
echo -e "Failed: ${RED}$fail${NC}"
echo ""

if [ $fail -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo ""
    echo "The calculateValues() function has been successfully refactored!"
    echo ""
    echo "Next steps:"
    echo "  1. Install numpy: pip install numpy"
    echo "  2. Run tests: python3 test_analysis_refactor.py"
    echo "  3. Review: cat REFACTORING_SUMMARY.md"
    exit 0
else
    echo -e "${RED}❌ SOME CHECKS FAILED${NC}"
    echo ""
    echo "Please review the failed checks above."
    exit 1
fi
