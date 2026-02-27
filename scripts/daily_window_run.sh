#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

KEYWORDS_FILE="${KEYWORDS_FILE:-keywords.txt}"
MAX_TOTAL="${MAX_TOTAL:-200}"
WITHIN_HOURS="${WITHIN_HOURS:-24}"
WINDOW_RANDOM_DELAY="${WINDOW_RANDOM_DELAY:-3600}"
ANTI_MIN_SLEEP="${ANTI_MIN_SLEEP:-0.8}"
ANTI_MAX_SLEEP="${ANTI_MAX_SLEEP:-2.8}"

./run.sh \
  --keywords-file "$KEYWORDS_FILE" \
  --max-total "$MAX_TOTAL" \
  --within-hours "$WITHIN_HOURS" \
  --window-random-delay "$WINDOW_RANDOM_DELAY" \
  --anti-min-sleep "$ANTI_MIN_SLEEP" \
  --anti-max-sleep "$ANTI_MAX_SLEEP"
