#!/usr/bin/env python3
"""
generate_plant_assets.py — generate HA plant packages and dashboard sections

Generates:
  - Per-plant packages with UUID-based unique_ids, ui_* sensors for dashboard lookups
  - Dashboard section files that only use state_attr() lookups on ui_* sensors
  - Central MiFlora router package

Conventions:
  - UUID-based unique_ids for all recordable sensors
  - ui_* sensors (no unique_id, snake_case) for dashboard card attributes
  - Dashboard sections reference only ui_* sensor attributes (no inline Jinja)
  - Quoted sensor names
  - Standard section comment style: # -----------------------------------------------------------------------------
"""

import argparse
import csv
import json
import re
import sys
import uuid
from pathlib import Path
from textwrap import dedent, indent
from typing import Any, Dict, List, Optional

import requests


def slugify(s: str) -> str:
    """Convert string to snake_case slug."""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def make_uuid(namespace: str, name: str) -> str:
    """Generate deterministic UUID from namespace and name."""
    ns = uuid.uuid5(uuid.NAMESPACE_DNS, "homeassistant.local")
    return str(uuid.uuid5(ns, f"{namespace}:{name}"))


def to_float(v, default=None):
    """Convert value to float or return default."""
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def ensure_dir(p: Path):
    """Create directory if it doesn't exist."""
    p.mkdir(parents=True, exist_ok=True)


def load_sensor_map(path: Path) -> Dict[str, Dict[str, str]]:
    """Load sensor mapping from JSON file."""
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def fix_mojibake(text: Optional[str]) -> str:
    """Repair common encoding issues in text."""
    if text is None:
        return ""
    if any(ch in text for ch in ("â", "Ã", "€")):
        try:
            return text.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            return text
    return text


def yaml_multiline(value: Optional[str], indent_spaces: int = 10) -> str:
    """Format value as YAML multiline string if needed."""
    raw = fix_mojibake(value or "").strip()
    text = raw.replace("\r\n", "\n").replace("\r", "\n").replace("\\n", "\n")
    text = text.replace("\u2028", "\n").replace("\u2029", "\n")

    if text == "":
        return '""'

    if "\n" in text:
        pad = " " * indent_spaces
        lines = "\n".join(pad + ln for ln in text.split("\n"))
        return f"|-\n{lines}"

    v = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{v}"'


ISO_LANG_MAP = {
    "en": "eng", "es": "spa", "fr": "fra", "de": "deu",
    "it": "ita", "pt": "por", "zh": "zho", "ja": "jpn", "ko": "kor",
}


def _match_lang_codes(lang: str) -> set[str]:
    """Get matching language codes for a language."""
    if not lang:
        return set()
    lang = lang.strip().lower()
    codes = {lang}
    iso3 = ISO_LANG_MAP.get(lang[:2])
    if iso3:
        codes.add(iso3)
    if len(lang) == 3:
        codes.add(lang[:2])
    return {code for code in codes if code}


def get_common_name_gbif(scientific: str, lang: str = "en", country: str | None = "US", timeout=8) -> str | None:
    """Use GBIF to get a vernacular name for a scientific name."""
    s = requests.Session()
    r = s.get("https://api.gbif.org/v1/species/match", params={"name": scientific}, timeout=timeout)
    r.raise_for_status()
    key = r.json().get("usageKey")
    if not key:
        return None
    r = s.get(f"https://api.gbif.org/v1/species/{key}/vernacularNames", timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        names = data
    elif isinstance(data, dict):
        names = data.get("results") or data.get("vernacularNames") or []
    else:
        names = []

    if not names:
        return None

    lang_codes = _match_lang_codes(lang)
    country_code = country.upper() if isinstance(country, str) else None

    def _pick(filter_fn):
        for entry in names:
            name = (entry or {}).get("vernacularName")
            if not name:
                continue
            if filter_fn(entry):
                return name
        return None

    if lang_codes and country_code:
        match = _pick(
            lambda entry: entry.get("language", "").lower() in lang_codes
            and entry.get("country", "").upper() == country_code
        )
        if match:
            return match

    if lang_codes:
        match = _pick(lambda entry: entry.get("language", "").lower() in lang_codes)
        if match:
            return match

    if country_code:
        match = _pick(lambda entry: entry.get("country", "").upper() == country_code)
        if match:
            return match

    return _pick(lambda entry: True)


def get_common_name_wikidata(scientific: str, lang="en", timeout=8) -> str | None:
    """Query Wikidata for an English label / vernacular name by exact scientific name."""
    query = f"""
    SELECT ?itemLabel ?vname WHERE {{
      ?item wdt:P225 "{scientific}" .
      OPTIONAL {{ ?item wdt:P1843 ?vname . FILTER(LANG(?vname) = "{lang}") }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}" . }}
    }} LIMIT 5
    """
    r = requests.get(
        "https://query.wikidata.org/sparql",
        params={"query": query, "format": "json"},
        headers={"User-Agent": "HomeAssistant-PlantCards/1.0"},
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()["results"]["bindings"]
    for b in data:
        if "vname" in b:
            return b["vname"]["value"]
    if data and "itemLabel" in data[0]:
        return data[0]["itemLabel"]["value"]
    return None


def best_common_name(scientific: str, lang="en", country: str | None = "US") -> str | None:
    """Get best common name from GBIF first, then Wikidata."""
    try:
        name = get_common_name_gbif(scientific, lang=lang, country=country)
        if name:
            return name
    except Exception:
        pass
    try:
        name = get_common_name_wikidata(scientific, lang=lang)
        if name:
            return name
    except Exception:
        pass
    return None


# -----------------------------------------------------------------------------
# Package Generation
# -----------------------------------------------------------------------------

PACKAGE_HEADER = """\
# =============================================================================
# Plant Package: {display_name} ({pid})
# =============================================================================
#
# Generated by generate_plant_assets.py
#
# Entities created:
#   - plant.{slug}
#   - sensor.{slug}_light_min_lux, sensor.{slug}_light_max_lux
#   - sensor.{slug}_temp_min, sensor.{slug}_temp_max
#   - sensor.{slug}_humidity_min, sensor.{slug}_humidity_max
#   - sensor.{slug}_moisture_min, sensor.{slug}_moisture_max
#   - sensor.{slug}_ec_min, sensor.{slug}_ec_max
#   - binary_sensor.{slug}_temperature_ok, binary_sensor.{slug}_light_ok
#   - binary_sensor.{slug}_moisture_ok, binary_sensor.{slug}_ec_ok
#   - binary_sensor.{slug}_all_ok
#   - sensor.{slug}_care_notes
#   - sensor.ui_{slug}_* (UI sensors for dashboard lookups, no unique_id)
#
# Thresholds from CSV:
#   Light lux:  min={min_light_lux}, max={max_light_lux}
#   Temp C:     min={min_temp}, max={max_temp}
#   Humidity %: min={min_humid}, max={max_humid}
#   Moisture %: min={min_moist}, max={max_moist}
#   EC uS/cm:   min={min_ec}, max={max_ec}
#
# =============================================================================
"""


def build_package_yaml(row: Dict[str, Any], sensors: Dict[str, str]) -> str:
    """Build the package YAML for a plant."""
    pid = row["pid"]
    display_pid = row.get("display_pid") or pid.title()
    slug = slugify(pid)
    friendly = f"{display_pid}"
    image = (row.get("image") or "").strip()

    # Extract thresholds
    min_light_lux = to_float(row.get("min_light_lux"))
    max_light_lux = to_float(row.get("max_light_lux"))
    min_temp = to_float(row.get("min_temp"))
    max_temp = to_float(row.get("max_temp"))
    min_humid = to_float(row.get("min_env_humid"))
    max_humid = to_float(row.get("max_env_humid"))
    min_moist = to_float(row.get("min_soil_moist"))
    max_moist = to_float(row.get("max_soil_moist"))
    min_ec = to_float(row.get("min_soil_ec"))
    max_ec = to_float(row.get("max_soil_ec"))

    # Sensor entity references (use routed sensors from router package)
    moisture = sensors.get("moisture", f"sensor.{slug}_moisture_routed")
    temperature = sensors.get("temperature", f"sensor.{slug}_temperature_routed")
    brightness = sensors.get("brightness", f"sensor.{slug}_illuminance_routed")
    conductivity = sensors.get("conductivity", f"sensor.{slug}_conductivity_routed")

    # Generate UUIDs for sensors
    def uid(name: str) -> str:
        return make_uuid(slug, name)

    # Build header
    header = PACKAGE_HEADER.format(
        display_name=display_pid,
        pid=pid,
        slug=slug,
        min_light_lux=min_light_lux or "null",
        max_light_lux=max_light_lux or "null",
        min_temp=min_temp or "null",
        max_temp=max_temp or "null",
        min_humid=min_humid or "null",
        max_humid=max_humid or "null",
        min_moist=min_moist or "null",
        max_moist=max_moist or "null",
        min_ec=min_ec or "null",
        max_ec=max_ec or "null",
    )

    # Build care attribute values
    care_attrs = []
    for attr_name, csv_key in [
        ("image", "image"),
        ("alias", "alias"),
        ("origin", "origin"),
        ("production", "production"),
        ("category", "category"),
        ("floral_language", "floral_language"),
        ("blooming", "blooming"),
        ("color", "color"),
        ("size", "size"),
        ("soil", "soil"),
        ("sunlight", "sunlight"),
        ("watering", "watering"),
        ("fertilization", "fertilization"),
        ("pruning", "pruning"),
    ]:
        val = yaml_multiline(row.get(csv_key), 10)
        care_attrs.append(f"          {attr_name}: {val}")

    care_attrs_yaml = "\n".join(care_attrs)

    yaml = f"""{header}
# -----------------------------------------------------------------------------
# Customization
# -----------------------------------------------------------------------------
homeassistant:
  customize:
    plant.{slug}:
      friendly_name: "{friendly}"

# -----------------------------------------------------------------------------
# Plant Entity
# -----------------------------------------------------------------------------
plant:
  {slug}:
    sensors:
      moisture: {moisture}
      temperature: {temperature}
      brightness: {brightness}
      conductivity: {conductivity}

# -----------------------------------------------------------------------------
# Threshold Sensors (recorded, UUID-based unique_ids)
# -----------------------------------------------------------------------------
template:
  - sensor:
      - name: "{display_pid} Light Min Lux"
        unique_id: "{uid('light_min_lux')}"
        state: "{min_light_lux if min_light_lux is not None else ''}"
        unit_of_measurement: "lx"

      - name: "{display_pid} Light Max Lux"
        unique_id: "{uid('light_max_lux')}"
        state: "{max_light_lux if max_light_lux is not None else ''}"
        unit_of_measurement: "lx"

      - name: "{display_pid} Temp Min"
        unique_id: "{uid('temp_min')}"
        state: "{min_temp if min_temp is not None else ''}"
        unit_of_measurement: "°C"

      - name: "{display_pid} Temp Max"
        unique_id: "{uid('temp_max')}"
        state: "{max_temp if max_temp is not None else ''}"
        unit_of_measurement: "°C"

      - name: "{display_pid} Humidity Min"
        unique_id: "{uid('humidity_min')}"
        state: "{min_humid if min_humid is not None else ''}"
        unit_of_measurement: "%"

      - name: "{display_pid} Humidity Max"
        unique_id: "{uid('humidity_max')}"
        state: "{max_humid if max_humid is not None else ''}"
        unit_of_measurement: "%"

      - name: "{display_pid} Moisture Min"
        unique_id: "{uid('moisture_min')}"
        state: "{min_moist if min_moist is not None else ''}"
        unit_of_measurement: "%"

      - name: "{display_pid} Moisture Max"
        unique_id: "{uid('moisture_max')}"
        state: "{max_moist if max_moist is not None else ''}"
        unit_of_measurement: "%"

      - name: "{display_pid} EC Min"
        unique_id: "{uid('ec_min')}"
        state: "{min_ec if min_ec is not None else ''}"
        unit_of_measurement: "µS/cm"

      - name: "{display_pid} EC Max"
        unique_id: "{uid('ec_max')}"
        state: "{max_ec if max_ec is not None else ''}"
        unit_of_measurement: "µS/cm"

# -----------------------------------------------------------------------------
# Binary Sensors: Status Indicators (recorded, UUID-based unique_ids)
# -----------------------------------------------------------------------------
  - binary_sensor:
      - name: "{display_pid} Temperature OK"
        unique_id: "{uid('temperature_ok')}"
        device_class: problem
        state: >-
          {{% from 'units/base.jinja' import u_convert_entity %}}
          {{% set t = u_convert_entity('{temperature}', 'c')|float(none) %}}
          {{% set tmin = states('sensor.{slug}_temp_min')|float(none) %}}
          {{% set tmax = states('sensor.{slug}_temp_max')|float(none) %}}
          {{{{ t is not none and tmin is not none and tmax is not none and (tmin <= t <= tmax) }}}}

      - name: "{display_pid} Light OK"
        unique_id: "{uid('light_ok')}"
        device_class: problem
        state: >-
          {{% set l = states('{brightness}')|float(none) %}}
          {{% set lmin = states('sensor.{slug}_light_min_lux')|float(none) %}}
          {{% set lmax = states('sensor.{slug}_light_max_lux')|float(none) %}}
          {{{{ l is not none and lmin is not none and lmax is not none and (lmin <= l <= lmax) }}}}

      - name: "{display_pid} Moisture OK"
        unique_id: "{uid('moisture_ok')}"
        device_class: problem
        state: >-
          {{% set m = states('{moisture}')|float(none) %}}
          {{% set mmin = states('sensor.{slug}_moisture_min')|float(none) %}}
          {{% set mmax = states('sensor.{slug}_moisture_max')|float(none) %}}
          {{{{ m is not none and mmin is not none and mmax is not none and (mmin <= m <= mmax) }}}}

      - name: "{display_pid} EC OK"
        unique_id: "{uid('ec_ok')}"
        device_class: problem
        state: >-
          {{% set e = states('{conductivity}')|float(none) %}}
          {{% set emin = states('sensor.{slug}_ec_min')|float(none) %}}
          {{% set emax = states('sensor.{slug}_ec_max')|float(none) %}}
          {{{{ e is not none and emin is not none and emax is not none and (emin <= e <= emax) }}}}

      - name: "{display_pid} All OK"
        unique_id: "{uid('all_ok')}"
        device_class: problem
        state: >-
          {{{{ is_state('binary_sensor.{slug}_temperature_ok','on')
             and is_state('binary_sensor.{slug}_light_ok','on')
             and is_state('binary_sensor.{slug}_moisture_ok','on')
             and is_state('binary_sensor.{slug}_ec_ok','on') }}}}

# -----------------------------------------------------------------------------
# Care Notes Sensor (recorded, UUID-based unique_id)
# -----------------------------------------------------------------------------
  - sensor:
      - name: "{display_pid} Care Notes"
        unique_id: "{uid('care_notes')}"
        icon: mdi:leaf
        state: >-
          {{% from 'units/base.jinja' import u_convert_value, u_convert_entity, u_humanize_value, u_humanize_entity %}}
          {{% set ns = namespace(out=[]) %}}
          {{% set t = u_convert_entity('{temperature}', 'c')|float(none) %}}
          {{% set l = states('{brightness}')|float(none) %}}
          {{% set m = states('{moisture}')|float(none) %}}
          {{% set e = states('{conductivity}')|float(none) %}}
          {{% set tmin = states('sensor.{slug}_temp_min')|float(none) %}}
          {{% set tmax = states('sensor.{slug}_temp_max')|float(none) %}}
          {{% set tminf = u_humanize_value(u_convert_entity('sensor.{slug}_temp_min', 'f'), '°F') -%}}
          {{% set tmaxf = u_humanize_value(u_convert_entity('sensor.{slug}_temp_max', 'f'), '°F') -%}}
          {{% set lmin = states('sensor.{slug}_light_min_lux')|float(none) %}}
          {{% set lmax = states('sensor.{slug}_light_max_lux')|float(none) %}}
          {{% set mmin = states('sensor.{slug}_moisture_min')|float(none) %}}
          {{% set mmax = states('sensor.{slug}_moisture_max')|float(none) %}}
          {{% set emin = states('sensor.{slug}_ec_min')|float(none) %}}
          {{% set emax = states('sensor.{slug}_ec_max')|float(none) %}}
          {{% if t is not none and (t < tmin or t > tmax) %}}
            {{% if t < tmin %}}
              {{% set ns.out = ns.out + ['Warm environment to ' ~ u_humanize_value(tmin,'°C') ~ '–' ~ u_humanize_value(tmax,'°C') ~ ' (' ~ tminf ~ '–' ~ tmaxf ~ ').'] %}}
            {{% else %}}
              {{% set ns.out = ns.out + ['Cool environment to ' ~ u_humanize_value(tmin,'°C') ~ '–' ~ u_humanize_value(tmax,'°C') ~ ' (' ~ tminf ~ '–' ~ tmaxf ~ ').'] %}}
            {{% endif %}}
          {{% endif %}}
          {{% if l is not none and (l < lmin or l > lmax) %}}
            {{% if l < lmin %}}
              {{% set ns.out = ns.out + ['Increase light toward ' ~ u_humanize_value(lmin) ~ '–' ~ u_humanize_value(lmax,'lx') ~ '.'] %}}
            {{% else %}}
              {{% set ns.out = ns.out + ['Reduce direct light; target ' ~ u_humanize_value(lmin) ~ '–' ~ u_humanize_value(lmax,'lx') ~ '.'] %}}
            {{% endif %}}
          {{% endif %}}
          {{% if m is not none and (m < mmin or m > mmax) %}}
            {{% if m < mmin %}}
              {{% set ns.out = ns.out + ['Water thoroughly; maintain soil moisture ' ~ u_humanize_value(mmin,'%') ~ '–' ~ u_humanize_value(mmax,'%') ~ '.'] %}}
            {{% else %}}
              {{% set ns.out = ns.out + ['Allow soil to dry slightly; keep ' ~ u_humanize_value(mmin,'%') ~ '–' ~ u_humanize_value(mmax,'%') ~ '.'] %}}
            {{% endif %}}
          {{% endif %}}
          {{% if e is not none and (e < emin or e > emax) %}}
            {{% if e < emin %}}
              {{% set ns.out = ns.out + ['Feed lightly; EC ' ~ u_humanize_value(emin) ~ '–' ~ u_humanize_value(emax) ~ ' µS/cm.'] %}}
            {{% else %}}
              {{% set ns.out = ns.out + ['Flush to reduce salts; resume gentle feeding.'] %}}
            {{% endif %}}
          {{% endif %}}
          {{{{ (ns.out | join('\\n')) if ns.out else 'Optimal. Maintain current care.' }}}}
        attributes:
{care_attrs_yaml}

# -----------------------------------------------------------------------------
# UI Sensors: Dashboard Lookups (no unique_id, snake_case names)
# These sensors store pre-computed card attributes for dashboard use.
# Dashboards reference these via state_attr() for zero Jinja in YAML cards.
# -----------------------------------------------------------------------------
  - trigger:
      - platform: state
        entity_id:
          - sensor.{slug}_temperature_routed
          - binary_sensor.{slug}_temperature_ok
          - sensor.{slug}_temp_min
          - sensor.{slug}_temp_max
    sensor:
      - name: ui_{slug}_temperature_card
        state: "{{{{ states('sensor.{slug}_temperature_routed') }}}}"
        attributes:
          primary: Temperature
          secondary: >-
            {{%- from 'units/base.jinja' import u_convert_value, u_humanize_value, u_humanize_entity -%}}
            {{%- set temp_min_f = u_humanize_value(u_convert_value(states('sensor.{slug}_temp_min'), 'c', 'f'), '°F') -%}}
            {{%- set temp_max_f = u_humanize_value(u_convert_value(states('sensor.{slug}_temp_max'), 'c', 'f'), '°F') -%}}
            {{{{ 'Current: ' ~ u_humanize_entity('sensor.{slug}_temperature_routed') }}}}
            {{{{ '\\nRange: ' ~ temp_min_f ~ '–' ~ temp_max_f }}}}
          icon: mdi:thermometer
          icon_color: "{{{{ 'green' if is_state('binary_sensor.{slug}_temperature_ok','on') else 'red' }}}}"

  - trigger:
      - platform: state
        entity_id:
          - sensor.{slug}_illuminance_routed
          - binary_sensor.{slug}_light_ok
          - sensor.{slug}_light_min_lux
          - sensor.{slug}_light_max_lux
    sensor:
      - name: ui_{slug}_light_card
        state: "{{{{ states('sensor.{slug}_illuminance_routed') }}}}"
        attributes:
          primary: Light
          secondary: >-
            {{%- from 'units/base.jinja' import u_humanize_entity, u_humanize_value -%}}
            {{%- set light_min_lux = u_humanize_value(states('sensor.{slug}_light_min_lux')) -%}}
            {{%- set light_max_lux = u_humanize_value(states('sensor.{slug}_light_max_lux'), 'lx') -%}}
            {{{{ 'Current: ' ~ u_humanize_entity('sensor.{slug}_illuminance_routed') }}}}
            {{{{ '\\nRange: ' ~ light_min_lux ~ '–' ~ light_max_lux }}}}
          icon: mdi:white-balance-sunny
          icon_color: "{{{{ 'green' if is_state('binary_sensor.{slug}_light_ok','on') else 'red' }}}}"

  - trigger:
      - platform: state
        entity_id:
          - sensor.{slug}_moisture_routed
          - binary_sensor.{slug}_moisture_ok
          - sensor.{slug}_moisture_min
          - sensor.{slug}_moisture_max
    sensor:
      - name: ui_{slug}_moisture_card
        state: "{{{{ states('sensor.{slug}_moisture_routed') }}}}"
        attributes:
          primary: Moisture
          secondary: >-
            {{%- from 'units/base.jinja' import u_humanize_entity, u_humanize_value -%}}
            {{%- set moist_min_pct = u_humanize_value(states('sensor.{slug}_moisture_min'), '%') -%}}
            {{%- set moist_max_pct = u_humanize_value(states('sensor.{slug}_moisture_max'), '%') -%}}
            {{{{ 'Current: ' ~ u_humanize_entity('sensor.{slug}_moisture_routed') }}}}
            {{{{ '\\nRange: ' ~ moist_min_pct ~ '–' ~ moist_max_pct }}}}
          icon: mdi:water-percent
          icon_color: "{{{{ 'green' if is_state('binary_sensor.{slug}_moisture_ok','on') else 'red' }}}}"

  - trigger:
      - platform: state
        entity_id:
          - sensor.{slug}_conductivity_routed
          - binary_sensor.{slug}_ec_ok
          - sensor.{slug}_ec_min
          - sensor.{slug}_ec_max
    sensor:
      - name: ui_{slug}_conductivity_card
        state: "{{{{ states('sensor.{slug}_conductivity_routed') }}}}"
        attributes:
          primary: Conductivity
          secondary: >-
            {{%- from 'units/base.jinja' import u_humanize_entity, u_humanize_value -%}}
            {{%- set cond_min_uscm = u_humanize_value(states('sensor.{slug}_ec_min')) -%}}
            {{%- set cond_max_uscm = u_humanize_value(states('sensor.{slug}_ec_max')) -%}}
            {{{{ 'Current: ' ~ u_humanize_entity('sensor.{slug}_conductivity_routed') }}}}
            {{{{ '\\nRange: ' ~ cond_min_uscm ~ '–' ~ cond_max_uscm ~ ' µS/cm' }}}}
          icon: mdi:flash
          icon_color: "{{{{ 'green' if is_state('binary_sensor.{slug}_ec_ok','on') else 'red' }}}}"

  - trigger:
      - platform: state
        entity_id: binary_sensor.{slug}_all_ok
    sensor:
      - name: ui_{slug}_overall_chip
        state: "{{{{ states('binary_sensor.{slug}_all_ok') }}}}"
        attributes:
          content: "{{{{ 'All Good' if is_state('binary_sensor.{slug}_all_ok', 'on') else 'Needs Attention' }}}}"
          icon: "{{{{ 'mdi:check-circle' if is_state('binary_sensor.{slug}_all_ok','on') else 'mdi:alert-circle' }}}}"
          icon_color: "{{{{ 'green' if is_state('binary_sensor.{slug}_all_ok','on') else 'red' }}}}"

  - trigger:
      - platform: state
        entity_id: binary_sensor.{slug}_light_ok
    sensor:
      - name: ui_{slug}_light_chip
        state: "{{{{ states('binary_sensor.{slug}_light_ok') }}}}"
        attributes:
          content: "{{{{ 'Light: OK' if is_state('binary_sensor.{slug}_light_ok', 'on') else 'Light: Problem' }}}}"
          icon: "{{{{ 'mdi:check-circle' if is_state('binary_sensor.{slug}_light_ok','on') else 'mdi:alert-circle' }}}}"
          icon_color: "{{{{ 'green' if is_state('binary_sensor.{slug}_light_ok','on') else 'red' }}}}"

  - trigger:
      - platform: state
        entity_id: binary_sensor.{slug}_temperature_ok
    sensor:
      - name: ui_{slug}_temperature_chip
        state: "{{{{ states('binary_sensor.{slug}_temperature_ok') }}}}"
        attributes:
          content: "{{{{ 'Temp: OK' if is_state('binary_sensor.{slug}_temperature_ok', 'on') else 'Temp: Problem' }}}}"
          icon: "{{{{ 'mdi:check-circle' if is_state('binary_sensor.{slug}_temperature_ok','on') else 'mdi:alert-circle' }}}}"
          icon_color: "{{{{ 'green' if is_state('binary_sensor.{slug}_temperature_ok','on') else 'red' }}}}"

  - trigger:
      - platform: state
        entity_id: binary_sensor.{slug}_moisture_ok
    sensor:
      - name: ui_{slug}_moisture_chip
        state: "{{{{ states('binary_sensor.{slug}_moisture_ok') }}}}"
        attributes:
          content: "{{{{ 'Moisture: OK' if is_state('binary_sensor.{slug}_moisture_ok', 'on') else 'Moisture: Problem' }}}}"
          icon: "{{{{ 'mdi:check-circle' if is_state('binary_sensor.{slug}_moisture_ok','on') else 'mdi:alert-circle' }}}}"
          icon_color: "{{{{ 'green' if is_state('binary_sensor.{slug}_moisture_ok','on') else 'red' }}}}"

  - trigger:
      - platform: state
        entity_id: binary_sensor.{slug}_ec_ok
    sensor:
      - name: ui_{slug}_conductivity_chip
        state: "{{{{ states('binary_sensor.{slug}_ec_ok') }}}}"
        attributes:
          content: "{{{{ 'EC: OK' if is_state('binary_sensor.{slug}_ec_ok', 'on') else 'EC: Problem' }}}}"
          icon: "{{{{ 'mdi:check-circle' if is_state('binary_sensor.{slug}_ec_ok','on') else 'mdi:alert-circle' }}}}"
          icon_color: "{{{{ 'green' if is_state('binary_sensor.{slug}_ec_ok','on') else 'red' }}}}"

  - trigger:
      - platform: state
        entity_id:
          - binary_sensor.{slug}_all_ok
          - sensor.{slug}_care_notes
    sensor:
      - name: ui_{slug}_care_summary
        state: "{{{{ states('sensor.{slug}_care_notes') }}}}"
        attributes:
          overall_status: "{{{{ 'All Good!' if is_state('binary_sensor.{slug}_all_ok', 'on') else 'Needs Attention' }}}}"
          care_notes: "{{{{ states('sensor.{slug}_care_notes') }}}}"
          sunlight: "{{{{ state_attr('sensor.{slug}_care_notes','sunlight') or '—' }}}}"
          watering: "{{{{ state_attr('sensor.{slug}_care_notes','watering') or '—' }}}}"
          fertilization: "{{{{ state_attr('sensor.{slug}_care_notes','fertilization') or '—' }}}}"
          pruning: "{{{{ state_attr('sensor.{slug}_care_notes','pruning') or '—' }}}}"
          soil: "{{{{ state_attr('sensor.{slug}_care_notes','soil') or '—' }}}}"
          notes: "{{{{ state_attr('sensor.{slug}_care_notes','floral_language') or '—' }}}}"
"""
    return yaml


# -----------------------------------------------------------------------------
# Dashboard Section Generation
# -----------------------------------------------------------------------------

def build_dashboard_section(row: Dict[str, Any]) -> str:
    """Build dashboard section YAML that uses only ui_* sensor lookups."""
    pid = row["pid"]
    scientific = (row.get("display_pid") or pid).strip()
    alias = best_common_name(scientific) or (row.get("alias") or "").strip()
    common = alias.title() if alias else scientific
    slug = slugify(pid)
    image_path = f"local/Images/{pid}.jpg"

    def _dq(text: str) -> str:
        return text.replace("\\", "\\\\").replace('"', '\\"')

    common_q = _dq(common)
    scientific_q = _dq(scientific)

    # Dashboard section using only state_attr() lookups - no inline Jinja
    section = f"""\
# -----------------------------------------------------------------------------
# Dashboard Section: {common} ({scientific})
# Generated by generate_plant_assets.py
# All dynamic values use state_attr() lookups on ui_* sensors
# -----------------------------------------------------------------------------
type: horizontal-stack
cards:
  - type: vertical-stack
    cards:

      # Title Card
      - type: custom:mushroom-title-card
        title: "{common_q}"
        subtitle: "{scientific_q}"

      # Status Chips
      - type: custom:mushroom-chips-card
        alignment: center
        chips:
          - type: template
            entity: binary_sensor.{slug}_all_ok
            content: "{{{{ state_attr('sensor.ui_{slug}_overall_chip', 'content') }}}}"
            icon: "{{{{ state_attr('sensor.ui_{slug}_overall_chip', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_overall_chip', 'icon_color') }}}}"
          - type: template
            entity: binary_sensor.{slug}_light_ok
            content: "{{{{ state_attr('sensor.ui_{slug}_light_chip', 'content') }}}}"
            icon: "{{{{ state_attr('sensor.ui_{slug}_light_chip', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_light_chip', 'icon_color') }}}}"
          - type: template
            entity: binary_sensor.{slug}_temperature_ok
            content: "{{{{ state_attr('sensor.ui_{slug}_temperature_chip', 'content') }}}}"
            icon: "{{{{ state_attr('sensor.ui_{slug}_temperature_chip', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_temperature_chip', 'icon_color') }}}}"
          - type: template
            entity: binary_sensor.{slug}_moisture_ok
            content: "{{{{ state_attr('sensor.ui_{slug}_moisture_chip', 'content') }}}}"
            icon: "{{{{ state_attr('sensor.ui_{slug}_moisture_chip', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_moisture_chip', 'icon_color') }}}}"
          - type: template
            entity: binary_sensor.{slug}_ec_ok
            content: "{{{{ state_attr('sensor.ui_{slug}_conductivity_chip', 'content') }}}}"
            icon: "{{{{ state_attr('sensor.ui_{slug}_conductivity_chip', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_conductivity_chip', 'icon_color') }}}}"

      # Metrics Grid
      - type: grid
        square: false
        columns: 2
        cards:

          # Temperature Card
          - type: custom:mushroom-template-card
            entity: sensor.{slug}_temperature_routed
            primary: "{{{{ state_attr('sensor.ui_{slug}_temperature_card', 'primary') }}}}"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_temperature_card', 'secondary') }}}}"
            icon: "{{{{ state_attr('sensor.ui_{slug}_temperature_card', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_temperature_card', 'icon_color') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info

          # Light Card
          - type: custom:mushroom-template-card
            entity: sensor.{slug}_illuminance_routed
            primary: "{{{{ state_attr('sensor.ui_{slug}_light_card', 'primary') }}}}"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_light_card', 'secondary') }}}}"
            icon: "{{{{ state_attr('sensor.ui_{slug}_light_card', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_light_card', 'icon_color') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info

          # Moisture Card
          - type: custom:mushroom-template-card
            entity: sensor.{slug}_moisture_routed
            primary: "{{{{ state_attr('sensor.ui_{slug}_moisture_card', 'primary') }}}}"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_moisture_card', 'secondary') }}}}"
            icon: "{{{{ state_attr('sensor.ui_{slug}_moisture_card', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_moisture_card', 'icon_color') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info

          # Conductivity Card
          - type: custom:mushroom-template-card
            entity: sensor.{slug}_conductivity_routed
            primary: "{{{{ state_attr('sensor.ui_{slug}_conductivity_card', 'primary') }}}}"
            secondary: "{{{{ state_attr('sensor.ui_{slug}_conductivity_card', 'secondary') }}}}"
            icon: "{{{{ state_attr('sensor.ui_{slug}_conductivity_card', 'icon') }}}}"
            icon_color: "{{{{ state_attr('sensor.ui_{slug}_conductivity_card', 'icon_color') }}}}"
            multiline_secondary: true
            tap_action:
              action: more-info

      # Care Summary
      - type: markdown
        content: >
          **{{{{ state_attr('sensor.ui_{slug}_care_summary', 'overall_status') }}}}:**
          {{{{ state_attr('sensor.ui_{slug}_care_summary', 'care_notes') }}}}

          ---

          **Sunlight:** {{{{ state_attr('sensor.ui_{slug}_care_summary', 'sunlight') }}}}

          **Watering:** {{{{ state_attr('sensor.ui_{slug}_care_summary', 'watering') }}}}

          **Fertilization:** {{{{ state_attr('sensor.ui_{slug}_care_summary', 'fertilization') }}}}

          **Pruning:** {{{{ state_attr('sensor.ui_{slug}_care_summary', 'pruning') }}}}

          **Soil:** {{{{ state_attr('sensor.ui_{slug}_care_summary', 'soil') }}}}

          **Notes:** {{{{ state_attr('sensor.ui_{slug}_care_summary', 'notes') }}}}

  # Plant Photo
  - type: picture
    image: "{image_path}"
"""
    return section


# -----------------------------------------------------------------------------
# Router Package Generation
# -----------------------------------------------------------------------------

ROUTER_HEADER = """\
# =============================================================================
# MiFlora Plant Probe Routing Package
# =============================================================================
#
# Generated by generate_plant_assets.py
#
# This package routes a single MiFlora probe to multiple plant entities via
# input_select. Each plant gets routed sensors that are only available when
# that plant is selected.
#
# Entities created:
#   - input_select.plant_sensor_location
#   - sensor.miflora_temperature_f, sensor.miflora_illuminance, etc.
#   - sensor.<plant>_temperature_routed, sensor.<plant>_illuminance_routed, etc.
#
# =============================================================================
"""


def build_router_package(rows: List[Dict[str, Any]], mif_temp: str, mif_lux: str, mif_moist: str, mif_ec: str) -> str:
    """Build the central MiFlora router package."""
    names = [r["pid"] for r in rows if r.get("pid")]
    options_yaml = "\n".join([f"      - {n.lower()}" for n in sorted(names, key=lambda x: x.lower())])

    routed_sensors = []
    for row in rows:
        pid = row["pid"]
        slug = slugify(pid)
        sel = pid.lower()
        display_pid = row.get("display_pid") or pid.title()

        routed_sensors.append(f"""
      - name: "{display_pid} Temperature Routed"
        unique_id: "{make_uuid(slug, 'temperature_routed')}"
        state: "{{{{ states('{mif_temp}') }}}}"
        availability: "{{{{ is_state('input_select.plant_sensor_location','{sel}') and has_value('{mif_temp}') }}}}"
        unit_of_measurement: "°F"

      - name: "{display_pid} Illuminance Routed"
        unique_id: "{make_uuid(slug, 'illuminance_routed')}"
        state: "{{{{ states('{mif_lux}') }}}}"
        availability: "{{{{ is_state('input_select.plant_sensor_location','{sel}') and has_value('{mif_lux}') }}}}"
        unit_of_measurement: "lx"

      - name: "{display_pid} Moisture Routed"
        unique_id: "{make_uuid(slug, 'moisture_routed')}"
        state: "{{{{ states('{mif_moist}') }}}}"
        availability: "{{{{ is_state('input_select.plant_sensor_location','{sel}') and has_value('{mif_moist}') }}}}"
        unit_of_measurement: "%"

      - name: "{display_pid} Conductivity Routed"
        unique_id: "{make_uuid(slug, 'conductivity_routed')}"
        state: "{{{{ states('{mif_ec}') }}}}"
        availability: "{{{{ is_state('input_select.plant_sensor_location','{sel}') and has_value('{mif_ec}') }}}}"
        unit_of_measurement: "µS/cm"
""")

    routed_yaml = "".join(routed_sensors)

    pkg = f"""{ROUTER_HEADER}
# -----------------------------------------------------------------------------
# Input Select: Probe Location
# -----------------------------------------------------------------------------
input_select:
  plant_sensor_location:
    name: "MiFlora Probe Location"
    icon: mdi:leaf-maple
    options:
{options_yaml}

# -----------------------------------------------------------------------------
# MiFlora Mirror Sensors (raw probe values)
# -----------------------------------------------------------------------------
template:
  - sensor:
      - name: "MiFlora Temperature F"
        unique_id: "{make_uuid('miflora', 'temperature_f')}"
        availability: "{{{{ has_value('{mif_temp}') }}}}"
        state: "{{{{ states('{mif_temp}') }}}}"
        unit_of_measurement: "°F"

      - name: "MiFlora Illuminance"
        unique_id: "{make_uuid('miflora', 'illuminance')}"
        availability: "{{{{ has_value('{mif_lux}') }}}}"
        state: "{{{{ states('{mif_lux}') }}}}"
        unit_of_measurement: "lx"

      - name: "MiFlora Moisture"
        unique_id: "{make_uuid('miflora', 'moisture')}"
        availability: "{{{{ has_value('{mif_moist}') }}}}"
        state: "{{{{ states('{mif_moist}') }}}}"
        unit_of_measurement: "%"

      - name: "MiFlora Conductivity"
        unique_id: "{make_uuid('miflora', 'conductivity')}"
        availability: "{{{{ has_value('{mif_ec}') }}}}"
        state: "{{{{ states('{mif_ec}') }}}}"
        unit_of_measurement: "µS/cm"

# -----------------------------------------------------------------------------
# Routed Sensors (per-plant, available only when selected)
# -----------------------------------------------------------------------------
  - sensor:{routed_yaml}
"""
    return pkg


# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Generate Home Assistant plant packages and dashboard sections")
    ap.add_argument("--csv", required=True, help="Path to plant database CSV")
    ap.add_argument("--names", nargs="+", required=True, help="One or more scientific names (pid)")
    ap.add_argument("--out-packages", default="./packages", help="Output folder for package YAMLs")
    ap.add_argument("--out-sections", default="./sections", help="Output folder for dashboard section YAMLs")
    ap.add_argument("--sensor-map", default=None, help="Optional JSON mapping of slug -> sensor entities")
    ap.add_argument("--miflora-temperature", default="sensor.plant_sensor_d455_temperature",
                    help="Entity id of the MiFlora temperature (°F)")
    ap.add_argument("--miflora-illuminance", default="sensor.plant_sensor_d455_illuminance",
                    help="Entity id of the MiFlora illuminance (lx)")
    ap.add_argument("--miflora-moisture", default="sensor.plant_sensor_d455_moisture",
                    help="Entity id of the MiFlora moisture (%%)")
    ap.add_argument("--miflora-conductivity", default="sensor.plant_sensor_d455_conductivity",
                    help="Entity id of the MiFlora conductivity (µS/cm)")
    ap.add_argument("--router-file", default="./packages/plant_sensor_router.yaml",
                    help="Output path for the generated MiFlora router package")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        sys.exit(f"CSV not found: {csv_path}")

    ensure_dir(Path(args.out_packages))
    ensure_dir(Path(args.out_sections))

    wanted = {slugify(n) for n in args.names}
    sensor_map = load_sensor_map(Path(args.sensor_map)) if args.sensor_map else {}

    rows: List[Dict[str, Any]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            slug = slugify(row.get("pid", ""))
            if slug in wanted:
                rows.append(row)

    if not rows:
        sys.exit("No matching plants found. Check your --names against the 'pid' column.")

    # Write per-plant packages & sections
    for row in rows:
        slug = slugify(row["pid"])
        sensors = sensor_map.get(slug, {})
        pkg_yaml = build_package_yaml(row, sensors)
        sec_yaml = build_dashboard_section(row)

        pkg_file = Path(args.out_packages) / f"{slug}.yaml"
        sec_file = Path(args.out_sections) / f"{slug}_section.yaml"
        pkg_file.write_text(pkg_yaml, encoding="utf-8")
        sec_file.write_text(sec_yaml, encoding="utf-8")
        print(f"Wrote {pkg_file}")
        print(f"Wrote {sec_file}")

    # Write central MiFlora router package
    router_yaml = build_router_package(
        rows,
        mif_temp=args.miflora_temperature,
        mif_lux=args.miflora_illuminance,
        mif_moist=args.miflora_moisture,
        mif_ec=args.miflora_conductivity,
    )
    router_path = Path(args.router_file)
    ensure_dir(router_path.parent)
    router_path.write_text(router_yaml, encoding="utf-8")
    print(f"Wrote {router_path}")


if __name__ == "__main__":
    main()
