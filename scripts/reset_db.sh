#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
rm -f tuitionbridge.db tuitionbridge.db-wal tuitionbridge.db-shm
echo "Database removed; it is re-seeded from data/synthetic/seed.json on next start."
