#!/bin/bash
#
# LIVE PAPER TRADING RUNNER — Cron-ready script for SA Quant Replica
# Auto-runs on 1st and 15th of each month
#
# Usage:
#   ./run_paper_trading.sh              # Execute rebalance
#   ./run_paper_trading.sh --dry-run    # Simulate without executing
#   ./run_paper_trading.sh --status     # Show portfolio status
#   ./run_paper_trading.sh --history    # Show trade history
#
# Crontab entry (runs at 9:30 AM UTC on 1st and 15th):
#   30 9 1,15 * * /home/quant/apps/quantclaw-data/run_paper_trading.sh >> /home/quant/apps/quantclaw-data/logs/paper_trading.log 2>&1

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="python3"
CLI="${SCRIPT_DIR}/cli.py"
LOG_DIR="${SCRIPT_DIR}/logs"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="${LOG_DIR}/paper_trading_${TIMESTAMP}.log"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Parse arguments
DRY_RUN=""
COMMAND="run"

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --status)
            COMMAND="status"
            shift
            ;;
        --history)
            COMMAND="history"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--status] [--history]"
            exit 1
            ;;
    esac
done

# Use venv if it exists, otherwise use system python3
if [[ -f "${SCRIPT_DIR}/.venv/bin/python3" ]]; then
    PYTHON="${SCRIPT_DIR}/.venv/bin/python3"
fi

# Log header
echo "========================================" | tee -a "${LOG_FILE}"
echo "LIVE PAPER TRADING — ${TIMESTAMP}" | tee -a "${LOG_FILE}"
echo "Command: paper-${COMMAND} ${DRY_RUN}" | tee -a "${LOG_FILE}"
echo "========================================" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"

# Execute command
case ${COMMAND} in
    run)
        "${PYTHON}" "${CLI}" "paper-${COMMAND}" ${DRY_RUN} 2>&1 | tee -a "${LOG_FILE}"
        EXIT_CODE=${PIPESTATUS[0]}
        ;;
    status|history)
        "${PYTHON}" "${CLI}" "paper-${COMMAND}" 2>&1 | tee -a "${LOG_FILE}"
        EXIT_CODE=${PIPESTATUS[0]}
        ;;
esac

# Log footer
echo "" | tee -a "${LOG_FILE}"
echo "========================================" | tee -a "${LOG_FILE}"
echo "Completed at: $(date +"%Y-%m-%d %H:%M:%S")" | tee -a "${LOG_FILE}"
echo "Exit code: ${EXIT_CODE}" | tee -a "${LOG_FILE}"
echo "========================================" | tee -a "${LOG_FILE}"

# Keep only last 30 log files
cd "${LOG_DIR}" && ls -t paper_trading_*.log | tail -n +31 | xargs -r rm

exit ${EXIT_CODE}
