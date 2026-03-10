#!/usr/bin/env bash
# =============================================================================
# run-load-tests.sh – Execute all BookStore Microservices load test scenarios
# =============================================================================
# Usage:
#   chmod +x scripts/load-testing/run-load-tests.sh
#   ./scripts/load-testing/run-load-tests.sh [OPTIONS]
#
# Options:
#   --tool locust|k6|both    Testing tool to use (default: locust)
#   --host <url>             API Gateway URL (default: http://localhost:8080)
#   --scenario normal|peak|stress|all  Which scenario(s) to run (default: all)
#   --help                   Show this help message
#
# Examples:
#   ./scripts/load-testing/run-load-tests.sh
#   ./scripts/load-testing/run-load-tests.sh --tool k6 --scenario stress
#   ./scripts/load-testing/run-load-tests.sh --host http://35.175.245.212:8080
# =============================================================================

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
TOOL="locust"
HOST="http://localhost:8080"
SCENARIO="all"
RESULTS_DIR="docs/load-testing/results"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tool)
      TOOL="$2"; shift 2;;
    --host)
      HOST="$2"; shift 2;;
    --scenario)
      SCENARIO="$2"; shift 2;;
    --help|-h)
      sed -n '/^# Usage/,/^# ===/p' "$0" | grep -v '^# ===' | sed 's/^# \?//'
      exit 0;;
    *)
      echo -e "${RED}Unknown option: $1${NC}" >&2
      exit 1;;
  esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
log()     { echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} $*"; }
success() { echo -e "${GREEN}✔${NC}  $*"; }
warn()    { echo -e "${YELLOW}⚠${NC}  $*"; }
error()   { echo -e "${RED}✘${NC}  $*" >&2; }
header()  { echo -e "\n${BOLD}${BLUE}── $* ──${NC}"; }

# ── Pre-flight checks ─────────────────────────────────────────────────────────
preflight_checks() {
  header "Pre-flight Checks"

  # Check working directory
  cd "$REPO_ROOT"
  log "Working directory: $REPO_ROOT"

  # Ensure results directory exists
  mkdir -p "$RESULTS_DIR"

  # Check API Gateway is reachable
  log "Checking API Gateway at $HOST..."
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$HOST/api/health/" || true)
  if [[ "$HTTP_STATUS" == "200" ]]; then
    success "API Gateway is healthy (HTTP 200)"
  else
    error "API Gateway returned HTTP $HTTP_STATUS (or timed out)"
    echo ""
    echo "  Start the system first:"
    echo "    docker compose up -d"
    echo "    docker compose ps"
    echo ""
    exit 1
  fi

  # Tool-specific checks
  case "$TOOL" in
    locust|both)
      if ! command -v locust &>/dev/null; then
        error "Locust not found. Install with: pip install locust"
        exit 1
      fi
      success "Locust $(locust --version 2>&1 | head -1)"
      ;;
  esac

  case "$TOOL" in
    k6|both)
      if ! command -v k6 &>/dev/null; then
        warn "K6 not found – skipping K6 tests."
        warn "Install: https://k6.io/docs/getting-started/installation/"
        [[ "$TOOL" == "k6" ]] && exit 1
        TOOL="locust"
      else
        success "K6 $(k6 version 2>&1 | head -1)"
      fi
      ;;
  esac
}

# ── Snapshot Docker stats ─────────────────────────────────────────────────────
snapshot_docker_stats() {
  local label="$1"
  local outfile="$RESULTS_DIR/docker-stats-${label}.txt"
  log "Capturing Docker stats → $outfile"
  docker stats --no-stream --format \
    "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}" \
    > "$outfile" 2>/dev/null || true
}

# ── Print circuit breaker state ───────────────────────────────────────────────
print_cb_state() {
  local label="$1"
  echo ""
  log "Circuit Breaker state ($label):"
  curl -s "$HOST/api/circuit-breakers/" | python3 -m json.tool 2>/dev/null \
    || curl -s "$HOST/api/circuit-breakers/"
  echo ""
}

# ── Locust scenarios ──────────────────────────────────────────────────────────
run_locust_normal() {
  header "Scenario: Normal Load (Locust)"
  log "50 users × 5 minutes"
  snapshot_docker_stats "before-normal"
  print_cb_state "before normal load"

  locust -f "$SCRIPT_DIR/locustfile.py" \
    --host="$HOST" \
    --users 50 \
    --spawn-rate 5 \
    --run-time 5m \
    --headless \
    --only-summary \
    --csv="$RESULTS_DIR/normal-load" \
    2>&1 | tee "$RESULTS_DIR/normal-load-locust.log"

  snapshot_docker_stats "after-normal"
  print_cb_state "after normal load"
  success "Normal load test complete → $RESULTS_DIR/normal-load_*.csv"
}

run_locust_peak() {
  header "Scenario: Peak Load (Locust)"
  log "200 users × 10 minutes"
  snapshot_docker_stats "before-peak"
  print_cb_state "before peak load"

  locust -f "$SCRIPT_DIR/locustfile.py" \
    --host="$HOST" \
    --users 200 \
    --spawn-rate 10 \
    --run-time 10m \
    --headless \
    --only-summary \
    --csv="$RESULTS_DIR/peak-load" \
    2>&1 | tee "$RESULTS_DIR/peak-load-locust.log"

  snapshot_docker_stats "after-peak"
  print_cb_state "after peak load"
  success "Peak load test complete → $RESULTS_DIR/peak-load_*.csv"
}

run_locust_stress() {
  header "Scenario: Stress Test (Locust)"
  warn "This test will drive 500 concurrent users. Expect errors – that is the point."
  log "500 users × 5 minutes (finding breaking point)"
  snapshot_docker_stats "before-stress"
  print_cb_state "before stress test"

  locust -f "$SCRIPT_DIR/locustfile.py" \
    --host="$HOST" \
    --users 500 \
    --spawn-rate 50 \
    --run-time 5m \
    --headless \
    --only-summary \
    --csv="$RESULTS_DIR/stress-test" \
    2>&1 | tee "$RESULTS_DIR/stress-test-locust.log"

  snapshot_docker_stats "after-stress"
  print_cb_state "after stress test"
  success "Stress test complete → $RESULTS_DIR/stress-test_*.csv"
}

# ── K6 scenarios ──────────────────────────────────────────────────────────────
run_k6_normal() {
  header "Scenario: Normal Load (K6)"
  log "50 VUs × 5 minutes"
  snapshot_docker_stats "k6-before-normal"

  BASE_URL="$HOST" k6 run \
    --env SCENARIO=normalLoad \
    --summary-trend-stats "avg,min,med,max,p(90),p(95),p(99)" \
    --out json="$RESULTS_DIR/k6-normal-load.json" \
    "$SCRIPT_DIR/k6-load-test.js" \
    2>&1 | tee "$RESULTS_DIR/k6-normal-load.log"

  snapshot_docker_stats "k6-after-normal"
  success "K6 normal load test complete"
}

run_k6_peak() {
  header "Scenario: Peak Load (K6)"
  log "200 VUs × 10 minutes"

  BASE_URL="$HOST" k6 run \
    --env SCENARIO=peakLoad \
    --summary-trend-stats "avg,min,med,max,p(90),p(95),p(99)" \
    --out json="$RESULTS_DIR/k6-peak-load.json" \
    "$SCRIPT_DIR/k6-load-test.js" \
    2>&1 | tee "$RESULTS_DIR/k6-peak-load.log"

  success "K6 peak load test complete"
}

run_k6_stress() {
  header "Scenario: Stress Test (K6)"
  warn "Ramping to 500 VUs – expect significant errors."

  BASE_URL="$HOST" k6 run \
    --env SCENARIO=stressTest \
    --summary-trend-stats "avg,min,med,max,p(90),p(95),p(99)" \
    --out json="$RESULTS_DIR/k6-stress-test.json" \
    "$SCRIPT_DIR/k6-load-test.js" \
    2>&1 | tee "$RESULTS_DIR/k6-stress-test.log"

  success "K6 stress test complete"
}

# ── Circuit Breaker demo ──────────────────────────────────────────────────────
run_circuit_breaker_demo() {
  header "Circuit Breaker Demo"
  CB_SCRIPT="$REPO_ROOT/scripts/demo-circuit-breaker.sh"
  if [[ -x "$CB_SCRIPT" ]]; then
    log "Running circuit breaker demo (non-interactive)..."
    # Run with a pipe to avoid interactive prompts (sends Enter automatically)
    yes "" | "$CB_SCRIPT" 2>&1 | tee "$RESULTS_DIR/circuit-breaker-demo.log" || true
    success "Circuit breaker demo complete → $RESULTS_DIR/circuit-breaker-demo.log"
  else
    warn "scripts/demo-circuit-breaker.sh not found or not executable – skipping."
  fi
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  echo ""
  echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${BLUE}║  BookStore Microservices – Load Test Runner  ║${NC}"
  echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════╝${NC}"
  echo ""
  log "Tool:     $TOOL"
  log "Host:     $HOST"
  log "Scenario: $SCENARIO"
  log "Results:  $RESULTS_DIR/"

  preflight_checks

  START_TIME=$(date +%s)

  case "$TOOL" in
    locust)
      case "$SCENARIO" in
        normal)  run_locust_normal ;;
        peak)    run_locust_peak ;;
        stress)  run_locust_stress ;;
        all)
          run_locust_normal
          log "Cooling down 30 seconds before next scenario..."
          sleep 30
          run_locust_peak
          log "Cooling down 30 seconds before next scenario..."
          sleep 30
          run_locust_stress
          ;;
        *)
          error "Unknown scenario: $SCENARIO (valid: normal|peak|stress|all)"
          exit 1;;
      esac
      ;;
    k6)
      case "$SCENARIO" in
        normal)  run_k6_normal ;;
        peak)    run_k6_peak ;;
        stress)  run_k6_stress ;;
        all)
          run_k6_normal
          sleep 30
          run_k6_peak
          sleep 30
          run_k6_stress
          ;;
        *)
          error "Unknown scenario: $SCENARIO (valid: normal|peak|stress|all)"
          exit 1;;
      esac
      ;;
    both)
      run_locust_normal; sleep 30
      run_k6_normal; sleep 30
      run_locust_peak; sleep 30
      run_k6_peak; sleep 30
      run_locust_stress; sleep 30
      run_k6_stress
      ;;
  esac

  # Always run CB demo at the end (unless stress-only)
  if [[ "$SCENARIO" == "all" ]]; then
    log "Cooling down 60 seconds before Circuit Breaker demo..."
    sleep 60
    run_circuit_breaker_demo
  fi

  END_TIME=$(date +%s)
  ELAPSED=$(( END_TIME - START_TIME ))

  echo ""
  echo -e "${BOLD}${GREEN}╔══════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${GREEN}║  All tests completed successfully!   ║${NC}"
  echo -e "${BOLD}${GREEN}╚══════════════════════════════════════╝${NC}"
  echo ""
  log "Total elapsed time: ${ELAPSED}s ($(( ELAPSED / 60 ))m $(( ELAPSED % 60 ))s)"
  log "Results saved to:   $RESULTS_DIR/"
  echo ""
  echo "  CSV reports:  ls $RESULTS_DIR/*.csv"
  echo "  JSON reports: ls $RESULTS_DIR/*.json"
  echo "  Logs:         ls $RESULTS_DIR/*.log"
}

main "$@"
