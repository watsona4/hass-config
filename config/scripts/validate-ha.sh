#!/usr/bin/env bash
set -euo pipefail

# Config
HA_TAG="${HA_TAG:-}"                    # e.g. 2025.8.3; if empty, will try .HA_VERSION then fall back to "stable"
HA_DOCKER_IMAGE="${HA_DOCKER_IMAGE:-ghcr.io/home-assistant/home-assistant}"
TZ="${TZ:-America/New_York}"

# Discover version tag: prefer your pinned runtime
if [[ -z "${HA_TAG}" && -f ".HA_VERSION" ]]; then
  HA_TAG="$(tr -d ' \t\n\r' < .HA_VERSION)"
fi
HA_TAG="${HA_TAG:-stable}"

# Where to write a temporary secrets stub for check_config
SECRETS_STUB=".ci_secrets.yaml"

# Tier 1: YAML lint (optional; skip if not installed)
if command -v yamllint >/dev/null 2>&1; then
  yamllint -s .
fi

# Create a stub secrets file if you do not want to use real secrets while validating
# Scans for '!secret <key>' tokens and generates placeholders.
generate_secrets_stub() {
  # Collect keys
  # shellcheck disable=SC2016
  grep -RhoE '!secret[ ]+[A-Za-z0-9_/-]+' -- *.yaml */*.yaml 2>/dev/null \
    | awk '{print $2}' \
    | sort -u \
    | awk '{printf "%s: placeholder\n", $1}' > "${SECRETS_STUB}" || true

  # Ensure the file exists, even if empty
  : > "${SECRETS_STUB}"
}
generate_secrets_stub

# Tier 2: Home Assistant structural validation
# Run check_config inside the official container, mounting repo read-only.
# We bind a stub secrets file at /config/secrets.yaml so missing secrets do not fail validation.
docker run --rm \
  -e TZ="${TZ}" \
  -v "$PWD":/config:ro \
  -v "$PWD/${SECRETS_STUB}":/config/secrets.yaml:ro \
  "${HA_DOCKER_IMAGE}:${HA_TAG}" \
  python -m homeassistant --config /config --script check_config --info

# Tier 3 (optional): semantic assertions against a running HA (prod or staging)
# If HA_URL and HA_TOKEN are set, run custom assertions.
if [[ -n "${HA_URL:-}" && -n "${HA_TOKEN:-}" && -f "tests/state_assertions.yaml" ]]; then
  python3 scripts/ha_assert.py tests/state_assertions.yaml
fi

echo "[OK] Validation passed."
