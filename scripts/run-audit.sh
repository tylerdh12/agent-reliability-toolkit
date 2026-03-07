#!/bin/bash
#
# run-audit.sh - Complete Agent Reliability Audit Runner
#
# Runs all test suites against an agent and generates a comprehensive report.
#
# Usage:
#   ./run-audit.sh --endpoint http://localhost:8000 --output report.json
#   ./run-audit.sh -e http://localhost:8000 -o report.json
#

set -e

# Default values
ENDPOINT=""
OUTPUT="results/audit-$(date +%Y%m%d-%H%M%S).json"
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--endpoint)
            ENDPOINT="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 --endpoint <url> [--output <file>] [--verbose]"
            echo ""
            echo "Options:"
            echo "  -e, --endpoint URL    Agent API endpoint (required)"
            echo "  -o, --output FILE     Output JSON file (default: results/audit-TIMESTAMP.json)"
            echo "  -v, --verbose         Show detailed test output"
            echo "  -h, --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$ENDPOINT" ]; then
    echo -e "${RED}Error: --endpoint is required${NC}"
    echo "Use --help for usage information"
    exit 1
fi

# Create results directory
mkdir -p "$(dirname "$OUTPUT")"
mkdir -p results/temp

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Agent Reliability Audit${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "Endpoint: $ENDPOINT"
echo "Output:   $OUTPUT"
echo ""

# Export endpoint for pytest
export AGENT_ENDPOINT="$ENDPOINT"

# Run test suites
declare -a test_suites=(
    "test_hallucination"
    "test_edge_cases"
    "test_security"
    "test_context"
    "test_integration"
)

declare -A suite_descriptions=(
    ["test_hallucination"]="Hallucination Resistance"
    ["test_edge_cases"]="Edge Case Handling"
    ["test_security"]="Security & Injection"
    ["test_context"]="Context Management"
    ["test_integration"]="Tool Integration"
)

# Initialize results
echo "{" > "$OUTPUT"
echo '  "audit_timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",' >> "$OUTPUT"
echo '  "agent_endpoint": "'"$ENDPOINT"'",' >> "$OUTPUT"
echo '  "test_results": {' >> "$OUTPUT"

total_tests=0
total_passed=0
total_failed=0
suite_count=0

for suite in "${test_suites[@]}"; do
    suite_count=$((suite_count + 1))
    description="${suite_descriptions[$suite]}"
    
    echo -e "${YELLOW}Running: $description${NC}"
    
    # Run pytest for this suite
    temp_output="results/temp/${suite}.json"
    
    if [ "$VERBOSE" = true ]; then
        pytest_args="-v"
    else
        pytest_args="-q"
    fi
    
    if pytest "tests/${suite}.py" $pytest_args --json-report --json-report-file="$temp_output" 2>/dev/null; then
        echo -e "${GREEN}  ✓ Passed${NC}"
        status="passed"
    else
        echo -e "${RED}  ✗ Failed${NC}"
        status="failed"
    fi
    
    # Parse pytest JSON output
    if [ -f "$temp_output" ]; then
        # Extract test counts from pytest JSON
        tests=$(jq -r '.summary.total // 0' "$temp_output" 2>/dev/null || echo "0")
        passed=$(jq -r '.summary.passed // 0' "$temp_output" 2>/dev/null || echo "0")
        failed=$(jq -r '.summary.failed // 0' "$temp_output" 2>/dev/null || echo "0")
        
        total_tests=$((total_tests + tests))
        total_passed=$((total_passed + passed))
        total_failed=$((total_failed + failed))
    else
        tests=0
        passed=0
        failed=0
    fi
    
    # Add to output JSON
    if [ $suite_count -gt 1 ]; then
        echo "    ," >> "$OUTPUT"
    fi
    
    echo "    \"$suite\": {" >> "$OUTPUT"
    echo "      \"description\": \"$description\"," >> "$OUTPUT"
    echo "      \"status\": \"$status\"," >> "$OUTPUT"
    echo "      \"total\": $tests," >> "$OUTPUT"
    echo "      \"passed\": $passed," >> "$OUTPUT"
    echo "      \"failed\": $failed" >> "$OUTPUT"
    echo -n "    }" >> "$OUTPUT"
    
    echo ""
done

# Close test_results
echo "" >> "$OUTPUT"
echo "  }," >> "$OUTPUT"

# Calculate overall metrics
if [ $total_tests -gt 0 ]; then
    pass_rate=$(awk "BEGIN {printf \"%.1f\", ($total_passed / $total_tests) * 100}")
else
    pass_rate="0.0"
fi

# Determine grade
grade="F"
if (( $(echo "$pass_rate >= 90" | bc -l) )); then
    grade="A"
elif (( $(echo "$pass_rate >= 80" | bc -l) )); then
    grade="B"
elif (( $(echo "$pass_rate >= 70" | bc -l) )); then
    grade="C"
elif (( $(echo "$pass_rate >= 60" | bc -l) )); then
    grade="D"
fi

# Add summary
echo '  "summary": {' >> "$OUTPUT"
echo "    \"total_tests\": $total_tests," >> "$OUTPUT"
echo "    \"passed\": $total_passed," >> "$OUTPUT"
echo "    \"failed\": $total_failed," >> "$OUTPUT"
echo "    \"pass_rate\": $pass_rate," >> "$OUTPUT"
echo "    \"grade\": \"$grade\"" >> "$OUTPUT"
echo '  }' >> "$OUTPUT"
echo "}" >> "$OUTPUT"

# Print summary
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Audit Complete${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "Total Tests: $total_tests"
echo "Passed:      $total_passed"
echo "Failed:      $total_failed"
echo "Pass Rate:   ${pass_rate}%"
echo ""

# Grade with color
if [ "$grade" = "A" ]; then
    echo -e "Grade: ${GREEN}$grade${NC}"
elif [ "$grade" = "B" ] || [ "$grade" = "C" ]; then
    echo -e "Grade: ${YELLOW}$grade${NC}"
else
    echo -e "Grade: ${RED}$grade${NC}"
fi

echo ""
echo "Results saved to: $OUTPUT"
echo ""

# Run scoring script if available
if [ -f "scripts/score-agent.py" ]; then
    echo "Generating detailed report..."
    python3 scripts/score-agent.py "$OUTPUT"
fi

# Clean up temp files
rm -rf results/temp

# Exit with appropriate code
if [ "$grade" = "A" ] || [ "$grade" = "B" ]; then
    exit 0
else
    exit 1
fi
