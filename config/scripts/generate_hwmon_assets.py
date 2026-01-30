#!/usr/bin/env python3
"""
Generate Home Assistant packages and dashboard views from machine telemetry configs.

Reads machine configuration YAML files from hwmon_machines/ and generates:
  - packages/hwmon/<machine>.yaml - Trigger-based sensors and ui_* sensors
  - dashboards/computers/views/<NN>_<machine>.yaml - Machine dashboard view

The telemetry sensor (created by telemetry-tap via MQTT discovery) stores the
full JSON payload as attributes. This generator creates sensors that extract
values from those nested JSON attributes.

Usage:
    python3 scripts/generate_hwmon_assets.py --machines frigate laptop desktop
    python3 scripts/generate_hwmon_assets.py --all
"""

import argparse
import uuid
from pathlib import Path
from typing import Any

import yaml

# Deterministic UUID namespace for this generator
UUID_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def generate_uuid(seed: str) -> str:
    """Generate a deterministic UUID for sensor unique_id.

    Uses uuid5 with a fixed namespace and the provided seed string to ensure
    the same UUID is generated for the same sensor across runs.

    Args:
        seed: A unique identifier string for this sensor (e.g., "frigate_cpu_temp")

    Returns:
        A deterministic UUID string
    """
    return str(uuid.uuid5(UUID_NAMESPACE, seed))


def slugify(name: str) -> str:
    """Convert a name to a valid Home Assistant entity slug."""
    import re
    # Replace common separators with underscores
    slug = name.lower().replace(" ", "_").replace("-", "_").replace("@", "_").replace(".", "_")
    # Remove any characters that aren't alphanumeric or underscore
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    # Collapse multiple underscores
    slug = re.sub(r"_+", "_", slug)
    # Strip leading/trailing underscores
    return slug.strip("_")


def _build_partitions_display_template(status_sensor: str, partitions_config: dict) -> str:
    """Build the Jinja2 template for partitions_display extra_attr.

    Incorporates custom display names from the partitions config section.

    Args:
        status_sensor: The drive status sensor entity ID
        partitions_config: The partitions section from machine config

    Returns:
        A Jinja2 template string that outputs JSON array of partition display data
    """
    # Build display name mapping from config
    includes = partitions_config.get("include", [])
    display_names = {}
    for p in includes:
        name = p.get("name", "")
        display = p.get("display_name", "")
        if name and display:
            display_names[name] = display

    # Build the Jinja2 dict literal for display_names
    if display_names:
        display_names_str = ", ".join(
            f"'{k}': '{v}'" for k, v in display_names.items()
        )
        display_names_decl = "{%- set display_names = {" + display_names_str + "} -%}"
    else:
        display_names_decl = "{%- set display_names = {} -%}"

    return (
        "{%- from 'units/base.jinja' import u_humanize_value -%}"
        "{%- set partitions = state_attr('" + status_sensor + "', 'partitions') | default([], true) -%}"
        + display_names_decl +
        "{%- set guid_names = {"
        "'c12a7328-f81f-11d2-ba4b-00a0c93ec93b': 'EFI', "
        "'e3c9e316-0b5c-4db8-817d-f92df00215ae': 'Reserved', "
        "'ebd0a0a2-b9e5-4433-87c0-68b6b72699c7': 'Data', "
        "'de94bba4-06d1-4d40-a16a-bfd50179d6ac': 'Recovery'"
        "} -%}"
        "{%- set type_icons = {"
        "'EFI': 'mdi:chip', "
        "'Reserved': 'mdi:lock', "
        "'Data': 'mdi:harddisk', "
        "'Recovery': 'mdi:backup-restore'"
        "} -%}"
        "{%- set type_colors = {"
        "'EFI': 'orange', "
        "'Reserved': 'purple', "
        "'Data': 'blue', "
        "'Recovery': 'teal'"
        "} -%}"
        "{%- set ns = namespace(result=[]) -%}"
        "{%- for p in partitions -%}"
        "{%- set raw_name = p.name | default('') -%}"
        "{%- set custom_name = display_names.get(raw_name, '') -%}"
        "{%- set is_generic = raw_name.startswith('Disk ') or raw_name == '' -%}"
        "{%- set guid_clean = (p.type_guid | default('')) | replace('{', '') | replace('}', '') | lower -%}"
        "{%- set type_name = guid_names.get(guid_clean, p.type | default('Unknown')) -%}"
        "{%- set label = custom_name or p.label | default(type_name if is_generic else raw_name) -%}"
        "{%- set size = u_humanize_value(p.size_b | default(0), 'B') -%}"
        "{%- set offset = u_humanize_value(p.start_offset_b | default(0), 'B') -%}"
        "{%- set vol_guid = (p.volume_guid | default('')) | replace('{', '') | replace('}', '') -%}"
        "{%- set drive_letter = p.drive_letter | default('') -%}"
        "{%- set is_hidden = p.is_hidden | default(false) -%}"
        "{%- set is_boot = p.is_boot | default(false) -%}"
        "{%- set is_system = p.is_system | default(false) -%}"
        "{%- set icon = 'mdi:eye-off' if is_hidden else type_icons.get(type_name, 'mdi:harddisk') -%}"
        "{%- set icon_color = 'grey' if is_hidden else type_colors.get(type_name, 'grey') -%}"
        "{%- set primary = label ~ (' (' ~ drive_letter ~ ':)' if drive_letter else '') -%}"
        "{%- set flags = [] -%}"
        "{%- if is_boot -%}{%- set flags = flags + ['Boot'] -%}{%- endif -%}"
        "{%- if is_system -%}{%- set flags = flags + ['System'] -%}{%- endif -%}"
        "{%- if is_hidden -%}{%- set flags = flags + ['Hidden'] -%}{%- endif -%}"
        "{%- set line1 = type_name ~ ' | ' ~ size ~ ' @ ' ~ offset -%}"
        "{%- set line2 = flags | join(', ') if flags else '' -%}"
        "{%- set line3 = vol_guid[:36] if vol_guid else '' -%}"
        "{%- set lines = [line1] -%}"
        "{%- if line2 -%}{%- set lines = lines + [line2] -%}{%- endif -%}"
        "{%- if line3 -%}{%- set lines = lines + [line3] -%}{%- endif -%}"
        "{%- set secondary = lines | join('\\n') -%}"
        "{%- set entry = {"
        "'primary': primary, "
        "'secondary': secondary, "
        "'icon': icon, "
        "'icon_color': icon_color, "
        "'type_name': type_name, "
        "'size': size, "
        "'offset': offset, "
        "'volume_guid': vol_guid, "
        "'drive_letter': drive_letter, "
        "'is_boot': is_boot, "
        "'is_system': is_system, "
        "'is_hidden': is_hidden"
        "} -%}"
        "{%- set ns.result = ns.result + [entry] -%}"
        "{%- endfor -%}"
        "{{- ns.result | tojson -}}"
    )


def load_machine_config(config_path: Path) -> dict:
    """Load a machine configuration YAML file.

    Automatically adds 'entity_prefix' to the machine dict, derived from
    the machine name using slugify(). This ensures entity references
    (sensor.{entity_prefix}_*) match the entity IDs that Home Assistant
    creates from sensor names ({name} ...).
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    # Add entity_prefix derived from name for consistent entity references
    if "machine" in config:
        name = config["machine"].get("name", "")
        config["machine"]["entity_prefix"] = slugify(name)
    return config


def generate_package_header(machine: dict) -> str:
    """Generate the package YAML header."""
    name = machine["name"]
    return f"""# =============================================================================
# Package: {name} Hardware Monitor
# =============================================================================
#
# Auto-generated by generate_hwmon_assets.py
# DO NOT EDIT - Changes will be overwritten
#
# Monitors {name} system telemetry via MQTT and provides:
#   - Data sensors for CPU, memory, disk, network, etc.
#   - UI sensors for dashboard card attributes
#   - Binary sensors for health status
#
# Source telemetry sensor: {machine['telemetry_sensor']}
#
# =============================================================================

"""


def write_anchor_container(f):
    """Start the template section - no anchors used anymore."""
    f.write("template:\n")


def write_sensor(f, sensor: dict, indent: int = 6):
    """Write a sensor definition to file."""
    spaces = " " * indent
    f.write(f'{spaces}- name: "{sensor["name"]}"\n')
    f.write(f'{spaces}  unique_id: {sensor["unique_id"]}\n')
    if "availability" in sensor:
        f.write(f'{spaces}  availability: "{sensor["availability"]}"\n')

    # State might be multi-line
    state = sensor["state"]
    if "\n" in state or len(state) > 60:
        f.write(f"{spaces}  state: >-\n")
        for line in state.split("\n"):
            f.write(f"{spaces}    {line.strip()}\n")
    else:
        f.write(f'{spaces}  state: "{state}"\n')

    if "icon" in sensor:
        f.write(f'{spaces}  icon: "{sensor["icon"]}"\n')
    if "unit_of_measurement" in sensor:
        f.write(f'{spaces}  unit_of_measurement: "{sensor["unit_of_measurement"]}"\n')
    if "state_class" in sensor:
        f.write(f'{spaces}  state_class: {sensor["state_class"]}\n')
    if "device_class" in sensor:
        f.write(f'{spaces}  device_class: {sensor["device_class"]}\n')
    if "attributes" in sensor:
        f.write(f"{spaces}  attributes:\n")
        for attr_name, attr_val in sensor["attributes"].items():
            if "\n" in str(attr_val):
                f.write(f"{spaces}    {attr_name}: >-\n")
                for line in str(attr_val).split("\n"):
                    f.write(f"{spaces}      {line.strip()}\n")
            else:
                f.write(f'{spaces}    {attr_name}: "{attr_val}"\n')


def generate_host_sensors(machine: dict, config: dict) -> list:
    """Generate host/status sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    host_config = config.get("host", {})
    if not host_config.get("enabled", False):
        return sensors

    # Uptime - directly from host.uptime_s
    sensors.append({
        "name": f"{name} Uptime (s)",
        "unique_id": generate_uuid(f"{slug}_uptime_s"),
        "availability": "{{ available }}",
        "state": "{{ (host.uptime_s | default(0)) | int }}",
        "icon": "mdi:timer-outline",
        "device_class": "duration",
        "unit_of_measurement": "s",
        "state_class": "measurement",
    })

    # Process count
    sensors.append({
        "name": f"{name} Process Count",
        "unique_id": generate_uuid(f"{slug}_process_count"),
        "availability": "{{ available }}",
        "state": "{{ (host.process_count | default(0)) | int }}",
        "icon": "mdi:application",
        "state_class": "measurement",
    })

    return sensors


def generate_health_sensors(machine: dict, config: dict) -> list:
    """Generate health status sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    health_config = config.get("health", {})
    if not health_config.get("enabled", False):
        return sensors

    # Overall status summary (first issue or 'OK', truncated to fit HA state limit)
    sensors.append({
        "name": f"{name} Overall Status Summary",
        "unique_id": generate_uuid(f"{slug}_overall_status_summary"),
        "availability": "{{ available }}",
        "state": (
            "{{ (health.issues[0][:250] ~ '...') if health.issues and health.issues[0]|length > 250 else"
            " (health.issues[0] if health.issues else 'OK') }}"
        ),
        "icon": "mdi:card-text-outline",
    })

    # Updates pending
    sensors.append({
        "name": f"{name} Updates Pending",
        "unique_id": generate_uuid(f"{slug}_updates_pending"),
        "availability": "{{ available }}",
        "state": "{{ ((health.updates | default({})).pending | default(0)) | int }}",
        "icon": "mdi:update",
        "state_class": "measurement",
    })

    # Updates list (package names)
    # Use .get() to safely access 'items' key without triggering dict.items() method
    sensors.append({
        "name": f"{name} Updates List",
        "unique_id": generate_uuid(f"{slug}_updates_list"),
        "availability": "{{ available }}",
        "state": "{{ ((health.updates | default({})).get('items', []) | map(attribute='name') | list | length) }} packages",
        "icon": "mdi:package-variant",
        "attributes": {
            "packages": "{{ (health.updates | default({})).get('items', []) | map(attribute='name') | list }}",
        },
    })

    # Services checked count
    sensors.append({
        "name": f"{name} Services Checked",
        "unique_id": generate_uuid(f"{slug}_services_checked"),
        "availability": "{{ available }}",
        "state": "{{ (health.services | default([]) | length) }}",
        "icon": "mdi:playlist-check",
        "state_class": "measurement",
    })

    # Containers checked count
    sensors.append({
        "name": f"{name} Containers Checked",
        "unique_id": generate_uuid(f"{slug}_containers_checked"),
        "availability": "{{ available }}",
        "state": "{{ (health.containers | default([]) | length) }}",
        "icon": "mdi:docker",
        "state_class": "measurement",
    })

    return sensors


def generate_cpu_sensors(machine: dict, config: dict) -> list:
    """Generate CPU-related sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    cpu_config = config.get("cpu", {})
    if not cpu_config.get("enabled", False):
        return sensors

    metrics = cpu_config.get("metrics", [])

    # CPU data is in cpus[0] for single-CPU systems
    if "load_pct" in metrics:
        sensors.append({
            "name": f"{name} CPU Utilization",
            "unique_id": generate_uuid(f"{slug}_cpu_utilization"),
            "availability": "{{ available }}",
            "state": "{{ (cpus[0].load_pct | default(0)) | round(1) }}",
            "icon": "mdi:chip",
            "unit_of_measurement": "%",
            "state_class": "measurement",
        })

    if "load_1m" in metrics:
        sensors.append({
            "name": f"{name} CPU Load 1m",
            "unique_id": generate_uuid(f"{slug}_cpu_load_1m"),
            "availability": "{{ available }}",
            "state": "{{ (cpus[0].load_1m | default(0)) | round(2) }}",
            "icon": "mdi:chip",
            "state_class": "measurement",
        })

    if "load_5m" in metrics:
        sensors.append({
            "name": f"{name} CPU Load 5m",
            "unique_id": generate_uuid(f"{slug}_cpu_load_5m"),
            "availability": "{{ available }}",
            "state": "{{ (cpus[0].load_5m | default(0)) | round(2) }}",
            "icon": "mdi:chip",
            "state_class": "measurement",
        })

    if "load_15m" in metrics:
        sensors.append({
            "name": f"{name} CPU Load 15m",
            "unique_id": generate_uuid(f"{slug}_cpu_load_15m"),
            "availability": "{{ available }}",
            "state": "{{ (cpus[0].load_15m | default(0)) | round(2) }}",
            "icon": "mdi:chip",
            "state_class": "measurement",
        })

    if "temp_c" in metrics:
        sensors.append({
            "name": f"{name} CPU Temp",
            "unique_id": generate_uuid(f"{slug}_cpu_temp"),
            "availability": "{{ available }}",
            "state": "{{ (cpus[0].temp_c | default(0)) | round(1) }}",
            "unit_of_measurement": "°C",
            "state_class": "measurement",
            "device_class": "temperature",
        })

    if "num_physical_cores" in metrics:
        sensors.append({
            "name": f"{name} CPU Physical Cores",
            "unique_id": generate_uuid(f"{slug}_cpu_physical_cores"),
            "availability": "{{ available }}",
            "state": "{{ cpus[0].num_physical_cores | default(0) }}",
            "icon": "mdi:chip",
            "state_class": "measurement",
        })

    if "num_logical_cores" in metrics:
        sensors.append({
            "name": f"{name} CPU Logical Cores",
            "unique_id": generate_uuid(f"{slug}_cpu_logical_cores"),
            "availability": "{{ available }}",
            "state": "{{ cpus[0].num_logical_cores | default(0) }}",
            "icon": "mdi:chip",
            "state_class": "measurement",
        })

    if "power_w" in metrics:
        sensors.append({
            "name": f"{name} CPU Power",
            "unique_id": generate_uuid(f"{slug}_cpu_power"),
            "availability": "{{ available }}",
            "state": "{{ (cpus[0].power_w | default(0)) | round(1) }}",
            "icon": "mdi:flash",
            "unit_of_measurement": "W",
            "state_class": "measurement",
            "device_class": "power",
        })

    return sensors


def generate_memory_sensors(machine: dict, config: dict) -> list:
    """Generate memory-related sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    mem_config = config.get("memory", {})
    if not mem_config.get("enabled", False):
        return sensors

    metrics = mem_config.get("metrics", [])

    if "system.load_pct" in metrics:
        sensors.append({
            "name": f"{name} Memory Percent",
            "unique_id": generate_uuid(f"{slug}_memory_percent"),
            "availability": "{{ available }}",
            "state": "{{ (memory.system.load_pct | default(0)) | round(1) }}",
            "icon": "mdi:memory",
            "unit_of_measurement": "%",
            "state_class": "measurement",
        })

    if "system.used_b" in metrics:
        sensors.append({
            "name": f"{name} Memory Used",
            "unique_id": generate_uuid(f"{slug}_memory_used"),
            "availability": "{{ available }}",
            "state": "{{ ((memory.system.used_b | default(0)) / 1073741824) | round(2) }}",
            "unit_of_measurement": "GiB",
            "device_class": "data_size",
            "state_class": "measurement",
        })

    if "system.available_b" in metrics:
        sensors.append({
            "name": f"{name} Memory Available",
            "unique_id": generate_uuid(f"{slug}_memory_available"),
            "availability": "{{ available }}",
            "state": "{{ ((memory.system.available_b | default(0)) / 1073741824) | round(2) }}",
            "unit_of_measurement": "GiB",
            "device_class": "data_size",
            "state_class": "measurement",
        })

    if "system.total_b" in metrics:
        sensors.append({
            "name": f"{name} Memory Total",
            "unique_id": generate_uuid(f"{slug}_memory_total"),
            "availability": "{{ available }}",
            "state": "{{ ((memory.system.total_b | default(0)) / 1073741824) | round(2) }}",
            "unit_of_measurement": "GiB",
            "device_class": "data_size",
            "state_class": "measurement",
        })

    if "virtual.load_pct" in metrics:
        sensors.append({
            "name": f"{name} Swap Percent",
            "unique_id": generate_uuid(f"{slug}_swap_percent"),
            "availability": "{{ available }}",
            "state": "{{ (memory.virtual.load_pct | default(0)) | round(1) }}",
            "icon": "mdi:memory",
            "unit_of_measurement": "%",
            "state_class": "measurement",
        })

    if "virtual.used_b" in metrics:
        sensors.append({
            "name": f"{name} Swap Used",
            "unique_id": generate_uuid(f"{slug}_swap_used"),
            "availability": "{{ available }}",
            "state": "{{ ((memory.virtual.used_b | default(0)) / 1073741824) | round(2) }}",
            "unit_of_measurement": "GiB",
            "device_class": "data_size",
            "state_class": "measurement",
        })

    if "virtual.available_b" in metrics:
        sensors.append({
            "name": f"{name} Swap Available",
            "unique_id": generate_uuid(f"{slug}_swap_available"),
            "availability": "{{ available }}",
            "state": "{{ ((memory.virtual.available_b | default(0)) / 1073741824) | round(2) }}",
            "unit_of_measurement": "GiB",
            "device_class": "data_size",
            "state_class": "measurement",
        })

    if "virtual.total_b" in metrics:
        sensors.append({
            "name": f"{name} Swap Total",
            "unique_id": generate_uuid(f"{slug}_swap_total"),
            "availability": "{{ available }}",
            "state": "{{ ((memory.virtual.total_b | default(0)) / 1073741824) | round(2) }}",
            "unit_of_measurement": "GiB",
            "device_class": "data_size",
            "state_class": "measurement",
        })

    return sensors


def generate_filesystem_sensors(machine: dict, config: dict) -> list:
    """Generate filesystem-related sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    fs_config = config.get("filesystems", {})
    if not fs_config.get("enabled", False):
        return sensors

    includes = fs_config.get("include", [])

    for fs in includes:
        # Support matching by label or mountpoint
        label = fs.get("label", "")
        mountpoint = fs.get("mountpoint", "")
        display = fs.get("display_name", (label or mountpoint).title())
        display_slug = slugify(display)

        # Determine the match attribute and value
        if label:
            match_attr = "label"
            match_val = label
        elif mountpoint:
            match_attr = "mountpoint"
            match_val = mountpoint
        else:
            continue  # Skip if neither label nor mountpoint specified

        # Percent used (calculated from used_b and available_b)
        sensors.append({
            "name": f"{name} FS {display} Percent",
            "unique_id": generate_uuid(f"{slug}_fs_{display_slug}_percent"),
            "availability": "{{ available }}",
            "state": (
                f"{{% set fs = filesystems | selectattr('{match_attr}', 'eq', '{match_val}') | first | default(none)"
                " %}{{ ((fs.used_b / (fs.used_b + fs.available_b)) * 100) | round(1) if fs else 0 }}"
            ),
            "icon": "mdi:harddisk",
            "unit_of_measurement": "%",
            "state_class": "measurement",
        })

        # Used space in GiB
        sensors.append({
            "name": f"{name} FS {display} Used",
            "unique_id": generate_uuid(f"{slug}_fs_{display_slug}_used"),
            "availability": "{{ available }}",
            "state": (
                f"{{% set fs = filesystems | selectattr('{match_attr}', 'eq', '{match_val}') | first | default(none)"
                " %}{{ ((fs.used_b | default(0)) / 1073741824) | round(2) if fs else 0 }}"
            ),
            "icon": "mdi:harddisk",
            "unit_of_measurement": "GiB",
            "device_class": "data_size",
            "state_class": "measurement",
        })

        # Total space in GiB
        sensors.append({
            "name": f"{name} FS {display} Total",
            "unique_id": generate_uuid(f"{slug}_fs_{display_slug}_total"),
            "availability": "{{ available }}",
            "state": (
                f"{{% set fs = filesystems | selectattr('{match_attr}', 'eq', '{match_val}') | first | default(none)"
                " %}{{ (((fs.used_b | default(0)) + (fs.available_b | default(0))) / 1073741824) | round(2) if fs"
                " else 0 }}"
            ),
            "icon": "mdi:harddisk",
            "unit_of_measurement": "GiB",
            "device_class": "data_size",
            "state_class": "measurement",
        })

    return sensors


def generate_network_sensors(machine: dict, config: dict) -> list:
    """Generate network-related sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    net_config = config.get("network", {})
    if not net_config.get("enabled", False):
        return sensors

    includes = net_config.get("include", [])

    # If specific interfaces are listed, create sensors for each
    if includes:
        for iface in includes:
            iface_name = iface.get("name", "")
            display = iface.get("display_name", iface_name)
            iface_slug = slugify(display)

            sensors.append({
                "name": f"{name} {display} Upload",
                "unique_id": generate_uuid(f"{slug}_{iface_slug}_upload"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                    "{{ (iface.rate_up_bps | default(0)) | round(0) if iface else 0 }}"
                ),
                "icon": "mdi:upload",
                "device_class": "data_rate",
                "unit_of_measurement": "B/s",
            })

            sensors.append({
                "name": f"{name} {display} Download",
                "unique_id": generate_uuid(f"{slug}_{iface_slug}_download"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                    "{{ (iface.rate_down_bps | default(0)) | round(0) if iface else 0 }}"
                ),
                "icon": "mdi:download",
                "device_class": "data_rate",
                "unit_of_measurement": "B/s",
            })

            sensors.append({
                "name": f"{name} {display} IPv4",
                "unique_id": generate_uuid(f"{slug}_{iface_slug}_ipv4"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                    "{{ iface.ipv4 | default('unknown') if iface else 'unknown' }}"
                ),
            })

            # Network interface info sensor with detailed attributes
            sensors.append({
                "name": f"{name} {display} Info",
                "unique_id": generate_uuid(f"{slug}_{iface_slug}_info"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                    "{{ iface.name | default('Unknown') if iface else 'Unknown' }}"
                ),
                "icon": "mdi:ethernet",
                "attributes": {
                    "name": (
                        f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                        "{{ iface.name | default('Unknown') if iface else 'Unknown' }}"
                    ),
                    "mac": (
                        f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                        "{{ iface.mac | default('Unknown') if iface else 'Unknown' }}"
                    ),
                    "ipv4": (
                        f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                        "{{ iface.ipv4 | default('None') if iface else 'None' }}"
                    ),
                    "ipv6": (
                        f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                        "{{ iface.ipv6 | default('None') if iface else 'None' }}"
                    ),
                    "link_speed_mbps": (
                        f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                        "{{ iface.link_speed_mbps | default(0) if iface else 0 }}"
                    ),
                    "duplex": (
                        f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                        "{{ iface.duplex | default('unknown') if iface else 'unknown' }}"
                    ),
                    "mtu": (
                        f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                        "{{ iface.mtu | default(0) if iface else 0 }}"
                    ),
                    "carrier": (
                        f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                        "{{ iface.carrier | default(false) if iface else false }}"
                    ),
                    "driver": (
                        f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                        "{{ iface.driver | default('Unknown') if iface else 'Unknown' }}"
                    ),
                },
            })
    else:
        # Default: create sensors for the first interface with an IPv4
        sensors.append({
            "name": f"{name} Network Upload",
            "unique_id": generate_uuid(f"{slug}_network_upload"),
            "availability": "{{ available }}",
            "state": (
                "{% set iface = ifaces | selectattr('ipv4', 'defined') | selectattr('carrier', 'eq', true) | first |"
                " default(none) %}{{ (iface.rate_up_bps | default(0)) | round(0) if iface else 0 }}"
            ),
            "icon": "mdi:upload",
            "device_class": "data_rate",
            "unit_of_measurement": "B/s",
        })

        sensors.append({
            "name": f"{name} Network Download",
            "unique_id": generate_uuid(f"{slug}_network_download"),
            "availability": "{{ available }}",
            "state": (
                "{% set iface = ifaces | selectattr('ipv4', 'defined') | selectattr('carrier', 'eq', true) | first |"
                " default(none) %}{{ (iface.rate_down_bps | default(0)) | round(0) if iface else 0 }}"
            ),
            "icon": "mdi:download",
            "device_class": "data_rate",
            "unit_of_measurement": "B/s",
        })

    return sensors


def generate_gpu_sensors(machine: dict, config: dict) -> list:
    """Generate GPU-related sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    gpu_config = config.get("gpus", {})
    if not gpu_config.get("enabled", False):
        return sensors

    metrics = gpu_config.get("metrics", [])

    # GPU Utilization (core load)
    if "core.load_pct" in metrics:
        sensors.append({
            "name": f"{name} GPU Utilization",
            "unique_id": generate_uuid(f"{slug}_gpu_utilization"),
            "availability": "{{ available }}",
            "state": "{{ (gpus[0].core.load_pct | default(0)) | round(1) if gpus else 0 }}",
            "icon": "mdi:gpu",
            "unit_of_measurement": "%",
            "state_class": "measurement",
        })

    # GPU Temperature
    if "temp_c" in metrics:
        sensors.append({
            "name": f"{name} GPU Temp",
            "unique_id": generate_uuid(f"{slug}_gpu_temp"),
            "availability": "{{ available }}",
            "state": "{{ (gpus[0].temp_c | default(0)) | round(0) | int if gpus else 0 }}",
            "unit_of_measurement": "°C",
            "state_class": "measurement",
            "device_class": "temperature",
        })

    # GPU Power
    if "core.power_w" in metrics:
        sensors.append({
            "name": f"{name} GPU Power",
            "unique_id": generate_uuid(f"{slug}_gpu_power"),
            "availability": "{{ available }}",
            "state": "{{ (gpus[0].core.power_w | default(0)) | round(1) if gpus else 0 }}",
            "icon": "mdi:lightning-bolt",
            "unit_of_measurement": "W",
            "state_class": "measurement",
            "device_class": "power",
        })

    # GPU Engine sensors (for mini-graph-card visualization)
    if "engines" in metrics:
        # Get engine configuration - can specify which engines to create sensors for
        engine_config = gpu_config.get("engine_sensors", [])
        if not engine_config:
            # Default to common GPU engines if not specified
            engine_config = [
                {"name": "GPU Core", "slug": "gpu_core"},
                {"name": "D3D 3D", "slug": "d3d_3d"},
                {"name": "D3D Copy", "slug": "d3d_copy"},
                {"name": "D3D Video Codec 0", "slug": "d3d_video_codec"},
            ]

        for engine in engine_config:
            engine_name = engine.get("name", "")
            engine_slug = engine.get("slug", engine_name.lower().replace(" ", "_").replace("-", "_"))
            # Use slug-based display name for consistent entity_id generation
            slug_display = engine_slug.replace('_', ' ').title()
            sensors.append({
                "name": f"{name} GPU Engine {slug_display}",
                "unique_id": generate_uuid(f"{slug}_gpu_engine_{engine_slug}"),
                "availability": "{{ available }}",
                "state": f"{{{{ ((gpus[0]['engines'] | default([]) | selectattr('name', 'eq', '{engine_name}') | first | default({{}}))['load_pct'] | default(0)) | round(0) | int if gpus else 0 }}}}",
                "icon": "mdi:engine",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            })

    return sensors


def generate_tpu_sensors(machine: dict, config: dict) -> list:
    """Generate TPU-related sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    tpu_config = config.get("tpus", {})
    if not tpu_config.get("enabled", False):
        return sensors

    sensors.append({
        "name": f"{name} Coral TPU Temp",
        "unique_id": generate_uuid(f"{slug}_coral_tpu_temp"),
        "availability": "{{ available }}",
        "state": "{{ (tpus[0].temp_c | default(0)) | round(1) if tpus else 0 }}",
        "unit_of_measurement": "°C",
        "state_class": "measurement",
        "device_class": "temperature",
    })

    sensors.append({
        "name": f"{name} Coral TPU Throttling",
        "unique_id": generate_uuid(f"{slug}_coral_tpu_throttling"),
        "availability": "{{ available }}",
        "state": "{{ tpus[0].thermal.throttling | default(false) if tpus else false }}",
        "icon": "mdi:thermometer-alert",
    })

    # TPU Thermal Info sensor with trip points and DFS states
    sensors.append({
        "name": f"{name} Coral TPU Thermal Info",
        "unique_id": generate_uuid(f"{slug}_coral_tpu_thermal_info"),
        "availability": "{{ available }}",
        "state": (
            "{% set tpu = tpus[0] if tpus else none %}"
            "{% if tpu and tpu.thermal %}"
            "{% if tpu.thermal.throttling | default(false) %}Throttling"
            "{% else %}OK{% endif %}"
            "{% else %}Unknown{% endif %}"
        ),
        "icon": "mdi:chip",
        "attributes": {
            "name": (
                "{{ tpus[0].name | default('Unknown') if tpus else 'Unknown' }}"
            ),
            "model": (
                "{{ tpus[0].model | default('Coral Edge TPU') if tpus else 'Unknown' }}"
            ),
            "temp_c": (
                "{{ (tpus[0].temp_c | default(0)) | round(1) if tpus else 0 }}"
            ),
            "warning_c": (
                "{{ (tpus[0].thermal.warning_c | default(0)) | round(1) if tpus and tpus[0].thermal else 0 }}"
            ),
            "critical_c": (
                "{{ (tpus[0].thermal.critical_c | default(0)) | round(1) if tpus and tpus[0].thermal else 0 }}"
            ),
            "throttling": (
                "{{ tpus[0].thermal.throttling | default(false) if tpus and tpus[0].thermal else false }}"
            ),
            "dfs_enabled": (
                "{% set tpu = tpus[0] if tpus else none %}"
                "{% set dfs = tpu.thermal.get('dfs', {}) if tpu and tpu.thermal else {} %}"
                "{{ dfs.get('enabled', false) }}"
            ),
            "dfs_active_state": (
                "{% set tpu = tpus[0] if tpus else none %}"
                "{% set dfs = tpu.thermal.get('dfs', {}) if tpu and tpu.thermal else {} %}"
                "{{ dfs.get('active_state', 'unknown') }}"
            ),
            "dfs_states": (
                "{% set tpu = tpus[0] if tpus else none %}"
                "{% set dfs = tpu.thermal.get('dfs', {}) if tpu and tpu.thermal else {} %}"
                "{% set states = dfs.get('states', []) %}"
                "{% if states %}"
                "{% for s in states %}"
                "{{ (s.trip_point_c | default(0) | round(0) | int | string) ~ '°C → ' ~ ((s.clock_limit_hz | default(0)) / 1000000 | round(0) | int | string) ~ ' MHz' }}"
                "{% if not loop.last %}, {% endif %}"
                "{% endfor %}"
                "{% else %}No states{% endif %}"
            ),
        },
    })

    return sensors


def generate_sbc_sensors(machine: dict, config: dict) -> list:
    """Generate SBC (Raspberry Pi) specific sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    sbc_config = config.get("sbc", {})
    if not sbc_config.get("enabled", False):
        return sensors

    metrics = sbc_config.get("metrics", [])

    # Throttling status (from host.throttling)
    if "throttling" in metrics:
        sensors.append({
            "name": f"{name} Throttling Status",
            "unique_id": generate_uuid(f"{slug}_throttling_status"),
            "availability": "{{ available }}",
            "state": "{{ 'Throttled' if (throttling.currently_throttled | default(false)) else 'OK' }}",
            "icon": "mdi:speedometer-slow",
            "attributes": {
                "undervoltage": "{{ throttling.undervoltage | default(false) }}",
                "arm_freq_capped": "{{ throttling.arm_freq_capped | default(false) }}",
                "currently_throttled": "{{ throttling.currently_throttled | default(false) }}",
                "soft_temp_limit": "{{ throttling.soft_temp_limit | default(false) }}",
                "undervoltage_occurred": "{{ throttling.undervoltage_occurred | default(false) }}",
                "arm_freq_cap_occurred": "{{ throttling.arm_freq_cap_occurred | default(false) }}",
                "throttle_occurred": "{{ throttling.throttle_occurred | default(false) }}",
                "soft_temp_limit_occurred": "{{ throttling.soft_temp_limit_occurred | default(false) }}",
            },
        })

    # ARM memory
    if "arm_mem_b" in metrics:
        sensors.append({
            "name": f"{name} ARM Memory",
            "unique_id": generate_uuid(f"{slug}_arm_memory"),
            "availability": "{{ available }}",
            "state": "{{ ((sbc.arm_mem_b | default(0)) / 1048576) | round(0) | int }}",
            "icon": "mdi:memory",
            "unit_of_measurement": "MiB",
            "device_class": "data_size",
            "state_class": "measurement",
        })

    # GPU memory
    if "gpu_mem_b" in metrics:
        sensors.append({
            "name": f"{name} GPU Memory",
            "unique_id": generate_uuid(f"{slug}_gpu_memory"),
            "availability": "{{ available }}",
            "state": "{{ ((sbc.gpu_mem_b | default(0)) / 1048576) | round(0) | int }}",
            "icon": "mdi:memory",
            "unit_of_measurement": "MiB",
            "device_class": "data_size",
            "state_class": "measurement",
        })

    # Core voltage
    if "voltages.core_v" in metrics:
        sensors.append({
            "name": f"{name} Core Voltage",
            "unique_id": generate_uuid(f"{slug}_core_voltage"),
            "availability": "{{ available }}",
            "state": "{{ ((sbc.voltages | default({})).core_v | default(0)) | round(2) }}",
            "icon": "mdi:flash",
            "unit_of_measurement": "V",
            "state_class": "measurement",
            "device_class": "voltage",
        })

    # ARM clock frequency
    if "clocks.arm_hz" in metrics:
        sensors.append({
            "name": f"{name} ARM Clock",
            "unique_id": generate_uuid(f"{slug}_arm_clock"),
            "availability": "{{ available }}",
            "state": "{{ (((sbc.clocks | default({})).arm_hz | default(0)) / 1000000) | round(0) | int }}",
            "icon": "mdi:sine-wave",
            "unit_of_measurement": "MHz",
            "device_class": "frequency",
            "state_class": "measurement",
        })

    return sensors


def generate_time_server_sensors(machine: dict, config: dict) -> list:
    """Generate time server (chrony/NTP/GPS) sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    ts_config = config.get("time_server", {})
    if not ts_config.get("enabled", False):
        return sensors

    metrics = ts_config.get("metrics", [])

    # Chrony tracking metrics
    if "tracking.reference_name" in metrics:
        sensors.append({
            "name": f"{name} NTP Reference",
            "unique_id": generate_uuid(f"{slug}_ntp_reference"),
            "availability": "{{ available }}",
            "state": "{{ (time_server.tracking | default({})).reference_name | default('unknown') }}",
            "icon": "mdi:clock-check",
        })

    if "tracking.stratum" in metrics:
        sensors.append({
            "name": f"{name} NTP Stratum",
            "unique_id": generate_uuid(f"{slug}_ntp_stratum"),
            "availability": "{{ available }}",
            "state": "{{ (time_server.tracking | default({})).stratum | default(0) }}",
            "icon": "mdi:layers",
            "state_class": "measurement",
        })

    if "tracking.system_time_offset_s" in metrics:
        sensors.append({
            "name": f"{name} Time Offset",
            "unique_id": generate_uuid(f"{slug}_time_offset"),
            "availability": "{{ available }}",
            "state": "{{ (((time_server.tracking | default({})).system_time_offset_s | default(0)) * 1000000) | round(3) }}",
            "icon": "mdi:clock-alert",
            "unit_of_measurement": "µs",
            "device_class": "duration",
            "state_class": "measurement",
        })

    if "tracking.rms_offset_s" in metrics:
        sensors.append({
            "name": f"{name} RMS Offset",
            "unique_id": generate_uuid(f"{slug}_rms_offset"),
            "availability": "{{ available }}",
            "state": "{{ (((time_server.tracking | default({})).rms_offset_s | default(0)) * 1000000) | round(3) }}",
            "icon": "mdi:chart-line-variant",
            "unit_of_measurement": "µs",
            "device_class": "duration",
            "state_class": "measurement",
        })

    if "tracking.frequency_ppm" in metrics:
        sensors.append({
            "name": f"{name} Frequency Offset",
            "unique_id": generate_uuid(f"{slug}_frequency_offset"),
            "availability": "{{ available }}",
            "state": "{{ ((time_server.tracking | default({})).frequency_ppm | default(0)) | round(3) }}",
            "icon": "mdi:sine-wave",
            "unit_of_measurement": "ppm",
            "state_class": "measurement",
        })

    if "tracking.leap_status" in metrics:
        sensors.append({
            "name": f"{name} Leap Status",
            "unique_id": generate_uuid(f"{slug}_leap_status"),
            "availability": "{{ available }}",
            "state": "{{ (time_server.tracking | default({})).leap_status | default('Normal') }}",
            "icon": "mdi:clock-fast",
        })

    # GPS metrics
    if "gps.mode" in metrics:
        sensors.append({
            "name": f"{name} GPS Mode",
            "unique_id": generate_uuid(f"{slug}_gps_mode"),
            "availability": "{{ available }}",
            # "state": "{{ time_server.gps.mode | default(0) }}",
            "state": (
                "{{ {0: 'No Fix', 1: 'No Fix', 2: '2D', 3: '3D'}.get((time_server.gps | default({})).mode | default(0), 'Unknown') }}"
            ),
            "icon": "mdi:crosshairs-gps",
            "device_class": "enum",
            "attributes": {
                "mode_text": (
                    "{{ {0: 'No Fix', 1: 'No Fix', 2: '2D', 3: '3D'}.get((time_server.gps | default({})).mode | default(0),"
                    " 'Unknown') }}"
                ),
            },
        })

    if "gps.status" in metrics:
        sensors.append({
            "name": f"{name} GPS Status",
            "unique_id": generate_uuid(f"{slug}_gps_status"),
            "availability": "{{ available }}",
            # "state": "{{ time_server.gps.status | default(0) }}",
            "state": (
                "{{ {0: 'Unknown', 1: 'Normal', 2: 'DGPS', 3: 'RTK Fixed', 4: 'RTK Float', 5: 'Dead"
                " Reckoning'}.get((time_server.gps | default({})).status | default(0), 'Unknown') }}"
            ),
            "icon": "mdi:satellite-variant",
            "device_class": "enum",
            "attributes": {
                "status_text": (
                    "{{ {0: 'Unknown', 1: 'Normal', 2: 'DGPS', 3: 'RTK Fixed', 4: 'RTK Float', 5: 'Dead"
                    " Reckoning'}.get((time_server.gps | default({})).status | default(0), 'Unknown') }}"
                ),
            },
        })

    if "gps.satellites_visible" in metrics:
        sensors.append({
            "name": f"{name} GPS Satellites Visible",
            "unique_id": generate_uuid(f"{slug}_gps_satellites_visible"),
            "availability": "{{ available }}",
            "state": "{{ (time_server.gps | default({})).satellites_visible | default(0) }}",
            "icon": "mdi:satellite-variant",
            "state_class": "measurement",
        })

    if "gps.satellites_used" in metrics:
        sensors.append({
            "name": f"{name} GPS Satellites Used",
            "unique_id": generate_uuid(f"{slug}_gps_satellites_used"),
            "availability": "{{ available }}",
            "state": "{{ (time_server.gps | default({})).satellites_used | default(0) }}",
            "icon": "mdi:satellite-variant",
            "state_class": "measurement",
        })

    if "gps.hdop" in metrics:
        sensors.append({
            "name": f"{name} GPS HDOP",
            "unique_id": generate_uuid(f"{slug}_gps_hdop"),
            "availability": "{{ available }}",
            "state": "{{ ((time_server.gps | default({})).hdop | default(99)) | round(2) }}",
            "icon": "mdi:crosshairs-question",
            "state_class": "measurement",
        })

    if "gps.latitude" in metrics:
        sensors.append({
            "name": f"{name} GPS Latitude",
            "unique_id": generate_uuid(f"{slug}_gps_latitude"),
            "availability": "{{ available }}",
            "state": "{{ ((time_server.gps | default({})).latitude | default(0)) | round(6) }}",
            "icon": "mdi:latitude",
            "unit_of_measurement": "°",
            "state_class": "measurement",
        })

    if "gps.longitude" in metrics:
        sensors.append({
            "name": f"{name} GPS Longitude",
            "unique_id": generate_uuid(f"{slug}_gps_longitude"),
            "availability": "{{ available }}",
            "state": "{{ ((time_server.gps | default({})).longitude | default(0)) | round(6) }}",
            "icon": "mdi:longitude",
            "unit_of_measurement": "°",
            "state_class": "measurement",
        })

    # Server stats
    if "server_stats.ntp_packets_received" in metrics:
        sensors.append({
            "name": f"{name} NTP Packets Received",
            "unique_id": generate_uuid(f"{slug}_ntp_packets_received"),
            "availability": "{{ available }}",
            "state": "{{ (time_server.server_stats | default({})).ntp_packets_received | default(0) }}",
            "icon": "mdi:counter",
            "state_class": "total_increasing",
        })

    if "server_stats.client_count" in metrics:
        sensors.append({
            "name": f"{name} NTP Client Count",
            "unique_id": generate_uuid(f"{slug}_ntp_client_count"),
            "availability": "{{ available }}",
            "state": "{{ (time_server.server_stats | default({})).client_count | default(0) }}",
            "icon": "mdi:account-multiple",
            "state_class": "measurement",
        })

    return sensors


def generate_motherboard_sensors(machine: dict, config: dict) -> list:
    """Generate motherboard temperature sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    mb_config = config.get("motherboard", {})
    if not mb_config.get("enabled", False):
        return sensors

    temps_config = mb_config.get("temps", {})
    includes = temps_config.get("include", [])

    for temp in includes:
        pattern = temp.get("pattern", "")
        display = temp.get("display_name", pattern)
        temp_slug = slugify(display)

        sensors.append({
            "name": f"{name} {display}",
            "unique_id": generate_uuid(f"{slug}_{temp_slug}"),
            "availability": "{{ available }}",
            "state": (
                f"{{% set t = motherboard_temps | selectattr('name', 'eq', '{pattern}') | first | default(none) %}}"
                "{{ (t.temp_c | default(0)) | round(1) if t else 0 }}"
            ),
            "unit_of_measurement": "°C",
            "state_class": "measurement",
            "device_class": "temperature",
        })

    return sensors


def generate_battery_sensors(machine: dict, config: dict) -> list:
    """Generate battery sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    bat_config = config.get("batteries", {})
    if not bat_config.get("enabled", False):
        return sensors

    metrics = bat_config.get("metrics", [])

    if "charge_level_pct" in metrics:
        sensors.append({
            "name": f"{name} Battery Level",
            "unique_id": generate_uuid(f"{slug}_battery_level"),
            "availability": "{{ available }}",
            "state": "{{ (batteries[0].charge_level_pct | default(0)) | round(0) | int if batteries else 0 }}",
            "icon": "mdi:battery",
            "unit_of_measurement": "%",
            "state_class": "measurement",
            "device_class": "battery",
        })

    if "discharging" in metrics:
        sensors.append({
            "name": f"{name} Battery Status",
            "unique_id": generate_uuid(f"{slug}_battery_status"),
            "availability": "{{ available }}",
            "state": "{{ 'Discharging' if batteries[0].discharging else 'Charging' if batteries else 'Unknown' }}",
            "icon": "mdi:battery-charging",
        })

    if "power_w" in metrics:
        sensors.append({
            "name": f"{name} Battery Power",
            "unique_id": generate_uuid(f"{slug}_battery_power"),
            "availability": "{{ available }}",
            "state": "{{ (batteries[0].power_w | default(0)) | round(1) if batteries else 0 }}",
            "icon": "mdi:flash",
            "unit_of_measurement": "W",
            "state_class": "measurement",
            "device_class": "power",
        })

    if "voltage_v" in metrics:
        sensors.append({
            "name": f"{name} Battery Voltage",
            "unique_id": generate_uuid(f"{slug}_battery_voltage"),
            "availability": "{{ available }}",
            "state": "{{ (batteries[0].voltage_v | default(0)) | round(2) if batteries else 0 }}",
            "icon": "mdi:flash",
            "unit_of_measurement": "V",
            "state_class": "measurement",
            "device_class": "voltage",
        })

    if "degradation_pct" in metrics:
        sensors.append({
            "name": f"{name} Battery Degradation",
            "unique_id": generate_uuid(f"{slug}_battery_degradation"),
            "availability": "{{ available }}",
            "state": "{{ (batteries[0].degradation_pct | default(0)) | round(1) if batteries else 0 }}",
            "icon": "mdi:battery-alert",
            "unit_of_measurement": "%",
            "state_class": "measurement",
        })

    if "remain_cap_mwh" in metrics:
        sensors.append({
            "name": f"{name} Battery Remaining Capacity",
            "unique_id": generate_uuid(f"{slug}_battery_remaining_capacity"),
            "availability": "{{ available }}",
            "state": "{{ ((batteries[0].remain_cap_mwh | default(0)) / 1000) | round(1) if batteries else 0 }}",
            "icon": "mdi:battery",
            "unit_of_measurement": "Wh",
            "device_class": "energy",
        })

    if "full_cap_mwh" in metrics:
        sensors.append({
            "name": f"{name} Battery Full Capacity",
            "unique_id": generate_uuid(f"{slug}_battery_full_capacity"),
            "availability": "{{ available }}",
            "state": "{{ ((batteries[0].full_cap_mwh | default(0)) / 1000) | round(1) if batteries else 0 }}",
            "icon": "mdi:battery",
            "unit_of_measurement": "Wh",
            "device_class": "energy",
        })

    return sensors


def generate_drive_sensors(machine: dict, config: dict) -> list:
    """Generate drive sensors with SMART data, transfer rates, and partition info."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    drv_config = config.get("drives", {})
    if not drv_config.get("enabled", False):
        return sensors

    includes = drv_config.get("include", [])
    metrics = drv_config.get("metrics", [])

    for drive in includes:
        drive_name = drive.get("name", "")
        display = drive.get("display_name", drive_name)
        drive_slug = slugify(display)

        # Drive total transfer rate (read + write)
        if "transfer_rate" in metrics:
            sensors.append({
                "name": f"{name} {display} Transfer Rate",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_transfer_rate"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{{ (d.total_rate_bps | default(0)) | int if d else 0 }}"
                ),
                "unit_of_measurement": "B/s",
                "device_class": "data_rate",
                "state_class": "measurement",
                "icon": "mdi:harddisk",
            })

        # Drive read rate
        if "read_rate" in metrics:
            sensors.append({
                "name": f"{name} {display} Read Rate",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_read_rate"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{{ (d.read_rate_bps | default(0)) | int if d else 0 }}"
                ),
                "unit_of_measurement": "B/s",
                "device_class": "data_rate",
                "state_class": "measurement",
                "icon": "mdi:arrow-down",
            })

        # Drive write rate
        if "write_rate" in metrics:
            sensors.append({
                "name": f"{name} {display} Write Rate",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_write_rate"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{{ (d.write_rate_bps | default(0)) | int if d else 0 }}"
                ),
                "unit_of_measurement": "B/s",
                "device_class": "data_rate",
                "state_class": "measurement",
                "icon": "mdi:arrow-up",
            })

        # Drive used bytes
        if "used_b" in metrics:
            sensors.append({
                "name": f"{name} {display} Used",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_used"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{{ ((d.used_b | default(0)) / 1073741824) | round(1) if d else 0 }}"
                ),
                "unit_of_measurement": "GiB",
                "device_class": "data_size",
                "state_class": "measurement",
                "icon": "mdi:harddisk",
            })

        # Drive available bytes
        if "available_b" in metrics:
            sensors.append({
                "name": f"{name} {display} Available",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_available"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{{ ((d.available_b | default(0)) / 1073741824) | round(1) if d else 0 }}"
                ),
                "unit_of_measurement": "GiB",
                "device_class": "data_size",
                "state_class": "measurement",
                "icon": "mdi:harddisk",
            })

        # Drive percent used
        if "used_pct" in metrics:
            sensors.append({
                "name": f"{name} {display} Percent Used",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_pct_used"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{% if d %}"
                    "{% set used = d.used_b | default(0) %}"
                    "{% set avail = d.available_b | default(0) %}"
                    "{% set total = used + avail %}"
                    "{{ ((used / total) * 100) | round(1) if total > 0 else 0 }}"
                    "{% else %}0{% endif %}"
                ),
                "unit_of_measurement": "%",
                "state_class": "measurement",
                "icon": "mdi:harddisk",
            })

        # Drive info sensor with model, type, manufacturer as attributes
        if "info" in metrics:
            sensors.append({
                "name": f"{name} {display} Info",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_info"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{{ d.model | default('Unknown') if d else 'Unknown' }}"
                ),
                "icon": "mdi:harddisk",
                "attributes": {
                    "model": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.model | default('Unknown') if d else 'Unknown' }}"
                    ),
                    "type": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.type | default('Unknown') if d else 'Unknown' }}"
                    ),
                    "manufacturer": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.manufacturer | default('Unknown') if d else 'Unknown' }}"
                    ),
                    "serial_number": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.serial_number | default('Unknown') if d else 'Unknown' }}"
                    ),
                    "firmware_version": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.firmware_version | default('Unknown') if d else 'Unknown' }}"
                    ),
                    "listed_capacity_gb": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ ((d.listed_cap_b | default(0)) / 1000000000) | round(0) | int if d else 0 }}"
                    ),
                },
            })

        # Drive temperature
        if "temp_c" in metrics:
            sensors.append({
                "name": f"{name} {display} Temp",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_temp"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{{ (d.temp_c | default(0)) | round(0) | int if d else 0 }}"
                ),
                "unit_of_measurement": "°C",
                "state_class": "measurement",
                "device_class": "temperature",
            })

        # SMART overall health
        if "smart.overall_health" in metrics:
            sensors.append({
                "name": f"{name} {display} Health",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_health"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{{ d.get('smart', {}).get('overall_health', 'Unknown') if d else 'Unknown' }}"
                ),
                "icon": "mdi:harddisk",
            })

        # SMART wear level (percentage used for NVMe)
        if "smart.wear_leveling_pct" in metrics:
            sensors.append({
                "name": f"{name} {display} Wear Level",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_wear_level"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{{ (100 - d.get('smart', {}).get('percentage_used_pct', 0)) | int if d else 100 }}"
                ),
                "icon": "mdi:disc",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            })

        # SMART info sensor (comprehensive SMART data)
        if "smart.info" in metrics:
            sensors.append({
                "name": f"{name} {display} SMART",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_smart"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{{ d.get('smart', {}).get('overall_health', 'Unknown') if d else 'Unknown' }}"
                ),
                "icon": "mdi:harddisk-plus",
                "attributes": {
                    "overall_health": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.get('smart', {}).get('overall_health', 'Unknown') if d else 'Unknown' }}"
                    ),
                    "power_on_hours": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.get('smart', {}).get('power_on_hours', 0) | int if d else 0 }}"
                    ),
                    "power_cycles": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.get('smart', {}).get('power_cycles', 0) | int if d else 0 }}"
                    ),
                    "percentage_used": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.get('smart', {}).get('percentage_used_pct', 0) | round(1) if d else 0 }}"
                    ),
                    "available_spare": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.get('smart', {}).get('available_spare_pct', 0) | round(1) if d else 0 }}"
                    ),
                    "unsafe_shutdowns": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.get('smart', {}).get('unsafe_shutdowns', 0) | int if d else 0 }}"
                    ),
                    "media_errors": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.get('smart', {}).get('media_errors', 0) | int if d else 0 }}"
                    ),
                    "data_units_read": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.get('smart', {}).get('data_units_read', 0) | int if d else 0 }}"
                    ),
                    "data_units_written": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.get('smart', {}).get('data_units_written', 0) | int if d else 0 }}"
                    ),
                },
            })

        # Comprehensive drive status sensor with all key metrics
        if "status" in metrics:
            sensors.append({
                "name": f"{name} {display} Status",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_status"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                    "{{ d.get('smart', {}).get('overall_health', 'Unknown') if d else 'Unknown' }}"
                ),
                "icon": "mdi:harddisk",
                "attributes": {
                    "name": f"{display}",
                    "model": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.model | default('Unknown') if d else 'Unknown' }}"
                    ),
                    "type": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.type | default('Unknown') if d else 'Unknown' }}"
                    ),
                    "serial_number": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.serial_number | default('Unknown') if d else 'Unknown' }}"
                    ),
                    "firmware_version": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.firmware_version | default('Unknown') if d else 'Unknown' }}"
                    ),
                    "capacity_gb": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ ((d.listed_cap_b | default(0)) / 1000000000) | round(0) | int if d else 0 }}"
                    ),
                    "used_gb": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ ((d.used_b | default(0)) / 1073741824) | round(1) if d else 0 }}"
                    ),
                    "available_gb": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ ((d.available_b | default(0)) / 1073741824) | round(1) if d else 0 }}"
                    ),
                    "used_pct": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{% if d %}{% set used = d.used_b | default(0) %}{% set avail = d.available_b | default(0) %}"
                        "{% set total = used + avail %}{{ ((used / total) * 100) | round(1) if total > 0 else 0 }}{% else %}0{% endif %}"
                    ),
                    "temp_c": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.temp_c | default(0) | int if d else 0 }}"
                    ),
                    "health": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.get('smart', {}).get('overall_health', 'Unknown') if d else 'Unknown' }}"
                    ),
                    "wear_level_pct": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ (100 - d.get('smart', {}).get('percentage_used_pct', 0)) | int if d else 100 }}"
                    ),
                    "total_read_tb": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ ((d.total_read_b | default(0)) / 1099511627776) | round(2) if d else 0 }}"
                    ),
                    "total_write_tb": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ ((d.total_write_b | default(0)) / 1099511627776) | round(2) if d else 0 }}"
                    ),
                    "read_rate_mbps": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ ((d.read_rate_bps | default(0)) / 1048576) | round(1) if d else 0 }}"
                    ),
                    "write_rate_mbps": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ ((d.write_rate_bps | default(0)) / 1048576) | round(1) if d else 0 }}"
                    ),
                    "read_activity_pct": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.read_activity_pct | default(0) | round(1) if d else 0 }}"
                    ),
                    "write_activity_pct": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ d.write_activity_pct | default(0) | round(1) if d else 0 }}"
                    ),
                    "partitions": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}"
                        "{{ (d.partitions | default([])) | tojson if d else '[]' }}"
                    ),
                },
            })

        # Partition sensors
        partitions = drive.get("partitions", [])
        for partition in partitions:
            part_name = partition.get("name", "")
            part_display = partition.get("display_name", part_name)
            part_slug = slugify(part_display)

            # Partition info sensor
            sensors.append({
                "name": f"{name} {display} {part_display}",
                "unique_id": generate_uuid(f"{slug}_{drive_slug}_{part_slug}_info"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}{{% set"
                    f" p = (d.partitions | default([]) | selectattr('name', 'eq', '{part_name}') | first |"
                    " default(none)) if d else none %}{{ p.label | default(p.name | default('Unknown')) if p else"
                    " 'Unknown' }}"
                ),
                "icon": "mdi:harddisk",
                "attributes": {
                    "name": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}{{%"
                        f" set p = (d.partitions | default([]) | selectattr('name', 'eq', '{part_name}') | first |"
                        " default(none)) if d else none %}{{ p.name | default('Unknown') if p else 'Unknown' }}"
                    ),
                    "label": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}{{%"
                        f" set p = (d.partitions | default([]) | selectattr('name', 'eq', '{part_name}') | first |"
                        " default(none)) if d else none %}{{ p.label | default('') if p else '' }}"
                    ),
                    "fstype": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}{{%"
                        f" set p = (d.partitions | default([]) | selectattr('name', 'eq', '{part_name}') | first |"
                        " default(none)) if d else none %}{{ p.fstype | default('Unknown') if p else 'Unknown' }}"
                    ),
                    "size_gb": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}{{%"
                        f" set p = (d.partitions | default([]) | selectattr('name', 'eq', '{part_name}') | first |"
                        " default(none)) if d else none %}{{ ((p.size_b | default(0)) / 1073741824) | round(1) if p"
                        " else 0 }}"
                    ),
                    "content": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}{{%"
                        f" set p = (d.partitions | default([]) | selectattr('name', 'eq', '{part_name}') | first |"
                        " default(none)) if d else none %}{{ p.content | default('unknown') if p else 'unknown'"
                        " }}"
                    ),
                    "encrypted": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}{{%"
                        f" set p = (d.partitions | default([]) | selectattr('name', 'eq', '{part_name}') | first |"
                        " default(none)) if d else none %}{{ p.get('encryption', {}).get('encrypted', false) if p"
                        " else false }}"
                    ),
                    "encryption_scheme": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}{{%"
                        f" set p = (d.partitions | default([]) | selectattr('name', 'eq', '{part_name}') | first |"
                        " default(none)) if d else none %}{{ p.get('encryption', {}).get('scheme', 'none') if p"
                        " else 'none' }}"
                    ),
                    "encryption_unlocked": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}{{%"
                        f" set p = (d.partitions | default([]) | selectattr('name', 'eq', '{part_name}') | first |"
                        " default(none)) if d else none %}{{ p.get('encryption', {}).get('unlocked', false) if p"
                        " else false }}"
                    ),
                    "type_name": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}{{%"
                        f" set p = (d.partitions | default([]) | selectattr('name', 'eq', '{part_name}') | first |"
                        " default(none)) if d else none %}{{ p.type_name | default('') if p else '' }}"
                    ),
                    "type_guid": (
                        f"{{% set d = drives | selectattr('name', 'eq', '{drive_name}') | first | default(none) %}}{{%"
                        f" set p = (d.partitions | default([]) | selectattr('name', 'eq', '{part_name}') | first |"
                        " default(none)) if d else none %}{{ p.type_guid | default('') if p else '' }}"
                    ),
                },
            })

    return sensors


def generate_wifi_sensors(machine: dict, config: dict) -> list:
    """Generate WiFi-specific sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    wifi_config = config.get("wifi", {})
    if not wifi_config.get("enabled", False):
        return sensors

    iface_name = wifi_config.get("interface", "Wi-Fi")
    metrics = wifi_config.get("metrics", [])

    if "essid" in metrics:
        sensors.append({
            "name": f"{name} WiFi Network",
            "unique_id": generate_uuid(f"{slug}_wifi_network"),
            "availability": "{{ available }}",
            "state": (
                f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                "{{ iface.wifi.essid | default('Not Connected') if iface and iface.wifi else 'Not Connected' }}"
            ),
            "icon": "mdi:wifi",
        })

    if "signal_pct" in metrics:
        sensors.append({
            "name": f"{name} WiFi Signal",
            "unique_id": generate_uuid(f"{slug}_wifi_signal"),
            "availability": "{{ available }}",
            "state": (
                f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                "{{ (iface.wifi.signal_pct | default(0)) | int if iface and iface.wifi else 0 }}"
            ),
            "icon": "mdi:wifi",
            "unit_of_measurement": "%",
            "state_class": "measurement",
        })

    if "signal_dbm" in metrics:
        sensors.append({
            "name": f"{name} WiFi Signal dBm",
            "unique_id": generate_uuid(f"{slug}_wifi_signal_dbm"),
            "availability": "{{ available }}",
            "state": (
                f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                "{{ (iface.wifi.signal_dbm | default(-100)) | int if iface and iface.wifi else -100 }}"
            ),
            "icon": "mdi:wifi",
            "unit_of_measurement": "dBm",
            "state_class": "measurement",
            "device_class": "signal_strength",
        })

    if "channel" in metrics:
        sensors.append({
            "name": f"{name} WiFi Channel",
            "unique_id": generate_uuid(f"{slug}_wifi_channel"),
            "availability": "{{ available }}",
            "state": (
                f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                "{{ (iface.wifi.channel | default(0)) | int if iface and iface.wifi else 0 }}"
            ),
            "icon": "mdi:wifi",
            "state_class": "measurement",
        })

    if "bitrate_mbps" in metrics:
        sensors.append({
            "name": f"{name} WiFi Bitrate",
            "unique_id": generate_uuid(f"{slug}_wifi_bitrate"),
            "availability": "{{ available }}",
            "state": (
                f"{{% set iface = ifaces | selectattr('name', 'eq', '{iface_name}') | first | default(none) %}}"
                "{{ (iface.wifi.bitrate_mbps | default(0)) | round(0) | int if iface and iface.wifi else 0 }}"
            ),
            "icon": "mdi:speedometer",
            "unit_of_measurement": "Mbit/s",
            "device_class": "data_rate",
            "state_class": "measurement",
        })

    return sensors


def generate_opnsense_sensors(machine: dict, config: dict) -> list:
    """Generate OPNsense-specific sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    opn_config = config.get("opnsense", {})
    if not opn_config.get("enabled", False):
        return sensors

    metrics = opn_config.get("metrics", [])

    if "plugins_count" in metrics:
        sensors.append({
            "name": f"{name} Plugins Count",
            "unique_id": generate_uuid(f"{slug}_plugins_count"),
            "availability": "{{ available }}",
            "state": "{{ opnsense_plugins | length }}",
            "icon": "mdi:puzzle",
            "state_class": "measurement",
        })

    return sensors


def generate_zenarmor_sensors(machine: dict, config: dict) -> list:
    """Generate Zenarmor (Sensei) sensors."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    za_config = config.get("zenarmor", {})
    if not za_config.get("enabled", False):
        return sensors

    metrics = za_config.get("metrics", [])

    if "cloud_running" in metrics:
        sensors.append({
            "name": f"{name} Zenarmor Cloud",
            "unique_id": generate_uuid(f"{slug}_zenarmor_cloud"),
            "availability": "{{ available }}",
            "state": "{{ 'Running' if zenarmor.cloud_running else 'Stopped' }}",
            "icon": "mdi:cloud-check",
        })

    if "engine_running" in metrics:
        sensors.append({
            "name": f"{name} Zenarmor Engine",
            "unique_id": generate_uuid(f"{slug}_zenarmor_engine"),
            "availability": "{{ available }}",
            "state": "{{ 'Running' if zenarmor.engine_running else 'Stopped' }}",
            "icon": "mdi:engine",
        })

    return sensors


def generate_backup_provider_sensors(machine: dict, config: dict) -> list:
    """Generate backup provider sensors (Borg, Restic, etc.)."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    backup_config = config.get("backup_providers", {})
    if not backup_config.get("enabled", False):
        return sensors

    includes = backup_config.get("include", [])

    for provider in includes:
        provider_name = provider.get("name", "")
        display = provider.get("display_name", provider_name)
        provider_slug = slugify(display)

        # Backup status sensor with detailed attributes
        sensors.append({
            "name": f"{name} {display} Backup",
            "unique_id": generate_uuid(f"{slug}_{provider_slug}_backup"),
            "availability": "{{ available }}",
            "state": (
                f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                "{% if bp %}"
                "{% if bp.ok %}OK{% else %}Error{% endif %}"
                "{% else %}Unknown{% endif %}"
            ),
            "icon": "mdi:backup-restore",
            "attributes": {
                "name": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.name | default('Unknown') if bp else 'Unknown' }}"
                ),
                "type": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.type | default('Unknown') if bp else 'Unknown' }}"
                ),
                "repo": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.repo | default('Unknown') if bp else 'Unknown' }}"
                ),
                "ok": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.ok | default(false) if bp else false }}"
                ),
                "last_run": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{% if bp and bp.last_run_ts %}"
                    "{{ (bp.last_run_ts | as_datetime).strftime('%Y-%m-%d %H:%M:%S') }}"
                    "{% else %}Never{% endif %}"
                ),
                "last_run_ago": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{% if bp and bp.last_run_ts %}"
                    "{{ (bp.last_run_ts | as_datetime | as_local) | relative_time }}"
                    "{% else %}Never{% endif %}"
                ),
                "last_success": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{% if bp and bp.last_success_ts %}"
                    "{{ (bp.last_success_ts | as_datetime).strftime('%Y-%m-%d %H:%M:%S') }}"
                    "{% else %}Never{% endif %}"
                ),
                "last_status": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.last_status | default('unknown') if bp else 'unknown' }}"
                ),
                "last_error": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.last_error | default('') if bp else '' }}"
                ),
                "duration_s": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.duration_s | default(0) if bp else 0 }}"
                ),
                "bytes_added": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.bytes_added | default(0) if bp else 0 }}"
                ),
                "repo_size_b": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.repo_size_b | default(0) if bp else 0 }}"
                ),
                "compression": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.compression | default('Unknown') if bp else 'Unknown' }}"
                ),
                "encryption": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.encryption | default('Unknown') if bp else 'Unknown' }}"
                ),
                "snapshots": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.retention.snapshots | default(0) if bp and bp.retention else 0 }}"
                ),
                "retention_policy": (
                    f"{{% set bp = backup_providers | selectattr('name', 'eq', '{provider_name}') | first | default(none) %}}"
                    "{{ bp.retention.policy | default('Unknown') if bp and bp.retention else 'Unknown' }}"
                ),
            },
        })

    return sensors


def generate_binary_sensors(machine: dict, config: dict) -> list:
    """Generate binary sensors for health status."""
    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    sensors = []

    health_config = config.get("health", {})
    if health_config.get("enabled", False):
        # Overall Status OK
        sensors.append({
            "name": f"{name} Overall Status OK",
            "unique_id": generate_uuid(f"{slug}_overall_status_ok"),
            "availability": "{{ available }}",
            "state": "{{ health.overall_ok | default(false) }}",
            "icon": "mdi:check-circle",
        })
        # Status Alarm (inverse - 'on' when there are issues)
        sensors.append({
            "name": f"{name} Status Alarm",
            "unique_id": generate_uuid(f"{slug}_status_alarm"),
            "availability": "{{ available }}",
            "state": "{{ not (health.overall_ok | default(true)) }}",
            "device_class": "problem",
        })

    services_config = config.get("services", {})
    if services_config.get("enabled", False):
        includes = services_config.get("include", [])
        if includes:
            service_names = "', '".join(includes)
            # Services OK - all tracked services are running
            sensors.append({
                "name": f"{name} Services OK",
                "unique_id": generate_uuid(f"{slug}_services_ok"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set tracked = ['{service_names}'] %}}{{% set svc_list = health.services | default([]) %}}{{{{"
                    " svc_list | selectattr('name', 'in', tracked) | selectattr('ok', 'eq', false) | list | length =="
                    " 0 }}"
                ),
                "icon": "mdi:check-circle",
            })
            # Display Services - 'on' when there are stopped services to show
            sensors.append({
                "name": f"{name} Display Services",
                "unique_id": generate_uuid(f"{slug}_display_services"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set tracked = ['{service_names}'] %}}{{% set svc_list = health.services | default([]) %}}{{{{"
                    " svc_list | selectattr('name', 'in', tracked) | selectattr('ok', 'eq', false) | list | length > 0"
                    " }}"
                ),
                "icon": "mdi:cog-off",
            })
        else:
            sensors.append({
                "name": f"{name} Services OK",
                "unique_id": generate_uuid(f"{slug}_services_ok"),
                "availability": "{{ available }}",
                "state": "{{ (health.services | default([]) | selectattr('ok', 'eq', false) | list | length) == 0 }}",
                "icon": "mdi:check-circle",
            })
            sensors.append({
                "name": f"{name} Display Services",
                "unique_id": generate_uuid(f"{slug}_display_services"),
                "availability": "{{ available }}",
                "state": "{{ (health.services | default([]) | selectattr('ok', 'eq', false) | list | length) > 0 }}",
                "icon": "mdi:cog-off",
            })

        # Generate individual service binary sensors (for auto-entities)
        for service in includes:
            service_slug = slugify(service)
            sensors.append({
                "name": f"{name} Service {service}",
                "unique_id": generate_uuid(f"{slug}_service_{service_slug}"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set svc = health.services | default([]) | selectattr('name', 'eq', '{service}') | first |"
                    " default(none) %}{{ svc.ok | default(false) if svc else false }}"
                ),
                "icon": "mdi:cog",
            })

    containers_config = config.get("containers", {})
    if containers_config.get("enabled", False):
        includes = containers_config.get("include", [])
        if includes:
            container_names = "', '".join(includes)
            # Containers OK
            sensors.append({
                "name": f"{name} Containers OK",
                "unique_id": generate_uuid(f"{slug}_containers_ok"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set tracked = ['{container_names}'] %}}{{% set ctr_list = health.containers | default([])"
                    " %}{{ ctr_list | selectattr('name', 'in', tracked) | selectattr('ok', 'eq', false) | list |"
                    " length == 0 }}"
                ),
                "icon": "mdi:docker",
            })
            # Display Containers - 'on' when there are stopped containers to show
            sensors.append({
                "name": f"{name} Display Containers",
                "unique_id": generate_uuid(f"{slug}_display_containers"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set tracked = ['{container_names}'] %}}{{% set ctr_list = health.containers | default([])"
                    " %}{{ ctr_list | selectattr('name', 'in', tracked) | selectattr('ok', 'eq', false) | list |"
                    " length > 0 }}"
                ),
                "icon": "mdi:server-off",
            })
        else:
            sensors.append({
                "name": f"{name} Containers OK",
                "unique_id": generate_uuid(f"{slug}_containers_ok"),
                "availability": "{{ available }}",
                "state": "{{ (health.containers | default([]) | selectattr('ok', 'eq', false) | list | length) == 0 }}",
                "icon": "mdi:docker",
            })
            sensors.append({
                "name": f"{name} Display Containers",
                "unique_id": generate_uuid(f"{slug}_display_containers"),
                "availability": "{{ available }}",
                "state": "{{ (health.containers | default([]) | selectattr('ok', 'eq', false) | list | length) > 0 }}",
                "icon": "mdi:server-off",
            })

        # Generate individual container binary sensors (for auto-entities)
        for container in includes:
            container_slug = slugify(container)
            sensors.append({
                "name": f"{name} Container {container}",
                "unique_id": generate_uuid(f"{slug}_container_{container_slug}"),
                "availability": "{{ available }}",
                "state": (
                    f"{{% set ctr = health.containers | default([]) | selectattr('name', 'eq', '{container}') | first |"
                    " default(none) %}{{ ctr.ok | default(false) if ctr else false }}"
                ),
                "icon": "mdi:server",
            })

    return sensors


def generate_ui_sensors(machine_config: dict) -> list:
    """Generate ui_* sensor definitions for dashboard display.

    This generates UI sensors needed for both the machine-specific view
    and the overview dashboard. Each block can include:
    - entity: Primary entity to track
    - triggers: Additional entities to trigger updates (optional)
    - name: UI sensor name
    - app: App name matching jinja template 'levels' dictionaries
    - options: Additional options for the jinja macros
    - info: Jinja template for detailed info attribute (optional)

    App names must match keys in the jinja template 'levels' dictionaries:
    - none.jinja: cpu_utilization, memory_utilization, disk_utilization, cpu_load, count_pending
    - duration.jinja: uptime, latency
    - temperature.jinja: cpu, ambient, dew_point
    - binary.jinja: alarm, online, running, problem
    """
    machine = machine_config["machine"]
    sections = machine_config.get("sections", {})
    dashboard = machine_config.get("dashboard", {})
    overview = dashboard.get("overview", {})

    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    name = machine["name"]
    telemetry_sensor = machine["telemetry_sensor"]
    blocks = []

    cpu_config = sections.get("cpu", {})
    mem_config = sections.get("memory", {})
    cpu_metrics = cpu_config.get("metrics", [])

    # CPU Utilization (for badges) - app matches none.jinja levels
    blocks.append({
        "entity": f"sensor.{entity_prefix}_cpu_utilization",
        "name": f"ui_{slug}_cpu_utilization",
        "app": "cpu_utilization",
    })

    # CPU Utilization with Load (for overview cards)
    if "load_1m" in cpu_metrics:
        blocks.append({
            "entity": f"sensor.{entity_prefix}_cpu_utilization",
            "triggers": [telemetry_sensor, f"sensor.{entity_prefix}_cpu_load_1m"],
            "name": f"ui_{slug}_cpu_utilization_load",
            "app": "cpu_utilization",
            "options": {"load": f"sensor.{entity_prefix}_cpu_load_1m"},
        })
    else:
        blocks.append({
            "entity": f"sensor.{entity_prefix}_cpu_utilization",
            "triggers": [telemetry_sensor],
            "name": f"ui_{slug}_cpu_utilization_load",
            "app": "cpu_utilization",
        })

    # CPU Load with detailed info
    if "load_1m" in cpu_metrics:
        cores_sensor = f"sensor.{entity_prefix}_cpu_logical_cores" if "num_logical_cores" in cpu_metrics else None
        triggers = [
            f"sensor.{entity_prefix}_cpu_load_5m",
            f"sensor.{entity_prefix}_cpu_load_15m",
        ]
        if cores_sensor:
            triggers.append(cores_sensor)
        blocks.append({
            "entity": f"sensor.{entity_prefix}_cpu_load_1m",
            "triggers": triggers,
            "name": f"ui_{slug}_cpu_load_1m",
            "app": "cpu_load",
            "options": {"cores": cores_sensor} if cores_sensor else {},
            "info": (
                "{%- set m1 = states('sensor."
                + entity_prefix
                + "_cpu_load_1m')|float(0) -%}{%- set m5 = states('sensor."
                + entity_prefix
                + "_cpu_load_5m')|float(0) -%}{%- set m15 = states('sensor."
                + entity_prefix
                + "_cpu_load_15m')|float(0) -%}"
                + ("{%- set c = states('" + cores_sensor + "')|int(0) -%}" if cores_sensor else "")
                + "{{- '1m: ' ~ m1 ~ ' • 5m: ' ~ m5 ~ ' • 15m: ' ~ m15"
                + (" ~ ' • ' ~ c ~ ' cores'" if cores_sensor else "")
                + " -}}"
            ),
        })

    # Memory Percent with detailed info
    mem_metrics = mem_config.get("metrics", [])
    has_mem_details = all(m in mem_metrics for m in ["system.load_pct", "system.used_b", "system.total_b"])
    has_swap_details = all(m in mem_metrics for m in ["virtual.load_pct", "virtual.used_b", "virtual.total_b"])
    if "system.load_pct" in mem_metrics:
        triggers = []
        options = {}
        if "system.used_b" in mem_metrics:
            triggers.append(f"sensor.{entity_prefix}_memory_used")
            options["used"] = f"sensor.{entity_prefix}_memory_used"
        if "system.total_b" in mem_metrics:
            triggers.append(f"sensor.{entity_prefix}_memory_total")
        if "system.available_b" in mem_metrics:
            triggers.append(f"sensor.{entity_prefix}_memory_available")

        block = {
            "entity": f"sensor.{entity_prefix}_memory_percent",
            "name": f"ui_{slug}_memory_percent",
            "app": "memory_utilization",
        }
        if triggers:
            block["triggers"] = triggers
        if options:
            block["options"] = options
        if has_mem_details:
            block["info"] = (
                "{%- from 'units/base.jinja' import u_humanize_entity -%}{%- set mem_used = u_humanize_entity('sensor."
                + entity_prefix
                + "_memory_used') -%}{%- set mem_total = u_humanize_entity('sensor."
                + entity_prefix
                + "_memory_total') -%}{%- set mem_free = u_humanize_entity('sensor."
                + entity_prefix
                + "_memory_available') -%}{{- 'Used: ' ~ mem_used ~ ' / ' ~ mem_total ~ '\\nFree: ' ~ mem_free -}}"
            )
        blocks.append(block)

    if "virtual.load_pct" in mem_metrics:
        triggers = []
        options = {}
        if "virtual.used_b" in mem_metrics:
            triggers.append(f"sensor.{entity_prefix}_swap_used")
            options["used"] = f"sensor.{entity_prefix}_swap_used"
        if "virtual.total_b" in mem_metrics:
            triggers.append(f"sensor.{entity_prefix}_swap_total")
        if "virtual.available_b" in mem_metrics:
            triggers.append(f"sensor.{entity_prefix}_swap_available")

        block = {
            "entity": f"sensor.{entity_prefix}_swap_percent",
            "name": f"ui_{slug}_swap_percent",
            "app": "swap_utilization",
        }
        if triggers:
            block["triggers"] = triggers
        if options:
            block["options"] = options
        if has_swap_details:
            block["info"] = (
                "{%- from 'units/base.jinja' import u_humanize_entity -%}{%- set mem_used = u_humanize_entity('sensor."
                + entity_prefix
                + "_swap_used') -%}{%- set mem_total = u_humanize_entity('sensor."
                + entity_prefix
                + "_swap_total') -%}{%- set mem_free = u_humanize_entity('sensor."
                + entity_prefix
                + "_swap_available') -%}{{- 'Used: ' ~ mem_used ~ ' / ' ~ mem_total ~ '\\nFree: ' ~ mem_free -}}"
            )
        blocks.append(block)

    # Uptime - app matches duration.jinja levels
    blocks.append({
        "entity": f"sensor.{entity_prefix}_uptime_s",
        "name": f"ui_{slug}_uptime_s",
        "app": "uptime",
        "options": {"device_class": "duration", "uom": "s"},
    })

    # Updates Pending - app matches none.jinja levels
    blocks.append({
        "entity": f"sensor.{entity_prefix}_updates_pending",
        "name": f"ui_{slug}_updates_pending",
        "app": "count_pending",
    })

    # Status Alarm (for overview status card) - with summary reference
    blocks.append({
        "entity": f"binary_sensor.{entity_prefix}_status_alarm",
        "triggers": [telemetry_sensor, f"sensor.{entity_prefix}_overall_status_summary"],
        "name": f"ui_{slug}_status_alarm",
        "app": "alarm",
        "options": {
            "device_class": "binary",
            "summary": f"sensor.{entity_prefix}_overall_status_summary",
        },
    })

    # CPU Temp - use overview config if available, else default
    temp_suffix = overview.get("temp_suffix", "cpu_temp")
    if cpu_config.get("enabled", False) and "temp_c" in cpu_metrics:
        blocks.append({
            "entity": f"sensor.{entity_prefix}_{temp_suffix}",
            "name": f"ui_{slug}_{temp_suffix}",
            "app": "cpu",
            "options": {"device_class": "temperature"},
        })

    # Filesystem sensors from overview config - with detailed info
    fs_config = sections.get("filesystems", {})
    fs_includes = fs_config.get("include", [])
    for fs in overview.get("filesystems", []):
        fs_slug = fs.get("slug", "")
        if fs_slug:
            # Check if we have the related sensors
            triggers = [
                f"sensor.{entity_prefix}_fs_{fs_slug}_used",
                f"sensor.{entity_prefix}_fs_{fs_slug}_total",
            ]
            block = {
                "entity": f"sensor.{entity_prefix}_fs_{fs_slug}_percent",
                "triggers": triggers,
                "name": f"ui_{slug}_fs_{fs_slug}_percent",
                "app": "disk_utilization",
                "options": {"free": f"sensor.{entity_prefix}_fs_{fs_slug}_free"},
                "info": (
                    "{%- from 'units/base.jinja' import u_humanize_entity -%}{%- set total = u_humanize_entity('sensor."
                    + entity_prefix
                    + "_fs_"
                    + fs_slug
                    + "_total') -%}{%- set used = u_humanize_entity('sensor."
                    + entity_prefix
                    + "_fs_"
                    + fs_slug
                    + "_used') -%}{{- 'Total: ' ~ total ~ ' • Used: ' ~ used -}}"
                ),
            }
            blocks.append(block)

    # Filesystem UI sensors from sections config (for detail page) - with extra_attrs
    fs_metrics = fs_config.get("metrics", [])
    for fs in fs_includes:
        label = fs.get("label", "")
        mountpoint = fs.get("mountpoint", "")
        display = fs.get("display_name", (label or mountpoint).title())
        fs_slug = slugify(display)

        # Determine match criteria
        if label:
            match_attr = "label"
            match_val = label
        else:
            match_attr = "mountpoint"
            match_val = mountpoint

        percent_sensor = f"sensor.{entity_prefix}_fs_{fs_slug}_percent"
        blocks.append({
            "entity": percent_sensor,
            "triggers": [
                telemetry_sensor,
                f"sensor.{entity_prefix}_fs_{fs_slug}_used",
                f"sensor.{entity_prefix}_fs_{fs_slug}_total",
            ],
            "name": f"ui_{slug}_fs_{fs_slug}",
            "app": "disk_utilization",
            "extra_attrs": {
                "fs_icon": (
                    "{%- set telemetry = state_attr('" + telemetry_sensor + "', 'filesystems') | default([]) -%}"
                    "{%- set drives = state_attr('" + telemetry_sensor + "', 'drives') | default([]) -%}"
                    f"{{%- set fs = telemetry | selectattr('{match_attr}', 'eq', '{match_val}') | first | default(none) -%}}"
                    "{%- set drive_name = fs.backing_blockdev.drive_name | default('') if fs and fs.backing_blockdev is defined else '' -%}"
                    "{%- set drive = drives | selectattr('name', 'eq', drive_name) | first | default(none) if drive_name else none -%}"
                    "{%- set partition = none -%}"
                    "{%- if drive and drive.partitions is defined -%}"
                    "{%- for p in drive.partitions -%}"
                    "{%- if p.label is defined and p.label == (fs.label | default('')) -%}"
                    "{%- set partition = p -%}"
                    "{%- endif -%}"
                    "{%- endfor -%}"
                    "{%- endif -%}"
                    "{%- set encrypted = (fs.encrypted | default(false)) or (partition.encryption.encrypted | default(false) if partition and partition.encryption is defined else false) if fs else false -%}"
                    "{{- 'mdi:folder-lock' if encrypted else 'mdi:folder' -}}"
                ),
                "fs_color": (
                    "{%- set pct = states('" + percent_sensor + "') | float(0) -%}"
                    "{%- if pct > 95 -%}#dc2626{%- elif pct > 85 -%}#f97316{%- elif pct > 70 -%}#eab308{%- else -%}#22c55e{%- endif -%}"
                ),
                "fs_secondary": (
                    "{%- from 'units/base.jinja' import u_humanize_value -%}"
                    "{%- set telemetry = state_attr('" + telemetry_sensor + "', 'filesystems') | default([], true) -%}"
                    "{%- set drives = state_attr('" + telemetry_sensor + "', 'drives') | default([], true) -%}"
                    f"{{%- set fs = telemetry | selectattr('{match_attr}', 'eq', '{match_val}') | first | default(none) -%}}"
                    "{%- set used_b = fs.used_b | default(0, true) if fs else 0 -%}"
                    "{%- set avail_b = fs.available_b | default(0, true) if fs else 0 -%}"
                    "{%- set total_b = used_b + avail_b -%}"
                    "{%- set pct = ((used_b / total_b) * 100) | round(0) | int if total_b > 0 else 0 -%}"
                    "{%- set fmt = fs.format | default('Unknown', true) if fs else 'Unknown' -%}"
                    "{%- set mnt = fs.mountpoint | default('Unknown', true) if fs else 'Unknown' -%}"
                    "{%- set fs_uuid = fs.uuid | default('', true) if fs else '' -%}"
                    "{%- set read_rate = fs.read_rate_bps | default(0, true) if fs else 0 -%}"
                    "{%- set write_rate = fs.write_rate_bps | default(0, true) if fs else 0 -%}"
                    "{%- set drive_name = fs.backing_blockdev.drive_name | default('', true) if fs and fs.backing_blockdev is defined else '' -%}"
                    "{%- set drive = drives | selectattr('name', 'eq', drive_name) | first | default(none) if drive_name else none -%}"
                    # Find partition by drive letter (more reliable on Windows)
                    "{%- set fs_drive_letter = mnt | replace(':\\\\', '') | replace(':/', '') if mnt and ':' in mnt else '' -%}"
                    "{%- set partition = none -%}"
                    "{%- if drive and drive.partitions is defined -%}"
                    "{%- for p in drive.partitions -%}"
                    "{%- if (fs_drive_letter and p.drive_letter | default('') == fs_drive_letter) or (p.label | default('') == (fs.label | default(''))) -%}"
                    "{%- set partition = p -%}"
                    "{%- endif -%}"
                    "{%- endfor -%}"
                    "{%- endif -%}"
                    # Check encryption from filesystem or partition
                    "{%- set fs_encrypted = fs.encrypted | default(false, true) if fs else false -%}"
                    "{%- set part_encrypted = partition.encryption.encrypted | default(false, true) if partition and partition.encryption is defined else false -%}"
                    "{%- set encrypted = fs_encrypted or part_encrypted -%}"
                    "{%- set enc_scheme = partition.encryption.scheme | default('', true) if partition and partition.encryption is defined else '' -%}"
                    "{%- set ns = namespace(lines=[]) -%}"
                    "{%- set ns.lines = ns.lines + [u_humanize_value(used_b, 'B') ~ ' / ' ~ u_humanize_value(total_b, 'B') ~ ' (' ~ pct ~ '% used)'] -%}"
                    "{%- set ns.lines = ns.lines + [fmt ~ ' | ' ~ mnt] -%}"
                    "{%- if read_rate > 0 or write_rate > 0 -%}"
                    "{%- set ns.lines = ns.lines + ['R: ' ~ u_humanize_value(read_rate, 'B') ~ '/s | W: ' ~ u_humanize_value(write_rate, 'B') ~ '/s'] -%}"
                    "{%- endif -%}"
                    "{%- if encrypted -%}"
                    "{%- set enc_text = 'Encrypted' ~ (' (' ~ enc_scheme ~ ')' if enc_scheme else '') -%}"
                    "{%- set ns.lines = ns.lines + [enc_text] -%}"
                    "{%- endif -%}"
                    "{%- if fs_uuid -%}"
                    "{%- set ns.lines = ns.lines + ['UUID: ' ~ fs_uuid] -%}"
                    "{%- endif -%}"
                    "{{- ns.lines | join('\\n') -}}"
                ),
            },
        })

    # GPU sensor - generate if enabled in overview OR sections
    # Track which sensors we've already generated to avoid duplicates
    generated_sensors = set()

    gpu_overview = overview.get("gpu", {})
    if gpu_overview.get("enabled", False):
        gpu_suffix = gpu_overview.get("suffix", "gpu_utilization")
        blocks.append({
            "entity": f"sensor.{entity_prefix}_{gpu_suffix}",
            "name": f"ui_{slug}_{gpu_suffix}",
            "app": "cpu_utilization",
        })
        generated_sensors.add(f"ui_{slug}_{gpu_suffix}")

    # Also generate from sections.gpus if not already generated
    gpu_sections = sections.get("gpus", {})
    if gpu_sections.get("enabled", False):
        sensor_name = f"ui_{slug}_gpu_utilization"
        if sensor_name not in generated_sensors:
            blocks.append({
                "entity": f"sensor.{entity_prefix}_gpu_utilization",
                "name": sensor_name,
                "app": "cpu_utilization",
            })
            generated_sensors.add(sensor_name)

        # GPU Temp sensor
        gpu_metrics = gpu_sections.get("metrics", [])
        if "temp_c" in gpu_metrics:
            blocks.append({
                "entity": f"sensor.{entity_prefix}_gpu_temp",
                "name": f"ui_{slug}_gpu_temp",
                "app": "cpu",
                "options": {"device_class": "temperature"},
            })

        # GPU Engines sensor (for mini-graph-card icon color)
        if "engines" in gpu_metrics:
            blocks.append({
                "entity": f"sensor.{entity_prefix}_gpu_engine_gpu_core",
                "name": f"ui_{slug}_gpu_engines",
                "app": "cpu_utilization",
            })

    # Drive temp sensors for each drive
    drv_sections = sections.get("drives", {})
    if drv_sections.get("enabled", False):
        drv_metrics = drv_sections.get("metrics", [])
        if "temp_c" in drv_metrics:
            for drive in drv_sections.get("include", []):
                drive_name = drive.get("name", "")
                display = drive.get("display_name", drive_name)
                drive_slug = slugify(display)
                blocks.append({
                    "entity": f"sensor.{entity_prefix}_{drive_slug}_temp",
                    "name": f"ui_{slug}_{drive_slug}_temp",
                    "app": "cpu",
                    "options": {"device_class": "temperature"},
                })

        # Drive status UI sensor with comprehensive info
        if "status" in drv_metrics:
            for drive in drv_sections.get("include", []):
                drive_name = drive.get("name", "")
                display = drive.get("display_name", drive_name)
                drive_slug = slugify(display)
                status_sensor = f"sensor.{entity_prefix}_{drive_slug}_status"
                blocks.append({
                    "entity": status_sensor,
                    "triggers": [
                        telemetry_sensor,
                        f"sensor.{entity_prefix}_{drive_slug}_temp",
                    ],
                    "name": f"ui_{slug}_{drive_slug}_status",
                    "app": "connectivity",
                    "options": {"attr": "health", "device_class": "binary"},
                    "info": (
                        "{%- set s = '" + status_sensor + "' -%}"
                        "{%- set health = state_attr(s, 'health') | default('Unknown', true) -%}"
                        "{%- set temp = state_attr(s, 'temp_c') | default(0, true) -%}"
                        "{%- set wear = state_attr(s, 'wear_level_pct') | default(100, true) -%}"
                        "{%- set used_pct = state_attr(s, 'used_pct') | default(0, true) | float -%}"
                        "{%- set used_gb = state_attr(s, 'used_gb') | default(0, true) | float -%}"
                        "{%- set avail_gb = state_attr(s, 'available_gb') | default(0, true) | float -%}"
                        "{%- set total_read = state_attr(s, 'total_read_tb') | default(0, true) | float -%}"
                        "{%- set total_write = state_attr(s, 'total_write_tb') | default(0, true) | float -%}"
                        "{%- set read_rate = state_attr(s, 'read_rate_mbps') | default(0, true) | float -%}"
                        "{%- set write_rate = state_attr(s, 'write_rate_mbps') | default(0, true) | float -%}"
                        "{%- set partitions = state_attr(s, 'partitions') | default([], true) -%}"
                        "{%- set lines = [] -%}"
                        "{%- set lines = lines + ['Health: ' ~ health ~ ' | Wear: ' ~ wear ~ '%'] -%}"
                        "{%- set lines = lines + ['Temp: ' ~ temp ~ '°C'] -%}"
                        "{%- set lines = lines + ['Used: ' ~ used_gb | round(0) ~ ' GB / ' ~ (used_gb + avail_gb) | round(0) ~ ' GB (' ~ used_pct | round(0) ~ '%)'] -%}"
                        "{%- set lines = lines + ['Total R/W: ' ~ total_read ~ ' / ' ~ total_write ~ ' TB'] -%}"
                        "{%- if read_rate > 0 or write_rate > 0 -%}"
                        "{%- set lines = lines + ['Activity: R ' ~ read_rate ~ ' / W ' ~ write_rate ~ ' MB/s'] -%}"
                        "{%- endif -%}"
                        "{%- if partitions -%}"
                        "{%- set part_names = [] -%}"
                        "{%- for p in partitions -%}"
                        "{%- set pn = (p.label | default('')) or (p.type_name | default('')) or (p.name | default('')) or ('Part ' ~ (p.number | default(loop.index))) -%}"
                        "{%- set part_names = part_names + [pn] -%}"
                        "{%- endfor -%}"
                        "{%- set lines = lines + ['Partitions: ' ~ part_names | join(', ')] -%}"
                        "{%- endif -%}"
                        "{{- lines | join('\\n') -}}"
                    ),
                    "extra_attrs": {
                        "drive_icon": (
                            "{%- set health = state_attr('" + status_sensor + "', 'health') | default('Unknown') | lower -%}"
                            "{{- 'mdi:harddisk' if health in ['passed', 'healthy'] else 'mdi:harddisk-remove' -}}"
                        ),
                        "drive_color": (
                            "{%- set health = state_attr('" + status_sensor + "', 'health') | default('Unknown', true) | lower -%}"
                            "{%- set wear = state_attr('" + status_sensor + "', 'wear_level_pct') | default(0, true) | int -%}"
                            "{%- set temp = state_attr('" + status_sensor + "', 'temp_c') | default(0, true) | int -%}"
                            "{%- if health not in ['passed', 'healthy'] -%}#dc2626"
                            "{%- elif wear > 80 or temp > 70 -%}#f59e0b"
                            "{%- elif wear > 50 or temp > 60 -%}#eab308"
                            "{%- else -%}#22c55e{%- endif -%}"
                        ),
                        "drive_secondary": (
                            "{%- from 'units/base.jinja' import u_humanize_value -%}"
                            "{%- set s = '" + status_sensor + "' -%}"
                            "{%- set health = state_attr(s, 'health') | default('Unknown', true) -%}"
                            "{%- set wear = state_attr(s, 'wear_level_pct') | default(0, true) | int -%}"
                            "{%- set temp = state_attr(s, 'temp_c') | default(0, true) | int -%}"
                            "{%- set firmware = state_attr(s, 'firmware_version') | default('', true) -%}"
                            "{%- set listed_cap_b = (state_attr(s, 'listed_cap_gb') | default(0, true) | float) * 1073741824 -%}"
                            "{%- set used_b = (state_attr(s, 'used_gb') | default(0, true) | float) * 1073741824 -%}"
                            "{%- set avail_b = (state_attr(s, 'available_gb') | default(0, true) | float) * 1073741824 -%}"
                            "{%- set total_b = used_b + avail_b -%}"
                            "{%- set used_pct = state_attr(s, 'used_pct') | default(0, true) | round(0) | int -%}"
                            "{%- set total_read_b = (state_attr(s, 'total_read_tb') | default(0, true) | float) * 1099511627776 -%}"
                            "{%- set total_write_b = (state_attr(s, 'total_write_tb') | default(0, true) | float) * 1099511627776 -%}"
                            "{{- 'Health: ' ~ health ~ ' | Wear: ' ~ wear ~ '% | Temp: ' ~ temp ~ '°C\\n' -}}"
                            "{{- 'Listed: ' ~ u_humanize_value(listed_cap_b, 'B') ~ ' | Used: ' ~ u_humanize_value(used_b, 'B') ~ ' (' ~ used_pct ~ '%)\\n' -}}"
                            "{{- 'Lifetime R/W: ' ~ u_humanize_value(total_read_b, 'B') ~ ' / ' ~ u_humanize_value(total_write_b, 'B') -}}"
                            "{%- if firmware %}{{- '\\nFirmware: ' ~ firmware -}}{%- endif %}"
                        ),
                        "partitions_display": _build_partitions_display_template(
                            status_sensor, sections.get("partitions", {})
                        ),
                    },
                })

    # TPU sensor - generate if enabled in overview OR sections
    tpu_overview = overview.get("tpu", {})
    if tpu_overview.get("enabled", False):
        tpu_suffix = tpu_overview.get("suffix", "coral_tpu_temp")
        blocks.append({
            "entity": f"sensor.{entity_prefix}_{tpu_suffix}",
            "name": f"ui_{slug}_{tpu_suffix}",
            "app": "cpu",
            "options": {"device_class": "temperature"},
        })
        generated_sensors.add(f"ui_{slug}_{tpu_suffix}")

    # Also generate from sections.tpus if not already generated
    tpu_sections = sections.get("tpus", {})
    if tpu_sections.get("enabled", False):
        sensor_name = f"ui_{slug}_coral_tpu_temp"
        if sensor_name not in generated_sensors:
            blocks.append({
                "entity": f"sensor.{entity_prefix}_coral_tpu_temp",
                "name": sensor_name,
                "app": "cpu",
                "options": {"device_class": "temperature"},
            })

    # Network interface UI sensors
    net_config = sections.get("network", {})
    if net_config.get("enabled", False):
        for iface in net_config.get("include", []):
            iface_name = iface.get("name", "")
            display = iface.get("display_name", iface_name)
            iface_slug = slugify(display)
            # Detect if WiFi interface for icon selection
            is_wifi = "wifi" in display.lower() or "wi-fi" in iface_name.lower()
            # UI sensor tracks the Info sensor's carrier attribute for connectivity status
            info_sensor = f"sensor.{entity_prefix}_{iface_slug}_info"
            blocks.append({
                "entity": info_sensor,
                "triggers": [
                    telemetry_sensor,
                    f"sensor.{entity_prefix}_{iface_slug}_upload",
                    f"sensor.{entity_prefix}_{iface_slug}_download",
                ],
                "name": f"ui_{slug}_network_{iface_slug}",
                "app": "connectivity",
                "options": {"attr": "carrier", "device_class": "binary"},
                "info": (
                    "{%- set carrier = state_attr('" + info_sensor + "', 'carrier') | default(false, true) -%}"
                    "{%- set bad = ['n/a', 'unknown', 'unavailable', 'none', ''] -%}"
                    "{%- set mac = state_attr('" + info_sensor + "', 'mac') | default('', true) -%}"
                    "{%- set ipv4 = state_attr('" + info_sensor + "', 'ipv4') | default('', true) -%}"
                    "{%- set ipv6 = state_attr('" + info_sensor + "', 'ipv6') | default('', true) -%}"
                    "{%- set speed_mbps = state_attr('" + info_sensor + "', 'link_speed_mbps') | default(0, true) | float -%}"
                    "{%- set speed = ((speed_mbps / 1000) | round(1) ~ ' Gbps' if speed_mbps >= 1000 else (speed_mbps | int ~ ' Mbps')) if speed_mbps > 0 else none -%}"
                    "{%- set lines = [] -%}"
                    "{%- if mac and (mac | lower) not in bad -%}{%- set lines = lines + ['MAC: ' ~ mac] -%}{%- endif -%}"
                    "{%- if ipv4 and (ipv4 | lower) not in bad -%}{%- set lines = lines + ['IPv4: ' ~ ipv4] -%}{%- endif -%}"
                    "{%- if ipv6 and (ipv6 | lower) not in bad -%}{%- set lines = lines + ['IPv6: ' ~ ipv6] -%}{%- endif -%}"
                    "{%- if speed -%}{%- set lines = lines + ['Speed: ' ~ speed] -%}{%- endif -%}"
                    "{{- lines | join('\\n') if lines else ('Connected' if carrier else 'Disconnected') -}}"
                ),
                "extra_attrs": {
                    "iface_icon": (
                        "{{- 'mdi:wifi' if state_attr('" + info_sensor + "', 'carrier') else 'mdi:wifi-off' -}}"
                        if is_wifi else
                        "{{- 'mdi:lan-connect' if state_attr('" + info_sensor + "', 'carrier') else 'mdi:lan-disconnect' -}}"
                    ),
                    "iface_color": "{{- '#22c55e' if state_attr('" + info_sensor + "', 'carrier') else '#dc2626' -}}",
                },
            })

    # System UI sensor (host info card)
    blocks.append({
        "entity": telemetry_sensor,
        "triggers": [telemetry_sensor],
        "name": f"ui_{slug}_system",
        "app": "connectivity",
        "options": {"attr": "host", "device_class": "binary"},
        "extra_attrs": {
            "system_icon": (
                "{%- set host = state_attr('" + telemetry_sensor + "', 'host') | default({}) -%}"
                "{%- set chassis = (host['chassis_type'] | default('Desktop')) | lower -%}"
                "{%- set icons = {'notebook': 'mdi:laptop', 'laptop': 'mdi:laptop', 'desktop': 'mdi:desktop-tower', 'server': 'mdi:server', 'tablet': 'mdi:tablet'} -%}"
                "{{- icons.get(chassis, 'mdi:desktop-tower') -}}"
            ),
            "system_color": (
                "{%- set host = state_attr('" + telemetry_sensor + "', 'host') | default({}) -%}"
                "{%- set os = (host['system'] | default('')) | lower -%}"
                "{{- 'blue' if 'windows' in os else ('orange' if 'linux' in os else ('purple' if 'freebsd' in os else 'grey')) -}}"
            ),
            "system_primary": (
                "{%- set host = state_attr('" + telemetry_sensor + "', 'host') | default({}) -%}"
                "{{- host['name'] | default('Unknown') -}}"
            ),
            "system_secondary": (
                "{%- set h = state_attr('" + telemetry_sensor + "', 'host') | default({}) -%}"
                "{%- set model = h['model'] | default('Unknown') -%}"
                "{%- set serial = h['serial'] | default('N/A') -%}"
                "{%- set system = h['system'] | default('Unknown') -%}"
                "{%- set release = h['release'] | default('') -%}"
                "{%- set machine = h['machine'] | default('') -%}"
                "{%- set os_str = h['os'] | default('') -%}"
                "{%- set build = os_str.split('-')[2] if '-' in os_str else os_str -%}"
                "{{- model ~ ' (Serial: ' ~ serial ~ ')\\n' ~ system ~ ' ' ~ release ~ ' (' ~ machine ~ ')\\nBuild: ' ~ build -}}"
            ),
        },
    })

    # WiFi stats UI sensor
    wifi_config = sections.get("wifi", {})
    if wifi_config.get("enabled", False):
        blocks.append({
            "entity": f"sensor.{entity_prefix}_wifi_signal",
            "triggers": [
                telemetry_sensor,
                f"sensor.{entity_prefix}_wifi_network",
                f"sensor.{entity_prefix}_wifi_signal_dbm",
                f"sensor.{entity_prefix}_wifi_channel",
                f"sensor.{entity_prefix}_wifi_bitrate",
            ],
            "name": f"ui_{slug}_wifi_stats",
            "app": "connectivity",
            "options": {"device_class": "binary"},
            "extra_attrs": {
                "wifi_icon": (
                    "{%- set sig = states('sensor." + entity_prefix + "_wifi_signal') | int(0) -%}"
                    "{{- 'mdi:wifi-strength-4' if sig > 75 else 'mdi:wifi-strength-3' if sig > 50 else 'mdi:wifi-strength-2' if sig > 25 else 'mdi:wifi-strength-1' if sig > 0 else 'mdi:wifi-off' -}}"
                ),
                "wifi_color": (
                    "{%- set sig = states('sensor." + entity_prefix + "_wifi_signal') | int(0) -%}"
                    "{{- 'green' if sig > 60 else 'orange' if sig > 30 else 'red' -}}"
                ),
                "wifi_primary": (
                    "{{- states('sensor." + entity_prefix + "_wifi_network') | default('Not Connected') -}}"
                ),
                "wifi_secondary": (
                    "{%- set sig = states('sensor." + entity_prefix + "_wifi_signal') | default('?') -%}"
                    "{%- set dbm = states('sensor." + entity_prefix + "_wifi_signal_dbm') | default('?') -%}"
                    "{%- set ch = states('sensor." + entity_prefix + "_wifi_channel') | default('?') -%}"
                    "{%- set rate = states('sensor." + entity_prefix + "_wifi_bitrate') | default('?') -%}"
                    "{%- set auth = states('sensor." + entity_prefix + "_wifi_auth') | default('') -%}"
                    "{%- set radio = states('sensor." + entity_prefix + "_wifi_radio') | default('') -%}"
                    "{{- sig ~ '% (' ~ dbm ~ ' dBm) | Ch ' ~ ch ~ '\\n' ~ rate ~ ' Mbps' ~ (' | ' ~ radio if radio else '') ~ (' | ' ~ auth if auth else '') -}}"
                ),
            },
        })

    # Battery status UI sensor
    bat_config = sections.get("batteries", {})
    if bat_config.get("enabled", False):
        blocks.append({
            "entity": telemetry_sensor,
            "triggers": [telemetry_sensor],
            "name": f"ui_{slug}_battery_status",
            "app": "connectivity",
            "options": {"device_class": "binary"},
            "extra_attrs": {
                "battery_icon": (
                    "{%- set bats = state_attr('" + telemetry_sensor + "', 'batteries') | default([], true) -%}"
                    "{%- set b = bats[0] if bats and bats | length > 0 else none -%}"
                    "{%- set level = (b['charge_level_pct'] | default(0) | int) if b else 0 -%}"
                    "{%- set discharging = (b['discharging'] | default(false)) if b else false -%}"
                    "{%- if not b -%}mdi:battery-unknown"
                    "{%- elif discharging -%}mdi:battery-{{- (level // 10 * 10) | int -}}-bluetooth"
                    "{%- elif level >= 100 -%}mdi:battery-charging-100"
                    "{%- else -%}mdi:battery-charging-{{- (level // 10 * 10) | int -}}"
                    "{%- endif -%}"
                ),
                "battery_color": (
                    "{%- set bats = state_attr('" + telemetry_sensor + "', 'batteries') | default([], true) -%}"
                    "{%- set b = bats[0] if bats and bats | length > 0 else none -%}"
                    "{%- set level = (b['charge_level_pct'] | default(0) | int) if b else 0 -%}"
                    "{%- set discharging = (b['discharging'] | default(false)) if b else false -%}"
                    "{%- if not b -%}grey"
                    "{%- elif level <= 20 -%}red"
                    "{%- elif level <= 50 -%}orange"
                    "{%- elif discharging -%}yellow"
                    "{%- else -%}green"
                    "{%- endif -%}"
                ),
                "battery_primary": (
                    "{%- set bats = state_attr('" + telemetry_sensor + "', 'batteries') | default([], true) -%}"
                    "{%- set b = bats[0] if bats and bats | length > 0 else none -%}"
                    "{%- set level = (b['charge_level_pct'] | default(0) | int) if b else 0 -%}"
                    "{{- 'Battery (' ~ level ~ '%)' -}}"
                ),
                "battery_secondary": (
                    "{%- set bats = state_attr('" + telemetry_sensor + "', 'batteries') | default([], true) -%}"
                    "{%- set b = bats[0] if bats and bats | length > 0 else none -%}"
                    "{%- if not b -%}No battery data"
                    "{%- else -%}"
                    "{%- set discharging = b['discharging'] | default(false) -%}"
                    "{%- set power = b['power_w'] | default(0) | round(1) -%}"
                    "{%- set voltage = b['voltage_v'] | default(0) | round(2) -%}"
                    "{%- set current = b['current_a'] | default(0) | round(2) -%}"
                    "{%- set status = 'Discharging' if discharging else 'Charging' if power > 0 else 'Idle (Full)' -%}"
                    "{%- set ns = namespace(lines=[]) -%}"
                    "{%- set ns.lines = ns.lines + [status] -%}"
                    "{%- if power > 0 or voltage > 0 -%}"
                    "{%- set pv_line = (power | string ~ ' W') if power > 0 else '' -%}"
                    "{%- set pv_line = pv_line ~ (' | ' if pv_line and voltage > 0 else '') ~ (voltage | string ~ ' V' if voltage > 0 else '') -%}"
                    "{%- set ns.lines = ns.lines + [pv_line] if pv_line else ns.lines -%}"
                    "{%- endif -%}"
                    "{%- if current != 0 -%}"
                    "{%- set ns.lines = ns.lines + [current | abs | string ~ ' A ' ~ ('draw' if current < 0 else 'charge')] -%}"
                    "{%- endif -%}"
                    "{{- ns.lines | join('\\n') -}}"
                    "{%- endif -%}"
                ),
            },
        })

        # Battery health UI sensor
        blocks.append({
            "entity": telemetry_sensor,
            "triggers": [telemetry_sensor],
            "name": f"ui_{slug}_battery_health",
            "app": "connectivity",
            "options": {"device_class": "binary"},
            "extra_attrs": {
                "health_icon": (
                    "{%- set bats = state_attr('" + telemetry_sensor + "', 'batteries') | default([], true) -%}"
                    "{%- set b = bats[0] if bats and bats | length > 0 else none -%}"
                    "{%- set degradation = (b['degradation_pct'] | default(0) | float) if b else 0 -%}"
                    "{%- if not b -%}mdi:battery-unknown"
                    "{%- elif degradation < 10 -%}mdi:battery-heart-variant"
                    "{%- elif degradation < 20 -%}mdi:battery-heart-outline"
                    "{%- else -%}mdi:battery-alert-variant-outline"
                    "{%- endif -%}"
                ),
                "health_color": (
                    "{%- set bats = state_attr('" + telemetry_sensor + "', 'batteries') | default([], true) -%}"
                    "{%- set b = bats[0] if bats and bats | length > 0 else none -%}"
                    "{%- set degradation = (b['degradation_pct'] | default(0) | float) if b else 0 -%}"
                    "{%- if not b -%}grey"
                    "{%- elif degradation < 10 -%}green"
                    "{%- elif degradation < 20 -%}orange"
                    "{%- else -%}red"
                    "{%- endif -%}"
                ),
                "health_primary": (
                    "{%- set bats = state_attr('" + telemetry_sensor + "', 'batteries') | default([], true) -%}"
                    "{%- set b = bats[0] if bats and bats | length > 0 else none -%}"
                    "{%- set degradation = (b['degradation_pct'] | default(0) | float) if b else 0 -%}"
                    "{%- set health = (100 - degradation) | round(1) -%}"
                    "{{- 'Battery Health (' ~ health ~ '%)' -}}"
                ),
                "health_secondary": (
                    "{%- set bats = state_attr('" + telemetry_sensor + "', 'batteries') | default([], true) -%}"
                    "{%- set b = bats[0] if bats and bats | length > 0 else none -%}"
                    "{%- if not b -%}No battery data"
                    "{%- else -%}"
                    "{%- set degradation = b['degradation_pct'] | default(0) | float -%}"
                    "{%- set design_mwh = b['design_cap_mwh'] | default(0) | int -%}"
                    "{%- set full_mwh = b['full_cap_mwh'] | default(0) | int -%}"
                    "{%- set remain_mwh = b['remain_cap_mwh'] | default(0) | int -%}"
                    "{%- set design_wh = design_mwh / 1000 -%}"
                    "{%- set full_wh = full_mwh / 1000 -%}"
                    "{%- set remain_wh = remain_mwh / 1000 -%}"
                    "{%- set ns = namespace(lines=[]) -%}"
                    "{%- set ns.lines = ns.lines + [degradation | round(1) | string ~ '% wear'] -%}"
                    "{%- if design_wh > 0 or full_wh > 0 -%}"
                    "{%- set cap_line = full_wh | round(1) | string ~ ' / ' ~ design_wh | round(1) | string ~ ' Wh capacity' -%}"
                    "{%- set ns.lines = ns.lines + [cap_line] -%}"
                    "{%- endif -%}"
                    "{%- if remain_wh > 0 -%}"
                    "{%- set ns.lines = ns.lines + [remain_wh | round(1) | string ~ ' Wh remaining'] -%}"
                    "{%- endif -%}"
                    "{{- ns.lines | join('\\n') -}}"
                    "{%- endif -%}"
                ),
            },
        })

    # GPU load UI sensor
    gpu_sections = sections.get("gpus", {})
    if gpu_sections.get("enabled", False):
        blocks.append({
            "entity": telemetry_sensor,
            "triggers": [telemetry_sensor],
            "name": f"ui_{slug}_gpu_load",
            "app": "cpu_utilization",
            "extra_attrs": {
                "gpu_icon": "mdi:expansion-card",
                "gpu_color": (
                    "{%- set gpus = state_attr('" + telemetry_sensor + "', 'gpus') | default([], true) -%}"
                    "{%- set g = gpus[0] if gpus and gpus | length > 0 else none -%}"
                    "{%- set core = g['core'] | default({}) if g else {} -%}"
                    "{%- set load = core['load_pct'] | default(0) | float -%}"
                    "{%- if load > 90 -%}red"
                    "{%- elif load > 70 -%}orange"
                    "{%- elif load > 30 -%}yellow"
                    "{%- else -%}green"
                    "{%- endif -%}"
                ),
                "gpu_primary": (
                    "{%- set gpus = state_attr('" + telemetry_sensor + "', 'gpus') | default([], true) -%}"
                    "{%- set g = gpus[0] if gpus and gpus | length > 0 else none -%}"
                    "{%- set core = g['core'] | default({}) if g else {} -%}"
                    "{%- set load = core['load_pct'] | default(0) | round(0) | int -%}"
                    "{{- 'GPU (' ~ load ~ '%)' -}}"
                ),
                "gpu_secondary": (
                    "{%- set gpus = state_attr('" + telemetry_sensor + "', 'gpus') | default([], true) -%}"
                    "{%- set g = gpus[0] if gpus and gpus | length > 0 else none -%}"
                    "{%- if not g -%}No GPU data"
                    "{%- else -%}"
                    "{%- set temp = g['temp_c'] | default(0) | round(0) | int -%}"
                    "{%- set core = g['core'] | default({}) -%}"
                    "{%- set soc = g['soc'] | default({}) -%}"
                    "{%- set core_power = core['power_w'] | default(0) | round(1) -%}"
                    "{%- set soc_power = soc['power_w'] | default(0) | round(1) -%}"
                    "{%- set voltage = soc['voltage_v'] | default(0) | round(2) -%}"
                    "{%- set total_power = core_power + soc_power -%}"
                    "{%- set ns = namespace(lines=[]) -%}"
                    "{%- if temp > 0 -%}{%- set ns.lines = ns.lines + [temp | string ~ '°C'] -%}{%- endif -%}"
                    "{%- if total_power > 0 -%}{%- set ns.lines = ns.lines + [total_power | round(1) | string ~ ' W'] -%}{%- endif -%}"
                    "{%- if voltage > 0 -%}{%- set ns.lines = ns.lines + [voltage | string ~ ' V'] -%}{%- endif -%}"
                    "{{- ns.lines | join(' | ') if ns.lines else 'Idle' -}}"
                    "{%- endif -%}"
                ),
            },
        })

    # Services status UI sensor
    svc_config = sections.get("services", {})
    if svc_config.get("enabled", False):
        blocks.append({
            "entity": f"binary_sensor.{entity_prefix}_services_ok",
            "triggers": [f"sensor.{entity_prefix}_services_checked"],
            "name": f"ui_{slug}_services_status",
            "app": "running",
            "extra_attrs": {
                "services_icon": "mdi:cog",
                "services_color": (
                    "{{- 'green' if is_state('binary_sensor." + entity_prefix + "_services_ok', 'on') else 'red' -}}"
                ),
                "services_primary": "Services Status",
                "services_secondary": (
                    "{{- states('sensor." + entity_prefix + "_services_checked') ~ ' monitored' -}}"
                ),
            },
        })

    # Partition UI sensors for each partition in the config
    drv_config = sections.get("drives", {})
    part_config = sections.get("partitions", {})
    if drv_config.get("enabled", False) and "status" in drv_config.get("metrics", []):
        drives = drv_config.get("include", [])
        if drives:
            drive = drives[0]
            display = drive.get("display_name", drive.get("name", ""))
            drive_slug = slugify(display)
            status_sensor = f"sensor.{entity_prefix}_{drive_slug}_status"

            for part in part_config.get("include", []):
                part_name = part.get("name", "")
                part_display = part.get("display_name", part_name)
                part_slug = slugify(part_display)
                blocks.append({
                    "entity": status_sensor,
                    "triggers": [status_sensor],
                    "name": f"ui_{slug}_partition_{part_slug}",
                    "app": "connectivity",
                    "options": {"device_class": "binary"},
                    "extra_attrs": {
                        "partition_icon": (
                            "{%- set partitions = state_attr('" + status_sensor + "', 'partitions') | default([], true) -%}"
                            "{%- set p = partitions | selectattr('name', 'eq', '" + part_name + "') | first | default(none) -%}"
                            "{%- set guid_icons = {'c12a7328-f81f-11d2-ba4b-00a0c93ec93b': 'mdi:chip', 'e3c9e316-0b5c-4db8-817d-f92df00215ae': 'mdi:lock', 'ebd0a0a2-b9e5-4433-87c0-68b6b72699c7': 'mdi:harddisk', 'de94bba4-06d1-4d40-a16a-bfd50179d6ac': 'mdi:backup-restore'} -%}"
                            "{%- if p -%}"
                            "{%- set guid = (p['type_guid'] | default('')) | replace('{', '') | replace('}', '') | lower -%}"
                            "{%- set is_hidden = p['is_hidden'] | default(false) -%}"
                            "{%- set enc = p['encryption'] | default({}) -%}"
                            "{%- set is_encrypted = enc['encrypted'] | default(false) -%}"
                            "{%- set enc_unlocked = enc['unlocked'] | default(false) -%}"
                            "{%- if is_hidden -%}mdi:eye-off"
                            "{%- elif is_encrypted -%}{{- 'mdi:lock-open-variant' if enc_unlocked else 'mdi:lock' -}}"
                            "{%- else -%}{{- guid_icons.get(guid, 'mdi:harddisk') -}}"
                            "{%- endif -%}"
                            "{%- else -%}mdi:harddisk{%- endif -%}"
                        ),
                        "partition_color": (
                            "{%- set partitions = state_attr('" + status_sensor + "', 'partitions') | default([], true) -%}"
                            "{%- set p = partitions | selectattr('name', 'eq', '" + part_name + "') | first | default(none) -%}"
                            "{%- set guid_colors = {'c12a7328-f81f-11d2-ba4b-00a0c93ec93b': 'orange', 'e3c9e316-0b5c-4db8-817d-f92df00215ae': 'purple', 'ebd0a0a2-b9e5-4433-87c0-68b6b72699c7': 'blue', 'de94bba4-06d1-4d40-a16a-bfd50179d6ac': 'teal'} -%}"
                            "{%- if p -%}"
                            "{%- set guid = (p['type_guid'] | default('')) | replace('{', '') | replace('}', '') | lower -%}"
                            "{%- set is_hidden = p['is_hidden'] | default(false) -%}"
                            "{{- 'grey' if is_hidden else guid_colors.get(guid, 'grey') -}}"
                            "{%- else -%}grey{%- endif -%}"
                        ),
                        "partition_primary": (
                            "{%- set partitions = state_attr('" + status_sensor + "', 'partitions') | default([], true) -%}"
                            "{%- set p = partitions | selectattr('name', 'eq', '" + part_name + "') | first | default(none) -%}"
                            "{%- if p -%}"
                            "{%- set dl = p['drive_letter'] | default('') -%}"
                            "{{- '" + part_display + "' ~ (' (' ~ dl ~ ':)' if dl else '') -}}"
                            "{%- else -%}" + part_display + "{%- endif -%}"
                        ),
                        "partition_secondary": (
                            "{%- from 'units/base.jinja' import u_humanize_value -%}"
                            "{%- set partitions = state_attr('" + status_sensor + "', 'partitions') | default([], true) -%}"
                            "{%- set p = partitions | selectattr('name', 'eq', '" + part_name + "') | first | default(none) -%}"
                            "{%- set guid_names = {'c12a7328-f81f-11d2-ba4b-00a0c93ec93b': 'EFI', 'e3c9e316-0b5c-4db8-817d-f92df00215ae': 'Reserved', 'ebd0a0a2-b9e5-4433-87c0-68b6b72699c7': 'Data', 'de94bba4-06d1-4d40-a16a-bfd50179d6ac': 'Recovery'} -%}"
                            "{%- if p -%}"
                            "{%- set guid = (p['type_guid'] | default('')) | replace('{', '') | replace('}', '') | lower -%}"
                            "{%- set type_name = guid_names.get(guid, p['type'] | default('Unknown')) -%}"
                            "{%- set size = u_humanize_value(p['size_b'] | default(0), 'B') -%}"
                            "{%- set offset = u_humanize_value(p['start_offset_b'] | default(0), 'B') -%}"
                            "{%- set vol_guid = (p['volume_guid'] | default('')) | replace('{', '') | replace('}', '') -%}"
                            "{%- set enc = p['encryption'] | default({}) -%}"
                            "{%- set is_encrypted = enc['encrypted'] | default(false) -%}"
                            "{%- set enc_scheme = enc['scheme'] | default('') -%}"
                            "{%- set enc_unlocked = enc['unlocked'] | default(false) -%}"
                            "{%- set flags = [] -%}"
                            "{%- if p['is_boot'] | default(false) -%}{%- set flags = flags + ['Boot'] -%}{%- endif -%}"
                            "{%- if p['is_system'] | default(false) -%}{%- set flags = flags + ['System'] -%}{%- endif -%}"
                            "{%- if p['is_hidden'] | default(false) -%}{%- set flags = flags + ['Hidden'] -%}{%- endif -%}"
                            "{%- set line1 = type_name ~ ' | ' ~ size ~ ' @ ' ~ offset -%}"
                            "{%- set lines = [line1] -%}"
                            "{%- if flags -%}{%- set lines = lines + [flags | join(', ')] -%}{%- endif -%}"
                            "{%- if is_encrypted -%}"
                            "{%- set enc_status = ('🔓 ' if enc_unlocked else '🔒 ') ~ (enc_scheme if enc_scheme else 'Encrypted') -%}"
                            "{%- set lines = lines + [enc_status] -%}"
                            "{%- endif -%}"
                            "{%- if vol_guid -%}{%- set lines = lines + [vol_guid] -%}{%- endif -%}"
                            "{{- lines | join('\\n') -}}"
                            "{%- else -%}Partition not found{%- endif -%}"
                        ),
                    },
                })

    return blocks


def generate_ui_binary_sensors(machine_config: dict) -> list:
    """Generate UI binary sensors for dashboard display.

    This generates binary sensors with attributes needed for Windows-style
    chips display on the overview dashboard.
    """
    machine = machine_config["machine"]
    dashboard = machine_config.get("dashboard", {})
    overview = dashboard.get("overview", {})
    services_config = overview.get("services", {})

    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    name = machine["name"]
    sensors = []

    # Only generate if chips display mode is used
    if services_config.get("display") == "chips":
        chips = services_config.get("chips", [])
        if chips:
            # Build attributes dict for each service chip
            attributes = {}
            for chip in chips:
                chip_slug = slugify(chip)
                # Each attribute is a dict with icon, icon_color, content
                # Use 'search' with (?i) for case-insensitive regex matching
                attributes[chip_slug] = (
                    "{{ {'icon': 'mdi:cog' if (health.services | default([]) | selectattr('name', 'search',"
                    f" '(?i){chip}') | selectattr('ok', 'eq', true) | list | length > 0) else 'mdi:cog-off', 'icon_color':"
                    f" 'green' if (health.services | default([]) | selectattr('name', 'search', '(?i){chip}') |"
                    " selectattr('ok', 'eq', true) | list | length > 0) else 'red', 'content':"
                    f" '{chip.replace('_', ' ').title()}'}} }}}}"
                )

            sensors.append({
                "name": f"ui_{slug}_services",
                "unique_id": generate_uuid(f"ui_{slug}_services"),
                "state": "{{ health.services | default([]) | selectattr('ok', 'eq', false) | list | length == 0 }}",
                "attributes": attributes,
            })

    return sensors


def generate_package(machine_config: dict, output_dir: Path) -> Path:
    """Generate a complete package YAML for a machine."""
    machine = machine_config["machine"]
    sections = machine_config.get("sections", {})

    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    telemetry_sensor = machine["telemetry_sensor"]

    # Collect all sensors
    all_sensors = []
    all_sensors.extend(generate_host_sensors(machine, sections))
    all_sensors.extend(generate_health_sensors(machine, sections))
    all_sensors.extend(generate_cpu_sensors(machine, sections))
    all_sensors.extend(generate_memory_sensors(machine, sections))
    all_sensors.extend(generate_filesystem_sensors(machine, sections))
    all_sensors.extend(generate_network_sensors(machine, sections))
    all_sensors.extend(generate_gpu_sensors(machine, sections))
    all_sensors.extend(generate_tpu_sensors(machine, sections))
    all_sensors.extend(generate_sbc_sensors(machine, sections))
    all_sensors.extend(generate_time_server_sensors(machine, sections))
    all_sensors.extend(generate_motherboard_sensors(machine, sections))
    all_sensors.extend(generate_battery_sensors(machine, sections))
    all_sensors.extend(generate_drive_sensors(machine, sections))
    all_sensors.extend(generate_wifi_sensors(machine, sections))
    all_sensors.extend(generate_opnsense_sensors(machine, sections))
    all_sensors.extend(generate_zenarmor_sensors(machine, sections))
    all_sensors.extend(generate_backup_provider_sensors(machine, sections))

    binary_sensors = generate_binary_sensors(machine, sections)
    ui_blocks = generate_ui_sensors(machine_config)
    ui_binary_sensors = generate_ui_binary_sensors(machine_config)

    # Write the package file
    output_path = output_dir / f"{slug}.yaml"

    with open(output_path, "w") as f:
        # Write header
        f.write(generate_package_header(machine))

        # Write anchor container (also starts template: block)
        write_anchor_container(f)

        # Main data sensors block
        f.write(f"""\
  # ---------------------------------------------------------------------------
  # Data Sensors: {machine["name"]}
  # ---------------------------------------------------------------------------
  - trigger:
      - platform: homeassistant
        event: start
      - platform: state
        entity_id: {telemetry_sensor}
    variables:
      entity_id: {telemetry_sensor}
      available: "{{{{ has_value(entity_id) }}}}"
      host: "{{{{ state_attr(entity_id, 'host') or {{}} }}}}"
      health: "{{{{ state_attr(entity_id, 'health') or {{}} }}}}"
      cpus: "{{{{ state_attr(entity_id, 'cpus') or [] }}}}"
      memory: "{{{{ state_attr(entity_id, 'memory') or {{}} }}}}"
      filesystems: "{{{{ state_attr(entity_id, 'filesystems') or [] }}}}"
      ifaces: "{{{{ state_attr(entity_id, 'ifaces') or [] }}}}"
      gpus: "{{{{ state_attr(entity_id, 'gpus') or [] }}}}"
      tpus: "{{{{ state_attr(entity_id, 'tpus') or [] }}}}"
""")
        # Optional variables based on enabled sections
        if sections.get("sbc", {}).get("enabled", False):
            f.write("""\
      sbc: "{{ state_attr(entity_id, 'host').get('sbc', {}) if state_attr(entity_id, 'host') else {} }}"
      throttling: "{{ state_attr(entity_id, 'host').get('throttling', {}) if state_attr(entity_id, 'host') else {} }}"
""")
        if sections.get("time_server", {}).get("enabled", False):
            f.write("""\
      time_server: "{{ state_attr(entity_id, 'time_server') or {} }}"
""")
        if sections.get("motherboard", {}).get("enabled", False):
            f.write("""\
      motherboard_temps: "{{ state_attr(entity_id, 'motherboard').get('temps', []) if state_attr(entity_id, 'motherboard') else [] }}"
""")
        if sections.get("opnsense", {}).get("enabled", False):
            f.write("""\
      opnsense_plugins: "{{ state_attr(entity_id, 'opnsense_plugins') or [] }}"
""")
        if sections.get("zenarmor", {}).get("enabled", False):
            f.write("""\
      zenarmor: "{{ state_attr(entity_id, 'zenarmor') or {} }}"
""")
        if sections.get("batteries", {}).get("enabled", False):
            f.write("""\
      batteries: "{{ state_attr(entity_id, 'batteries') or [] }}"
""")
        if sections.get("drives", {}).get("enabled", False):
            f.write("""\
      drives: "{{ state_attr(entity_id, 'drives') or [] }}"
""")
        if sections.get("backup_providers", {}).get("enabled", False):
            f.write("""\
      backup_providers: "{{ state_attr(entity_id, 'backup_providers') or [] }}"
""")
        f.write("    sensor:\n")

        for sensor in all_sensors:
            write_sensor(f, sensor)

        if binary_sensors or ui_binary_sensors:
            f.write("    binary_sensor:\n")
            for sensor in binary_sensors:
                write_sensor(f, sensor)
            # UI Binary Sensors (for chips display)
            for sensor in ui_binary_sensors:
                write_sensor(f, sensor)

        f.write("""
  # ---------------------------------------------------------------------------
  # UI Sensors: Dashboard Display
  # ---------------------------------------------------------------------------
""")

        for block in ui_blocks:
            # Build trigger entity list
            trigger_entities = [block["entity"]]
            if "triggers" in block:
                trigger_entities.extend(block["triggers"])

            if len(trigger_entities) == 1:
                entity_id_yaml = f"        entity_id: {trigger_entities[0]}"
            else:
                entity_id_yaml = "        entity_id:\n" + "\n".join(f"          - {te}" for te in trigger_entities)

            # Build options yaml
            if "options" in block:
                options_yaml = "      options:\n" + "\n".join(f"        {k}: {v}" for k, v in block["options"].items())
            else:
                options_yaml = "      options: {}"

            device_class = block.get("options", {}).get("device_class", "none")

            f.write(f"""\
  - trigger:
      - platform: homeassistant
        event: start
      - platform: state
{entity_id_yaml}
    variables:
      entity_id: {block['entity']}
      app: {block['app']}
{options_yaml}
      state_info: >-
        {{%- from 'main.jinja' import get_device_state_info -%}}
        {{{{ get_device_state_info(entity_id, app, options=options) | from_json }}}}
      state_info_vertical: >-
        {{%- from 'main.jinja' import get_device_state_info -%}}
        {{{{ get_device_state_info(entity_id, app, layout='vertical', options=options) | from_json }}}}
    sensor:
      - name: {block['name']}
        unique_id: {generate_uuid(block['name'])}
        state: "{{{{ states(entity_id) }}}}"
        attributes:
          value: "{{{{ state_info.value }}}}"
          name: "{{{{ state_info.name }}}}"
          default_desc: "{{{{ state_info.default_desc }}}}"
          short_desc: "{{{{ state_info.short_desc }}}}"
          full_desc: "{{{{ state_info.full_desc }}}}"
          icon: "{{{{ state_info.icon }}}}"
          color: "{{{{ state_info.color }}}}"
          badge: "{{{{ state_info.badge }}}}"
          badge_color: "{{{{ state_info.badge_color }}}}"
          label: "{{{{ state_info.label }}}}"
          short_label: "{{{{ state_info.short_label }}}}"
          long_label: "{{{{ state_info.long_label }}}}"
          label_vertical: "{{{{ state_info_vertical.label }}}}"
          short_label_vertical: "{{{{ state_info_vertical.short_label }}}}"
          long_label_vertical: "{{{{ state_info_vertical.long_label }}}}"
          app: {block['app']}
          device_class: {device_class}
""")
            if "info" in block:
                f.write(f"""\
          long_desc: >-
            {block['info']}
""")
            if "extra_attrs" in block:
                for attr_name, attr_template in block["extra_attrs"].items():
                    f.write(f"""\
          {attr_name}: >-
            {attr_template}
""")

    return output_path


def _generate_card(card_name: str, ctx: dict) -> str:
    """Generate YAML for a specific card type.

    Args:
        card_name: Name of the card to generate (e.g., 'cpu_utilization', 'filesystems')
        ctx: Context dict with entity_prefix, slug, sections, telemetry_sensor, etc.

    Returns:
        YAML string for the card(s), or empty string if card not applicable
    """
    entity_prefix = ctx["entity_prefix"]
    slug = ctx["slug"]
    sections = ctx["sections"]
    telemetry_sensor = ctx["telemetry_sensor"]

    # Card generators
    if card_name == "health_summary":
        return f"""\
          - type: custom:mushroom-template-card
            entity: binary_sensor.{entity_prefix}_status_alarm
            icon: "{{{{ state_attr('sensor.ui_{slug}_status_alarm', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_status_alarm', 'color') }}}}"
            primary: Health Status
            secondary: "{{{{ state_attr('sensor.ui_{slug}_status_alarm', 'long_desc') }}}}"
            tap_action:
              action: more-info
"""

    elif card_name == "system":
        return f"""\
          - type: custom:mushroom-template-card
            entity: {telemetry_sensor}
            icon: "{{{{ state_attr('sensor.ui_{slug}_system', 'system_icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_system', 'system_color') }}}}"
            primary: "{{{{ state_attr('sensor.ui_{slug}_system', 'system_primary') }}}}"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_system', 'system_secondary') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info
"""

    elif card_name == "updates":
        return f"""\
          - type: markdown
            content: |
              {{% set packages = state_attr('sensor.{entity_prefix}_updates_list', 'packages') | default([]) %}}
              **Available Updates:**
              {{%- for pkg in packages %}}
                - {{{{ pkg }}}}
              {{%- endfor %}}
            visibility:
              - condition: numeric_state
                entity: sensor.{entity_prefix}_updates_pending
                above: 0
            card_mod:
              style: |
                ha-card {{
                  background: rgba(var(--rgb-primary-color), 0.1);
                  font-size: 0.9em;
                }}
"""

    elif card_name == "cpu_utilization":
        cpu_config = sections.get("cpu", {})
        if not cpu_config.get("enabled", False):
            return ""
        return f"""\
          - type: custom:mushroom-template-card
            entity: sensor.{entity_prefix}_cpu_utilization
            icon: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization', 'color') }}}}"
            primary: CPU Utilization
            secondary: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization', 'label') }}}}"
            tap_action:
              action: more-info
"""

    elif card_name == "cpu_load":
        cpu_config = sections.get("cpu", {})
        if not cpu_config.get("enabled", False) or "load_1m" not in cpu_config.get("metrics", []):
            return ""
        return f"""\
          - type: custom:mushroom-template-card
            entity: sensor.{entity_prefix}_cpu_load_1m
            icon: "{{{{ state_attr('sensor.ui_{slug}_cpu_load_1m', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_cpu_load_1m', 'color') }}}}"
            primary: CPU Load (1m/5m/15m)
            secondary: "{{{{ state_attr('sensor.ui_{slug}_cpu_load_1m', 'long_desc') }}}}"
            tap_action:
              action: more-info
"""

    elif card_name == "memory":
        mem_config = sections.get("memory", {})
        if not mem_config.get("enabled", False):
            return ""
        return f"""\
          - type: custom:mushroom-template-card
            entity: sensor.{entity_prefix}_memory_percent
            icon: "{{{{ state_attr('sensor.ui_{slug}_memory_percent', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_memory_percent', 'color') }}}}"
            primary: "Memory ({{{{ state_attr('sensor.ui_{slug}_memory_percent', 'value') }}}} used)"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_memory_percent', 'long_desc') }}}}"
            tap_action:
              action: more-info
"""

    elif card_name == "swap":
        mem_config = sections.get("memory", {})
        if not mem_config.get("enabled", False) or "virtual.load_pct" not in mem_config.get("metrics", []):
            return ""
        return f"""\
          - type: custom:mushroom-template-card
            entity: sensor.{entity_prefix}_swap_percent
            icon: "{{{{ state_attr('sensor.ui_{slug}_swap_percent', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_swap_percent', 'color') }}}}"
            primary: "Swap ({{{{ state_attr('sensor.ui_{slug}_swap_percent', 'value') }}}} used)"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_swap_percent', 'long_desc') }}}}"
            tap_action:
              action: more-info
"""

    elif card_name == "cpu_temp":
        cpu_config = sections.get("cpu", {})
        if not cpu_config.get("enabled", False) or "temp_c" not in cpu_config.get("metrics", []):
            return ""
        return f"""\
          - type: custom:mushroom-template-card
            entity: sensor.{entity_prefix}_cpu_temp
            icon: "{{{{ state_attr('sensor.ui_{slug}_cpu_temp', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_cpu_temp', 'color') }}}}"
            primary: CPU Temperature
            secondary: "{{{{ state_attr('sensor.ui_{slug}_cpu_temp', 'label') }}}}"
            tap_action:
              action: more-info
"""

    elif card_name == "drive_temp":
        drv_config = sections.get("drives", {})
        if not drv_config.get("enabled", False) or "temp_c" not in drv_config.get("metrics", []):
            return ""
        cards = ""
        for drive in drv_config.get("include", []):
            display = drive.get("display_name", drive.get("name", ""))
            drive_slug = slugify(display)
            cards += f"""\
          - type: custom:mushroom-template-card
            entity: sensor.{entity_prefix}_{drive_slug}_temp
            icon: "{{{{ state_attr('sensor.ui_{slug}_{drive_slug}_temp', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_{drive_slug}_temp', 'color') }}}}"
            primary: {display} Temperature
            secondary: "{{{{ state_attr('sensor.ui_{slug}_{drive_slug}_temp', 'label') }}}}"
            tap_action:
              action: more-info
"""
        return cards

    elif card_name == "gpu_temp":
        gpu_config = sections.get("gpus", {})
        if not gpu_config.get("enabled", False) or "temp_c" not in gpu_config.get("metrics", []):
            return ""
        return f"""\
          - type: custom:mushroom-template-card
            entity: sensor.{entity_prefix}_gpu_temp
            icon: "{{{{ state_attr('sensor.ui_{slug}_gpu_temp', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_gpu_temp', 'color') }}}}"
            primary: GPU Temperature
            secondary: "{{{{ state_attr('sensor.ui_{slug}_gpu_temp', 'label') }}}}"
            tap_action:
              action: more-info
"""

    elif card_name == "filesystems":
        fs_config = sections.get("filesystems", {})
        if not fs_config.get("enabled", False):
            return ""
        cards = ""
        for fs in fs_config.get("include", []):
            label = fs.get("label", "")
            mountpoint = fs.get("mountpoint", "")
            display = fs.get("display_name", (label or mountpoint).title())
            fs_slug = slugify(display)
            ui_sensor = f"sensor.ui_{slug}_fs_{fs_slug}"
            cards += f"""\
          - type: custom:mushroom-template-card
            entity: sensor.{entity_prefix}_fs_{fs_slug}_percent
            icon: "{{{{ state_attr('{ui_sensor}', 'fs_icon') | default('mdi:folder') }}}}"
            icon_color: "{{{{ state_attr('{ui_sensor}', 'fs_color') | default('green') }}}}"
            primary: {display}
            secondary: "{{{{ state_attr('{ui_sensor}', 'fs_secondary') | default('') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info
"""
        return cards

    elif card_name == "drives":
        drv_config = sections.get("drives", {})
        if not drv_config.get("enabled", False) or "status" not in drv_config.get("metrics", []):
            return ""
        cards = ""
        for drive in drv_config.get("include", []):
            display = drive.get("display_name", drive.get("name", ""))
            drive_slug = slugify(display)
            ui_sensor = f"sensor.ui_{slug}_{drive_slug}_status"
            status_sensor = f"sensor.{entity_prefix}_{drive_slug}_status"
            cards += f"""\
          - type: custom:mushroom-template-card
            entity: {status_sensor}
            icon: "{{{{ state_attr('{ui_sensor}', 'drive_icon') }}}}"
            icon_color: "{{{{ state_attr('{ui_sensor}', 'drive_color') }}}}"
            primary: "{{{{ state_attr('{status_sensor}', 'model') | default('{display}') }}}}"
            secondary: "{{{{ state_attr('{ui_sensor}', 'drive_secondary') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info
"""
        return cards

    elif card_name == "partitions":
        drv_config = sections.get("drives", {})
        part_config = sections.get("partitions", {})
        if not drv_config.get("enabled", False) or "status" not in drv_config.get("metrics", []):
            return ""
        # Get the first drive (for now, assuming single drive)
        drives = drv_config.get("include", [])
        if not drives:
            return ""
        drive = drives[0]
        display = drive.get("display_name", drive.get("name", ""))
        drive_slug = slugify(display)
        status_sensor = f"sensor.{entity_prefix}_{drive_slug}_status"

        # Generate static cards for each partition in the config via UI sensors
        cards = ""
        part_includes = part_config.get("include", [])

        for part in part_includes:
            part_name = part.get("name", "")
            part_display = part.get("display_name", part_name)
            part_slug = slugify(part_display)
            ui_sensor = f"sensor.ui_{slug}_partition_{part_slug}"
            cards += f"""\
          - type: custom:mushroom-template-card
            entity: {status_sensor}
            icon: "{{{{ state_attr('{ui_sensor}', 'partition_icon') }}}}"
            icon_color: "{{{{ state_attr('{ui_sensor}', 'partition_color') }}}}"
            primary: "{{{{ state_attr('{ui_sensor}', 'partition_primary') }}}}"
            secondary: "{{{{ state_attr('{ui_sensor}', 'partition_secondary') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info
"""
        return cards

    elif card_name == "network_interfaces":
        net_config = sections.get("network", {})
        if not net_config.get("enabled", False):
            return ""
        cards = ""
        for iface in net_config.get("include", []):
            display = iface.get("display_name", iface.get("name", ""))
            iface_slug = slugify(display)
            cards += f"""\
          - type: custom:mushroom-template-card
            entity: sensor.{entity_prefix}_{iface_slug}_info
            icon: "{{{{ state_attr('sensor.ui_{slug}_network_{iface_slug}','iface_icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_network_{iface_slug}','iface_color') }}}}"
            primary: "{{{{ state_attr('sensor.{entity_prefix}_{iface_slug}_info', 'name') }}}}"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_network_{iface_slug}','long_desc') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info
"""
        return cards

    elif card_name == "wifi_stats":
        wifi_config = sections.get("wifi", {})
        if not wifi_config.get("enabled", False):
            return ""
        # Build a single merged WiFi card with all stats via UI sensor
        return f"""\
          - type: custom:mushroom-template-card
            entity: sensor.{entity_prefix}_wifi_signal
            icon: "{{{{ state_attr('sensor.ui_{slug}_wifi_stats', 'wifi_icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_wifi_stats', 'wifi_color') }}}}"
            primary: "{{{{ state_attr('sensor.ui_{slug}_wifi_stats', 'wifi_primary') }}}}"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_wifi_stats', 'wifi_secondary') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info
"""

    elif card_name == "battery_status":
        bat_config = sections.get("batteries", {})
        if not bat_config.get("enabled", False):
            return ""
        # Battery status card via UI sensor
        return f"""\
          - type: custom:mushroom-template-card
            entity: {telemetry_sensor}
            icon: "{{{{ state_attr('sensor.ui_{slug}_battery_status', 'battery_icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_battery_status', 'battery_color') }}}}"
            primary: "{{{{ state_attr('sensor.ui_{slug}_battery_status', 'battery_primary') }}}}"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_battery_status', 'battery_secondary') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info
"""

    elif card_name == "battery_health":
        bat_config = sections.get("batteries", {})
        if not bat_config.get("enabled", False):
            return ""
        # Battery health card via UI sensor
        return f"""\
          - type: custom:mushroom-template-card
            entity: {telemetry_sensor}
            icon: "{{{{ state_attr('sensor.ui_{slug}_battery_health', 'health_icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_battery_health', 'health_color') }}}}"
            primary: "{{{{ state_attr('sensor.ui_{slug}_battery_health', 'health_primary') }}}}"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_battery_health', 'health_secondary') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info
"""

    elif card_name == "gpu_load":
        gpu_config = sections.get("gpus", {})
        if not gpu_config.get("enabled", False):
            return ""
        # GPU load card via UI sensor
        return f"""\
          - type: custom:mushroom-template-card
            entity: {telemetry_sensor}
            icon: "{{{{ state_attr('sensor.ui_{slug}_gpu_load', 'gpu_icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_gpu_load', 'gpu_color') }}}}"
            primary: "{{{{ state_attr('sensor.ui_{slug}_gpu_load', 'gpu_primary') }}}}"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_gpu_load', 'gpu_secondary') }}}}"
            tap_action:
              action: more-info
"""

    elif card_name == "engines":
        gpu_config = sections.get("gpus", {})
        if not gpu_config.get("enabled", False) or "engines" not in gpu_config.get("metrics", []):
            return ""

        # Get engine configuration for mini-graph-card
        engine_config = gpu_config.get("engine_sensors", [])
        if not engine_config:
            # Default engines
            engine_config = [
                {"name": "GPU Core", "slug": "gpu_core"},
                {"name": "D3D 3D", "slug": "d3d_3d"},
                {"name": "D3D Copy", "slug": "d3d_copy"},
                {"name": "D3D Video Codec 0", "slug": "d3d_video_codec"},
            ]

        # Build entity list for mini-graph-card
        entities_yaml = ""
        for engine in engine_config:
            engine_name = engine.get("name", "")
            engine_slug = engine.get("slug", engine_name.lower().replace(" ", "_").replace("-", "_"))
            display_name = engine_name.replace("D3D ", "").replace(" 0", "")
            entities_yaml += f"""
              - entity: sensor.{entity_prefix}_gpu_engine_{engine_slug}
                name: {display_name}"""

        # Mini-graph-card with bar visualization and dynamic icon color via UI sensor
        return f"""\
          - type: custom:mini-graph-card
            name: GPU Engines
            icon: mdi:engine
            entities:{entities_yaml}
            hours_to_show: 0.5
            points_per_hour: 120
            line_width: 2
            show:
              graph: bar
              labels: true
              fill: fade
            card_mod:
              style: |
                ha-card {{
                  --icon-color: {{{{ state_attr('sensor.ui_{entity_prefix}_gpu_engines', 'color') }}}};
                }}
                .icon {{
                  color: var(--icon-color) !important;
                }}
"""

    elif card_name == "services_status":
        svc_config = sections.get("services", {})
        if not svc_config.get("enabled", False):
            return ""
        # Services status card via UI sensor
        return f"""\
          - type: custom:mushroom-template-card
            entity: binary_sensor.{entity_prefix}_services_ok
            icon: "{{{{ state_attr('sensor.ui_{slug}_services_status', 'services_icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_services_status', 'services_color') }}}}"
            primary: "{{{{ state_attr('sensor.ui_{slug}_services_status', 'services_primary') }}}}"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_services_status', 'services_secondary') }}}}"
            tap_action:
              action: more-info
"""

    elif card_name == "containers_status":
        ctr_config = sections.get("containers", {})
        if not ctr_config.get("enabled", False):
            return ""
        return f"""\
          - type: custom:mushroom-template-card
            entity: binary_sensor.{entity_prefix}_containers_ok
            icon: mdi:docker
            icon_color: "{{{{ 'green' if is_state('binary_sensor.{entity_prefix}_containers_ok', 'on') else 'red' }}}}"
            primary: Containers Status
            secondary: "{{{{ states('sensor.{entity_prefix}_containers_checked') }}}} monitored"
            tap_action:
              action: more-info
"""

    elif card_name == "tpu":
        tpu_config = sections.get("tpus", {})
        if not tpu_config.get("enabled", False):
            return ""
        return f"""\
          - type: custom:mushroom-template-card
            entity: sensor.{entity_prefix}_coral_tpu_temp
            icon: "{{{{ state_attr('sensor.ui_{slug}_coral_tpu_temp', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_coral_tpu_temp', 'color') }}}}"
            primary: TPU Temperature
            secondary: "{{{{ state_attr('sensor.ui_{slug}_coral_tpu_temp', 'label') }}}}"
            tap_action:
              action: more-info
"""

    # Unknown card type
    return ""


def generate_dashboard_view(machine_config: dict, output_dir: Path) -> Path:
    """Generate a dashboard view YAML for a machine."""
    machine = machine_config["machine"]
    sections = machine_config.get("sections", {})
    dashboard = machine_config.get("dashboard", {})

    name = machine["name"]
    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    view_order = machine.get("view_order", 5)
    telemetry_sensor = machine["telemetry_sensor"]

    # Get detail_sections from dashboard config, or use default
    detail_sections = dashboard.get("detail_sections", [])

    output_path = output_dir / f"{view_order:02d}_{slug}.yaml"

    with open(output_path, "w") as f:
        f.write(f"""\
# -----------------------------------------------------------------------------
# Computers Dashboard: {name} View
# -----------------------------------------------------------------------------
#
# Auto-generated by generate_hwmon_assets.py
# DO NOT EDIT - Changes will be overwritten
#
# -----------------------------------------------------------------------------

title: {name}
path: {slug}
type: sections
max_columns: 3
cards: []

badges:
  - type: custom:mushroom-template-badge
    entity: binary_sensor.{entity_prefix}_status_alarm
    icon: "{{{{ state_attr('sensor.ui_{slug}_status_alarm', 'icon') }}}}"
    color: "{{{{ state_attr('sensor.ui_{slug}_status_alarm', 'color') }}}}"
    label: Status
    content: "{{{{ state_attr('sensor.ui_{slug}_status_alarm', 'short_label') }}}}"
    tap_action:
      action: more-info
  - type: custom:mushroom-template-badge
    entity: sensor.{entity_prefix}_uptime_s
    icon: "{{{{ state_attr('sensor.ui_{slug}_uptime_s', 'icon') }}}}"
    color: "{{{{ state_attr('sensor.ui_{slug}_uptime_s', 'color') }}}}"
    label: Uptime
    content: "{{{{ state_attr('sensor.ui_{slug}_uptime_s', 'short_label') }}}}"
    tap_action:
      action: more-info
  - type: custom:mushroom-template-badge
    entity: sensor.{entity_prefix}_cpu_load_1m
    icon: "{{{{ state_attr('sensor.ui_{slug}_cpu_load_1m', 'icon') }}}}"
    color: "{{{{ state_attr('sensor.ui_{slug}_cpu_load_1m', 'color') }}}}"
    label: CPU Load
    content: "{{{{ state_attr('sensor.ui_{slug}_cpu_load_1m', 'short_label') }}}}"
    tap_action:
      action: more-info
  - type: custom:mushroom-template-badge
    entity: sensor.{entity_prefix}_cpu_utilization
    icon: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization', 'icon') }}}}"
    color: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization', 'color') }}}}"
    label: CPU
    content: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization', 'short_label') }}}}"
    tap_action:
      action: more-info
  - type: custom:mushroom-template-badge
    entity: sensor.{entity_prefix}_cpu_temp
    icon: "{{{{ state_attr('sensor.ui_{slug}_cpu_temp', 'icon') }}}}"
    color: "{{{{ state_attr('sensor.ui_{slug}_cpu_temp', 'color') }}}}"
    label: CPU Temp
    content: "{{{{ state_attr('sensor.ui_{slug}_cpu_temp', 'short_label') }}}}"
    tap_action:
      action: more-info
  - type: custom:mushroom-template-badge
    entity: sensor.{entity_prefix}_memory_percent
    icon: "{{{{ state_attr('sensor.ui_{slug}_memory_percent', 'icon') }}}}"
    color: "{{{{ state_attr('sensor.ui_{slug}_memory_percent', 'color') }}}}"
    label: Memory
    content: "{{{{ state_attr('sensor.ui_{slug}_memory_percent', 'short_label') }}}}"
    tap_action:
      action: more-info

sections:
""")

        # Build context for card generators
        ctx = {
            "entity_prefix": entity_prefix,
            "slug": slug,
            "sections": sections,
            "telemetry_sensor": telemetry_sensor,
        }

        # Section title to subtitle mapping
        section_subtitles = {
            "System Status": "Health overview and pending updates",
            "CPU & Memory": "Utilization, load average, and memory pressure",
            "Device Temperatures": "Thermal status across components",
            "Filesystems": "Mounted volumes and storage capacity",
            "Drives & Partitions": "Physical disks, SMART health, and partition layout",
            "Drives": "Physical disk health and capacity",
            "Partitions": "Disk partition layout",
            "Network": "Interface status and connectivity",
            "WiFi": "Wireless connection details",
            "Battery": "Charge level and power status",
            "GPU": "Graphics processor load and thermals",
            "Services": "Monitored system services",
            "Containers": "Docker container health",
            "TPU": "ML accelerator status",
            "Storage": "Disk capacity and performance",
            "Time Server": "NTP synchronization status",
            "GPS": "Satellite positioning data",
            "Motherboard": "Board sensor readings",
            "OPNsense": "Firewall status",
            "Zenarmor": "DPI engine status",
            "SBC": "Single-board computer metrics",
        }

        # Generate sections from detail_sections config
        if detail_sections:
            for section in detail_sections:
                title = section.get("title", "")
                subtitle = section.get("subtitle", section_subtitles.get(title, ""))
                cards = section.get("cards", [])

                if not cards:
                    continue

                # Generate cards for this section
                cards_yaml = ""
                for card_name in cards:
                    card_yaml = _generate_card(card_name, ctx)
                    if card_yaml:
                        cards_yaml += card_yaml

                if not cards_yaml:
                    continue

                # Write the section with optional subtitle
                subtitle_line = f"\n            subtitle: {subtitle}" if subtitle else ""
                f.write(f"""
  - type: grid
    column_span: 1
    cards:
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: {title}{subtitle_line}
{cards_yaml}""")

    return output_path


def generate_overview_view(machine_configs: list, output_dir: Path) -> Path:
    """Generate the 01_overview.yaml dashboard view combining all machines.

    Args:
        machine_configs: List of loaded machine configuration dicts
        output_dir: Directory to write the view file

    Returns:
        Path to the generated file
    """
    output_path = output_dir / "01_overview.yaml"

    # Sort machines by view_order
    sorted_configs = sorted(machine_configs, key=lambda c: c["machine"].get("view_order", 99))

    with open(output_path, "w") as f:
        f.write("""\
# -----------------------------------------------------------------------------
# Computers Dashboard: Systems Overview
# -----------------------------------------------------------------------------
#
# Auto-generated by generate_hwmon_assets.py
# DO NOT EDIT - Changes will be overwritten
#
# -----------------------------------------------------------------------------

title: Systems Overview
type: sections
max_columns: 2
cards: []

badges:
""")
        # Generate badges - one per machine showing CPU utilization
        for config in sorted_configs:
            machine = config["machine"]
            slug = machine["slug"]
            entity_prefix = machine.get("entity_prefix", slug)
            name = machine["name"]
            overview = config.get("dashboard", {}).get("overview", {})
            display_name = overview.get("display_name", name)

            f.write(f"""\
  - type: custom:mushroom-template-badge
    entity: sensor.{entity_prefix}_cpu_utilization
    icon: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization', 'icon') }}}}"
    color: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization', 'color') }}}}"
    label: {display_name}
    content: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization', 'short_label') }}}}"
    tap_action:
      action: more-info
    icon_tap_action:
      action: toggle
""")

        # Generate sections - single grid with all machines
        f.write("""\
sections:
  - type: grid
    column_span: 2
    cards:
""")

        for config in sorted_configs:
            _write_overview_machine_card(f, config)

    return output_path


def _write_overview_machine_card(f, config: dict):
    """Write a single machine's vertical-stack card for the overview."""
    machine = config["machine"]
    sections = config.get("sections", {})
    overview = config.get("dashboard", {}).get("overview", {})

    slug = machine["slug"]
    entity_prefix = machine.get("entity_prefix", slug)
    name = machine["name"]
    display_name = overview.get("display_name", name)

    # Get overview-specific settings
    filesystems = overview.get("filesystems", [])
    temp_suffix = overview.get("temp_suffix", "cpu_temp")
    gpu_config = overview.get("gpu", {})
    tpu_config = overview.get("tpu", {})
    services_config = overview.get("services", {})
    containers_config = overview.get("containers", {})

    # Write the header and summary cards
    f.write(f"""\
      - type: vertical-stack
        cards:

          # Header
          - type: custom:mushroom-title-card
            title: {display_name}
            subtitle: "{{{{ states('sensor.{entity_prefix}_overall_status_summary') }}}}"

          # Summary
          - type: horizontal-stack
            cards:
              - type: custom:mushroom-template-card
                entity: sensor.{entity_prefix}_uptime_s
                icon: "{{{{ state_attr('sensor.ui_{slug}_uptime_s', 'icon') }}}}"
                icon_color: "{{{{ state_attr('sensor.ui_{slug}_uptime_s', 'color') }}}}"
                primary: Uptime
                secondary: "{{{{ state_attr('sensor.ui_{slug}_uptime_s', 'label_vertical') }}}}"
                badge_icon: "{{{{ state_attr('sensor.ui_{slug}_uptime_s', 'badge') }}}}"
                badge_color: "{{{{ state_attr('sensor.ui_{slug}_uptime_s', 'badge_color') }}}}"
                layout: vertical
                multiline_secondary: true
                tap_action:
                  action: more-info
                icon_tap_action:
                  action: toggle
                grid_options:
                  columns: 12
                  rows: auto
              - type: custom:mushroom-template-card
                entity: sensor.{entity_prefix}_updates_pending
                icon: "{{{{ state_attr('sensor.ui_{slug}_updates_pending', 'icon') }}}}"
                icon_color: "{{{{ state_attr('sensor.ui_{slug}_updates_pending', 'color') }}}}"
                primary: Updates
                secondary: "{{{{ state_attr('sensor.ui_{slug}_updates_pending', 'label_vertical') }}}}"
                badge_icon: "{{{{ state_attr('sensor.ui_{slug}_updates_pending', 'badge') }}}}"
                badge_color: "{{{{ state_attr('sensor.ui_{slug}_updates_pending', 'badge_color') }}}}"
                layout: vertical
                multiline_secondary: true
                tap_action:
                  action: more-info
                icon_tap_action:
                  action: toggle
                grid_options:
                  columns: 12
                  rows: auto
              - type: custom:mushroom-template-card
                entity: binary_sensor.{entity_prefix}_status_alarm
                icon: "{{{{ state_attr('sensor.ui_{slug}_status_alarm', 'icon') }}}}"
                icon_color: "{{{{ state_attr('sensor.ui_{slug}_status_alarm', 'color') }}}}"
                primary: Status
                secondary: "{{{{ state_attr('sensor.ui_{slug}_status_alarm', 'long_label_vertical') }}}}"
                badge_icon: "{{{{ state_attr('sensor.ui_{slug}_status_alarm', 'badge') }}}}"
                badge_color: "{{{{ state_attr('sensor.ui_{slug}_status_alarm', 'badge_color') }}}}"
                layout: vertical
                multiline_secondary: true
                tap_action:
                  action: more-info
                icon_tap_action:
                  action: toggle
                grid_options:
                  columns: 12
                  rows: auto
          - type: horizontal-stack
            cards:
              - type: custom:mushroom-template-card
                entity: sensor.{entity_prefix}_cpu_utilization
                icon: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization_load', 'icon') }}}}"
                icon_color: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization_load', 'color') }}}}"
                primary: CPU
                secondary: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization_load', 'label') }}}}"
                badge_icon: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization_load', 'badge') }}}}"
                badge_color: "{{{{ state_attr('sensor.ui_{slug}_cpu_utilization_load', 'badge_color') }}}}"
                multiline_secondary: true
                tap_action:
                  action: more-info
                icon_tap_action:
                  action: toggle
                grid_options:
                  columns: 12
                  rows: auto
              - type: custom:mushroom-template-card
                entity: sensor.{entity_prefix}_memory_percent
                icon: "{{{{ state_attr('sensor.ui_{slug}_memory_percent', 'icon') }}}}"
                icon_color: "{{{{ state_attr('sensor.ui_{slug}_memory_percent', 'color') }}}}"
                primary: "Memory ({{{{ state_attr('sensor.ui_{slug}_memory_percent', 'value') }}}} used)"
                secondary: "{{{{ state_attr('sensor.ui_{slug}_memory_percent', 'long_desc') }}}}"
                badge_icon: "{{{{ state_attr('sensor.ui_{slug}_memory_percent', 'badge') }}}}"
                badge_color: "{{{{ state_attr('sensor.ui_{slug}_memory_percent', 'badge_color') }}}}"
                multiline_secondary: true
                tap_action:
                  action: more-info
                icon_tap_action:
                  action: toggle
                grid_options:
                  columns: 12
                  rows: auto
          - type: horizontal-stack
            cards:
""")

    # Determine filesystem cards
    if filesystems:
        # Multiple filesystems - stack them, temp/GPU/TPU in separate stack
        f.write("              - type: vertical-stack\n")
        f.write("                cards:\n")
        for fs in filesystems:
            fs_slug = fs["slug"]
            fs_label = fs.get("label", "Disk")
            f.write(f"""\
                  - type: custom:mushroom-template-card
                    entity: sensor.{entity_prefix}_fs_{fs_slug}_percent
                    icon: "{{{{ state_attr('sensor.ui_{slug}_fs_{fs_slug}_percent', 'icon') }}}}"
                    icon_color: "{{{{ state_attr('sensor.ui_{slug}_fs_{fs_slug}_percent', 'color') }}}}"
                    primary: {fs_label}
                    secondary: "{{{{ state_attr('sensor.ui_{slug}_fs_{fs_slug}_percent', 'long_desc') }}}}"
                    badge_icon: "{{{{ state_attr('sensor.ui_{slug}_fs_{fs_slug}_percent', 'badge') }}}}"
                    badge_color: "{{{{ state_attr('sensor.ui_{slug}_fs_{fs_slug}_percent', 'badge_color') }}}}"
                    multiline_secondary: true
                    tap_action:
                      action: more-info
                    icon_tap_action:
                      action: toggle
                    grid_options:
                      columns: 12
                      rows: auto
""")
        # Temp/GPU/TPU stack
        _write_temp_and_gpu_tpu_stack(f, slug, entity_prefix, temp_suffix, gpu_config, tpu_config)
    else:
        # No filesystems configured, just show temp
        _write_temp_and_gpu_tpu_stack(f, slug, entity_prefix, temp_suffix, gpu_config, tpu_config, full_width=True)

    # Services section
    services_display = services_config.get("display")
    if services_display:
        f.write(f"""
          - type: custom:mushroom-title-card
            subtitle: Stopped Services
            visibility:
              - condition: state
                entity: binary_sensor.{entity_prefix}_display_services
                state: 'on'
""")
        if services_display == "chips":
            # Windows-style chips with specific attributes
            chips = services_config.get("chips", [])
            if chips:
                f.write(f"""
          - type: custom:mushroom-chips-card
            alignment: center
            visibility:
              - condition: state
                entity: binary_sensor.{entity_prefix}_display_services
                state: 'on'
            chips:
""")
                for chip in chips:
                    f.write(f"""\
              - type: template
                icon: "{{{{ state_attr('binary_sensor.ui_{slug}_services','{chip}').icon }}}}"
                icon_color: "{{{{ state_attr('binary_sensor.ui_{slug}_services','{chip}').icon_color }}}}"
                content: "{{{{ state_attr('binary_sensor.ui_{slug}_services','{chip}').content }}}}"
                tap_action:
                  action: none
""")
        else:
            # Auto-entities for Linux/FreeBSD
            f.write(f"""
          - type: custom:auto-entities
            card:
              type: custom:mushroom-chips-card
              alignment: start
            card_param: chips
            filter:
              include:
                - entity_id: binary_sensor.{slug}*_service_*
                  state: 'off'
                  options:
                    type: template
                    entity: this.entity_id
                    icon: |
                      {{{{- 'mdi:cog' if is_state(entity,'on') else 'mdi:cog-off' -}}}}
                    icon_color: |
                      {{{{- 'green' if is_state(entity,'on') else 'red' -}}}}
                    content: >
                      {{%- set s = state_attr(entity,'friendly_name') | default('', true) -%}}
                      {{{{- (s.partition('Service')[2]) if 'Service' in s else '' -}}}}
                    tap_action: none
              exclude: []
            sort:
              method: name
""")

    # Containers section
    containers_display = containers_config.get("display")
    if containers_display:
        f.write(f"""
          - type: custom:mushroom-title-card
            subtitle: Stopped Containers
            visibility:
              - condition: state
                entity: binary_sensor.{entity_prefix}_display_containers
                state: 'on'

          - type: custom:auto-entities
            card:
              type: custom:mushroom-chips-card
              alignment: start
            card_param: chips
            filter:
              include:
                - entity_id: binary_sensor.{slug}*_container_*
                  state: 'off'
                  options:
                    type: template
                    entity: this.entity_id
                    icon: >
                      {{{{- 'mdi:server' if is_state(entity,'on') else 'mdi:server-off' -}}}}
                    icon_color: |
                      {{{{- 'green' if is_state(entity,'on') else 'red' -}}}}
                    content: >
                      {{%- set s = state_attr(entity,'friendly_name') | default('', true) -%}}
                      {{{{- (s.partition('Container')[2]) if 'Container' in s else '' -}}}}
                    tap_action: none
              exclude: []
            sort:
              method: name
""")

    f.write("\n")


def _write_temp_and_gpu_tpu_stack(
    f, slug: str, entity_prefix: str, temp_suffix: str | None, gpu_config: dict, tpu_config: dict, full_width: bool = False
):
    """Write the temperature and optional GPU/TPU cards in a vertical stack."""
    # Check if we have any cards to write
    has_temp = temp_suffix is not None
    has_gpu = gpu_config.get("enabled", False)
    has_tpu = tpu_config.get("enabled", False)

    if not has_temp and not has_gpu and not has_tpu:
        return  # Nothing to write

    indent = "              " if not full_width else "              "

    f.write(f"{indent}- type: vertical-stack\n")
    f.write(f"{indent}  cards:\n")

    # Temperature card (optional)
    if has_temp:
        f.write(f"{indent}    - type: custom:mushroom-template-card\n")
        f.write(f"{indent}      entity: sensor.{entity_prefix}_{temp_suffix}\n")
        f.write(f"{indent}      icon: \"{{{{ state_attr('sensor.ui_{slug}_{temp_suffix}', 'icon') }}}}\"\n")
        f.write(f"{indent}      icon_color: \"{{{{ state_attr('sensor.ui_{slug}_{temp_suffix}', 'color') }}}}\"\n")
        f.write(f"{indent}      primary: CPU Temp\n")
        f.write(f"{indent}      secondary: \"{{{{ state_attr('sensor.ui_{slug}_{temp_suffix}', 'label') }}}}\"\n")
        f.write(f"{indent}      badge_icon: \"{{{{ state_attr('sensor.ui_{slug}_{temp_suffix}', 'badge') }}}}\"\n")
        f.write(f"{indent}      badge_color: \"{{{{ state_attr('sensor.ui_{slug}_{temp_suffix}', 'badge_color') }}}}\"\n")
        f.write(f"{indent}      multiline_secondary: true\n")
        f.write(f"{indent}      tap_action:\n")
        f.write(f"{indent}        action: more-info\n")
        f.write(f"{indent}      icon_tap_action:\n")
        f.write(f"{indent}        action: more-info\n")
        f.write(f"{indent}      grid_options:\n")
        f.write(f"{indent}        columns: 12\n")
        f.write(f"{indent}        rows: auto\n")

    # GPU card (optional)
    if gpu_config.get("enabled", False):
        gpu_suffix = gpu_config.get("suffix", "gpu_utilization")
        gpu_label = gpu_config.get("label", "GPU")
        f.write(f"{indent}    - type: custom:mushroom-template-card\n")
        f.write(f"{indent}      visibility:\n")
        f.write(f"{indent}        - condition: state\n")
        f.write(f"{indent}          entity: sensor.{entity_prefix}_{gpu_suffix}\n")
        f.write(f"{indent}          state_not: unknown\n")
        f.write(f"{indent}      entity: sensor.{entity_prefix}_{gpu_suffix}\n")
        f.write(f"{indent}      icon: \"{{{{ state_attr('sensor.ui_{slug}_{gpu_suffix}', 'icon') }}}}\"\n")
        f.write(f"{indent}      icon_color: \"{{{{ state_attr('sensor.ui_{slug}_{gpu_suffix}', 'color') }}}}\"\n")
        f.write(f"{indent}      primary: {gpu_label}\n")
        f.write(f"{indent}      secondary: \"{{{{ state_attr('sensor.ui_{slug}_{gpu_suffix}', 'label') }}}}\"\n")
        f.write(f"{indent}      badge_icon: \"{{{{ state_attr('sensor.ui_{slug}_{gpu_suffix}', 'badge') }}}}\"\n")
        f.write(
            f"{indent}      badge_color: \"{{{{ state_attr('sensor.ui_{slug}_{gpu_suffix}', 'badge_color') }}}}\"\n"
        )
        f.write(f"{indent}      multiline_secondary: true\n")
        f.write(f"{indent}      tap_action:\n")
        f.write(f"{indent}        action: more-info\n")
        f.write(f"{indent}      icon_tap_action:\n")
        f.write(f"{indent}        action: more-info\n")
        f.write(f"{indent}      grid_options:\n")
        f.write(f"{indent}        columns: 12\n")
        f.write(f"{indent}        rows: auto\n")

    # TPU card (optional)
    if tpu_config.get("enabled", False):
        tpu_suffix = tpu_config.get("suffix", "coral_tpu_temp")
        tpu_label = tpu_config.get("label", "TPU")
        f.write(f"{indent}    - type: custom:mushroom-template-card\n")
        f.write(f"{indent}      visibility:\n")
        f.write(f"{indent}        - condition: state\n")
        f.write(f"{indent}          entity: sensor.{entity_prefix}_{tpu_suffix}\n")
        f.write(f"{indent}          state_not: unknown\n")
        f.write(f"{indent}      entity: sensor.{entity_prefix}_{tpu_suffix}\n")
        f.write(f"{indent}      icon: \"{{{{ state_attr('sensor.ui_{slug}_{tpu_suffix}', 'icon') }}}}\"\n")
        f.write(f"{indent}      icon_color: \"{{{{ state_attr('sensor.ui_{slug}_{tpu_suffix}', 'color') }}}}\"\n")
        f.write(f"{indent}      primary: {tpu_label}\n")
        f.write(f"{indent}      secondary: \"{{{{ state_attr('sensor.ui_{slug}_{tpu_suffix}', 'label') }}}}\"\n")
        f.write(f"{indent}      badge_icon: \"{{{{ state_attr('sensor.ui_{slug}_{tpu_suffix}', 'badge') }}}}\"\n")
        f.write(
            f"{indent}      badge_color: \"{{{{ state_attr('sensor.ui_{slug}_{tpu_suffix}', 'badge_color') }}}}\"\n"
        )
        f.write(f"{indent}      multiline_secondary: true\n")
        f.write(f"{indent}      tap_action:\n")
        f.write(f"{indent}        action: more-info\n")
        f.write(f"{indent}      icon_tap_action:\n")
        f.write(f"{indent}        action: more-info\n")
        f.write(f"{indent}      grid_options:\n")
        f.write(f"{indent}        columns: 12\n")
        f.write(f"{indent}        rows: auto\n")


def main():
    parser = argparse.ArgumentParser(description="Generate hwmon packages and dashboards")
    parser.add_argument("--machines", nargs="+", help="Machine slugs to process")
    parser.add_argument("--all", action="store_true", help="Process all machine configs")
    parser.add_argument("--config-dir", default="hwmon_machines", help="Directory containing machine configs")
    parser.add_argument("--package-dir", default="packages/hwmon", help="Output directory for packages")
    parser.add_argument(
        "--dashboard-dir", default="dashboards/computers/views", help="Output directory for dashboard views"
    )
    args = parser.parse_args()

    # Determine base path
    script_path = Path(__file__).resolve()
    config_base = script_path.parent.parent  # config/

    config_dir = config_base / args.config_dir
    package_dir = config_base / args.package_dir
    dashboard_dir = config_base / args.dashboard_dir

    # Ensure output directories exist
    package_dir.mkdir(parents=True, exist_ok=True)
    dashboard_dir.mkdir(parents=True, exist_ok=True)

    # Find machine configs to process
    if args.all:
        machine_files = list(config_dir.glob("*.yaml"))
    elif args.machines:
        machine_files = [config_dir / f"{m}.yaml" for m in args.machines]
    else:
        print("Error: Specify --machines or --all")
        return 1

    # Load and process all machine configs
    all_configs = []
    for machine_file in machine_files:
        if not machine_file.exists():
            print(f"Warning: Config not found: {machine_file}")
            continue

        print(f"Processing: {machine_file.name}")
        config = load_machine_config(machine_file)
        all_configs.append(config)

        # Generate package
        pkg_path = generate_package(config, package_dir)
        print(f"  Generated package: {pkg_path}")

        # Generate dashboard view
        dash_path = generate_dashboard_view(config, dashboard_dir)
        print(f"  Generated dashboard: {dash_path}")

    # Generate the overview dashboard combining all machines (only when --all is used)
    if args.all and all_configs:
        print("Generating overview dashboard...")
        overview_path = generate_overview_view(all_configs, dashboard_dir)
        print(f"  Generated overview: {overview_path}")

    print("Done!")
    return 0


if __name__ == "__main__":
    exit(main())
