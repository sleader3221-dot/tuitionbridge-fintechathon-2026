#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. .venv/bin/activate
mkdir -p evidence/test_results
python -m pytest -v 2>&1 | tee evidence/test_results/pytest_verbose.txt
python -m pytest -q 2>&1 | tail -n 3 | tee evidence/test_results/pytest_summary.txt
