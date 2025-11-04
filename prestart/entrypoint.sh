#!/bin/sh
set -eu

CONFIG_PATH="${PRESTART_CONFIG:-/config/prestart_tasks.yaml}"
RUNNER="${PRESTART_RUNNER:-/prestart/run_prestart_tasks.py}"
ROOT_DIR="${PRESTART_ROOT:-/config}"

if [ -f "$CONFIG_PATH" ]; then
    echo "[prestart] loading tasks from ${CONFIG_PATH}"
    python3 "$RUNNER" --config "$CONFIG_PATH" --root "$ROOT_DIR"
else
    echo "[prestart] configuration ${CONFIG_PATH} not found; skipping pre-start tasks"
fi

exec /init "$@"
