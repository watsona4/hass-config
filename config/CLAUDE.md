# Home Assistant Configuration — Project Instructions

## Style Guides

When writing or editing YAML or Jinja2 templates in this project, **always**
follow the rules in these files:

- `yaml-style-guide.md` — formatting, indentation, quoting, block scalars,
  sequences, comments, and package file structure.
- `jinja2-style-guide.md` — state access, type conversions, variables,
  boolean expressions, availability templates, macros, and `now()` usage.

Read both files before making any changes. If existing code violates the
guides, fix violations in any code you touch but don't refactor files you
weren't asked to change.

## Key Rules (Quick Reference)

**YAML:**
- 2-space indent, block style only (no `[flow]` or `{flow}` ever)
- Booleans: lowercase `true`/`false` only
- Double-quote entity IDs, states, names
- Prefer `>-` for templates (strips trailing newline)
- No default values in config

**Jinja2:**
- Never `states.entity.state` — use `states()`, `is_state()`, `state_attr()`
- Always `| float(0)` or `| float(none)` — never bare `| float`
- Space around pipe: `| float` not `|float`
- `{% set %}` variables at top, only what's needed
- `has_value()` for all availability checks
- Python-style `and`/`or`/`not`

## File Structure

Package files live in `packages/`. Each package is self-contained with a
header comment listing purpose and dependencies. Integration sections are
ordered: `homeassistant:` → `input_*:` → `template:` → `automation:` →
`script:`.

## Recurring Task: Sunny Sensor Calibration (1st & 15th of each month)

An automation (`packages/sunny_calibration.yaml`) reminds the owner on the 1st
and 15th to report recent clearly-sunny / clearly-cloudy days, so the owner
may open a session with something like "this is my report for the 1st" or
just describe recent weather unprompted. **When that happens, follow
`docs/sunny-sensor-calibration.md` — read it in full before doing anything.**
It has the model, the exact SQL/pandas extraction procedure, every gotcha
found so far (including one about entity renames breaking raw-state history —
easy to miss), and a running calibration log to read for context. Don't
improvise a different approach; the doc exists specifically so this doesn't
need to be re-derived each time. Reference data lives in
`docs/sunny-sensor-labels.csv` and `docs/sunny-sensor-references.csv`
(append-only, durable against the 30-day recorder purge). After a calibration
session, update all three: the calibration doc's log, the memory entry
`[[sunny-sensor-tree-obstruction]]`, and the two CSVs.

---

## Entity Migration: YAML → GUI

This project is migrating entities from YAML packages to Home Assistant's
GUI-managed entities. GUI entities get immediate reload, remote editing via
Nabu Casa, and device linking.

### What MUST Stay in YAML (GUI Lacks Support)

- `binary_sensor` with `delay_off` or `delay_on`
- Trigger-based templates
- Templates needing `attribute_templates`

Everything else should be created via the GUI using the APIs below.

### Migration Workflow

When asked to migrate a package:

1. **Read the package YAML** file in `packages/`
2. **Identify** which entities can migrate (most) vs must stay (delay_off,
   triggers, attribute_templates)
3. **Create input helpers** via WebSocket API
4. **Create template entities** via HTTP config flow API
5. **Assign devices** — each template entity should be attached to the
   device it queries or references. Use the device registry to find IDs.
6. **Report** what was created and what must remain in YAML
7. **Always confirm** the plan with the user before making API calls

### Already Migrated

- **Blinds package** (`packages/blinds.yaml` or similar):
  - 21 `input_select` helpers (closed reason dropdowns) — DONE
  - 28 template `binary_sensor` entities — DONE
  - Presence sensors with `delay_off` remain in YAML

---

## Home Assistant API Reference

The HA instance is local. Base URL: `http://localhost:8123`

Authentication: Long-lived access token as Bearer token.
```
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

The token should be in the environment variable `HA_TOKEN`. Never hardcode it.

### Input Helpers — WebSocket API

Input helpers (input_select, input_boolean, input_number, input_text) are
created via WebSocket. Use Python `websockets` library.

**Connection flow:**
```
1. Connect to ws://localhost:8123/api/websocket
2. Receive: {"type": "auth_required"}
3. Send:    {"type": "auth", "access_token": "<TOKEN>"}
4. Receive: {"type": "auth_ok"}
5. Send commands with incrementing "id" field
```

**Create input_select:**
```json
{"id": 1, "type": "input_select/create", "name": "My Select", "options": ["A", "B", "C"], "icon": "mdi:blinds"}
```

**Create input_boolean:**
```json
{"id": 2, "type": "input_boolean/create", "name": "My Toggle", "icon": "mdi:toggle-switch"}
```

**Create input_number:**
```json
{"id": 3, "type": "input_number/create", "name": "My Number", "min": 0, "max": 100, "step": 1, "mode": "slider", "unit_of_measurement": "°F"}
```

**Create input_text:**
```json
{"id": 4, "type": "input_text/create", "name": "My Text"}
```

**Response:** `{"id": N, "type": "result", "success": true, "result": {...}}`
On error: `{"id": N, "type": "result", "success": false, "error": {"code": "...", "message": "..."}}`

### Template Entities — HTTP Config Flow API

Template sensors, binary sensors, etc. are created via HTTP POST config
entry flows. This is NOT in the official API docs — it was reverse-engineered
from browser DevTools.

**3-step flow:**

**Step 1: Start flow**
```bash
curl -s -X POST http://localhost:8123/api/config/config_entries/flow \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"handler": "template", "show_advanced_options": true}'
```
Response: `{"type": "menu", "flow_id": "<FLOW_ID>", ...}`

**Step 2: Select entity type**
```bash
curl -s -X POST http://localhost:8123/api/config/config_entries/flow/<FLOW_ID> \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"next_step_id": "binary_sensor"}'
```
Valid `next_step_id` values: `binary_sensor`, `sensor`, `switch`, `number`,
`select`, `button`, `cover`, `fan`, `light`, `lock`, `alarm_control_panel`,
`event`, `image`, `update`, `vacuum`, `weather`

Response: `{"type": "form", "flow_id": "<FLOW_ID>", ...}`

**Step 3: Submit entity config**
```json
{
  "name": "My Sensor Name",
  "state": "{{ is_state('sensor.something', 'on') }}",
  "device_id": "abc123def456...",
  "advanced_options": {
    "availability": "{{ has_value('sensor.something') }}"
  }
}
```

Response on success: `{"type": "create_entry", "title": "My Sensor Name", ...}`
Response on error: `{"type": "form", "errors": {...}, ...}`

**Fields by entity type:**

| Field | binary_sensor | sensor | Where |
|---|---|---|---|
| `name` | required | required | top-level |
| `state` | required | required | top-level |
| `device_id` | optional | optional | top-level |
| `device_class` | optional | optional | top-level |
| `availability` | optional | optional | `advanced_options` |
| `unit_of_measurement` | — | optional | `advanced_options` |
| `state_class` | — | optional | `advanced_options` |

### Device Registry

The device registry is in the HA config directory at
`.storage/core.device_registry`. It's JSON:

```python
import json
with open('.storage/core.device_registry') as f:
    reg = json.load(f)
devices = reg['data']['devices']
# Each device has: id, name, name_by_user, ...
```

**Device assignment rule:** Each template entity should be attached to the
HA device it primarily queries or references. For example:
- A brightness sensor for "Kitchen Left Window" → Kitchen Left Window device
- A button state sensor using `timer.breakfast_room_timer` → Breakfast Room Window Button device
- A "Closed TV" sensor checking `media_player.un50j5500` → Living Room TV device
- Group/aggregate sensors → no device (omit device_id)

### Entity Registry

To look up existing entities:
```bash
curl -s http://localhost:8123/api/states \
  -H "Authorization: Bearer $HA_TOKEN" | python3 -m json.tool
```

Or read `.storage/core.entity_registry` directly.

---

## Python Reference Implementation

For bulk operations, use Python with `requests` and `websockets`:

```python
#!/usr/bin/env python3
"""Helper for HA entity migration."""

import asyncio
import json
import os
import time

import requests
import websockets

HA_URL = "http://localhost:8123"
TOKEN = os.environ["HA_TOKEN"]
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def create_template_entity(entity_type: str, name: str, state: str,
                           availability: str = None, device_id: str = None,
                           device_class: str = None,
                           unit_of_measurement: str = None,
                           state_class: str = None) -> dict:
    """Create a template entity via the 3-step config flow."""

    # Step 1: Start flow
    resp = requests.post(
        f"{HA_URL}/api/config/config_entries/flow",
        headers=HEADERS,
        json={"handler": "template", "show_advanced_options": True},
    )
    resp.raise_for_status()
    flow_id = resp.json()["flow_id"]

    # Step 2: Select type
    resp = requests.post(
        f"{HA_URL}/api/config/config_entries/flow/{flow_id}",
        headers=HEADERS,
        json={"next_step_id": entity_type},
    )
    resp.raise_for_status()
    flow_id = resp.json()["flow_id"]

    # Step 3: Submit
    form = {"name": name, "state": state.strip()}
    if device_id:
        form["device_id"] = device_id
    if device_class:
        form["device_class"] = device_class

    advanced = {}
    if availability:
        advanced["availability"] = availability.strip()
    if unit_of_measurement:
        advanced["unit_of_measurement"] = unit_of_measurement
    if state_class:
        advanced["state_class"] = state_class
    if advanced:
        form["advanced_options"] = advanced

    resp = requests.post(
        f"{HA_URL}/api/config/config_entries/flow/{flow_id}",
        headers=HEADERS,
        json=form,
    )
    resp.raise_for_status()
    result = resp.json()

    if result.get("type") != "create_entry":
        raise RuntimeError(f"Failed to create {name}: {result}")
    return result


async def create_input_helper(helper_type: str, **kwargs) -> dict:
    """Create an input helper via WebSocket."""
    uri = HA_URL.replace("http", "ws") + "/api/websocket"

    async with websockets.connect(uri) as ws:
        # Auth
        await ws.recv()  # auth_required
        await ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
        auth = json.loads(await ws.recv())
        if auth["type"] != "auth_ok":
            raise RuntimeError(f"Auth failed: {auth}")

        # Send command
        cmd = {"id": 1, "type": f"{helper_type}/create", **kwargs}
        await ws.send(json.dumps(cmd))

        # Read until we get our response
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                if not msg.get("success"):
                    raise RuntimeError(f"Failed: {msg['error']['message']}")
                return msg["result"]
```

Install dependencies: `pip install requests websockets pyyaml`

---

## Workflow Tips

- **Always dry-run first** — print what would be created before making calls
- **Throttle** — add 200-300ms delay between API calls
- **Check for duplicates** — query existing entities before creating
- **Jinja templates in JSON** — single quotes inside templates don't need
  escaping in JSON strings. The templates use Jinja `'single quotes'` which
  are fine inside JSON `"double quotes"`.
- **Error recovery** — if step 1 or 2 succeeds but step 3 fails, the flow
  is abandoned automatically (HA cleans up stale flows)

## Reading Package YAML for Migration

When parsing a package YAML file to extract entities for migration:

- **input_select / input_boolean / input_number / input_text** — extract
  directly from the `input_select:`, `input_boolean:`, etc. top-level keys.
  The YAML key is the entity slug; the `name:` field is the friendly name.

- **template binary_sensor / sensor** — found under `template:` →
  `binary_sensor:` or `sensor:`. Each has `name`, `state`, and optionally
  `availability`, `device_class`, `unique_id`, `delay_on`, `delay_off`,
  `attribute_templates`, etc.

- **Skip entities** with `delay_on`, `delay_off`, `attribute_templates`, or
  that are under a `triggers:` block — these must stay in YAML.

- **Shared variables** — packages often define variables at the top of a
  Jinja block and reuse them across sensors. When migrating, each GUI sensor
  must be self-contained — inline only the `{% set %}` variables that
  specific sensor actually uses. Don't copy the entire shared block.
