#!/usr/bin/env bash
# Phase A end-to-end smoke test.
# Usage: scripts/smoke_test.sh [URL]
set -euo pipefail

cd "$(dirname "$0")/.."

URL="${1:-https://karpathy.ai/}"

echo "=== 1. one-shot distill (no queue) ==="
python3 -m wikillm distill-url "$URL"

echo
echo "=== 2. queue + drain ==="
python3 -m wikillm enqueue "$URL"
python3 -m wikillm process --once
python3 -m wikillm stats

echo
echo "=== 3. notes produced ==="
ls -lR notes/ | head -40
