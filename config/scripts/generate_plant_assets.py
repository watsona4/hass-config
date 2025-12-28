#!/usr/bin/env python3
"""
generate_plant_assets.py — generate HA plant packages and dashboard sections
(Bodhi-style sections)

- Title uses the common name (alias) when available; subtitle shows scientific name
- Local images: /local/Images/<scientific_slug>.jpg
- Gauge 'max' Jinja is quoted
- Multiline-safe YAML attributes + mojibake repair
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from textwrap import indent
from typing import Any, Dict, List, Optional

import requests


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def to_float(v, default=None):
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def load_sensor_map(path: Path) -> Dict[str, Dict[str, str]]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def fix_mojibake(text: Optional[str]) -> str:
    if text is None:
        return ""
    if any(ch in text for ch in ("â", "Ã", "€")):
        try:
            return text.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            return text
    return text


def yaml_attr(key: str, value: Optional[str], indent_spaces: int = 10) -> str:
    # Repair encoding glitches first
    raw = fix_mojibake(value or "").strip()
    # Normalize line endings to LF
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Turn literal backslash-n sequences into real newlines
    text = text.replace("\\n", "\n")
    # Handle Unicode line/paragraph separators as newlines
    text = text.replace("\u2028", "\n").replace("\u2029", "\n")

    pad = " " * indent_spaces
    if text == "":
        return f'{pad}{key}: ""'

    if "\n" in text:
        # Emit a proper block scalar with correctly indented lines
        lines = "\n".join((" " * (indent_spaces + 2)) + ln for ln in text.split("\n"))
        return f"{pad}{key}: |-\n{lines}"

    # Single-line: quote and escape safely
    v = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'{pad}{key}: "{v}"'


ISO_LANG_MAP = {
    "en": "eng",
    "es": "spa",
    "fr": "fra",
    "de": "deu",
    "it": "ita",
    "pt": "por",
    "zh": "zho",
    "ja": "jpn",
    "ko": "kor",
}


def _match_lang_codes(lang: str) -> set[str]:
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
    """Use GBIF to get a vernacular name for a scientific name.

    Preference order:
      1. Matching language + country (when both exist on the record)
      2. Matching language
      3. Any available vernacular name
    """
    s = requests.Session()
    # 1) species/match → usageKey
    r = s.get("https://api.gbif.org/v1/species/match", params={"name": scientific}, timeout=timeout)
    r.raise_for_status()
    key = r.json().get("usageKey")
    if not key:
        return None
    # 2) vernacularNames for that key
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

    # 1. Language + country match
    if lang_codes and country_code:
        match = _pick(
            lambda entry: entry.get("language", "").lower() in lang_codes
            and entry.get("country", "").upper() == country_code
        )
        if match:
            return match

    # 2. Language-only match
    if lang_codes:
        match = _pick(lambda entry: entry.get("language", "").lower() in lang_codes)
        if match:
            return match

    # 3. Country-only match
    if country_code:
        match = _pick(lambda entry: entry.get("country", "").upper() == country_code)
        if match:
            return match

    # 4. Fallback to any available vernacular name
    any_name = _pick(lambda entry: True)
    return any_name


def get_common_name_wikidata(scientific: str, lang="en", timeout=8) -> str | None:
    """Query Wikidata for an English label / vernacular name by exact scientific name (P225)."""
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
    # prefer vernacular (P1843), else English label
    for b in data:
        if "vname" in b:
            return b["vname"]["value"]
    if data and "itemLabel" in data[0]:
        return data[0]["itemLabel"]["value"]
    return None


def best_common_name(scientific: str, lang="en", country: str | None = "US") -> str | None:
    """GBIF first (language+country preferences), then Wikidata (language only)."""
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


PACKAGE_HEADER = """\
###############################################################################
# Plant care package: {display_name} ({pid})
# Generated by generate_plant_assets.py
###############################################################################
"""


def build_package_yaml(row: Dict[str, Any], sensors: Dict[str, str]) -> str:
    pid = row["pid"]
    display_pid = row.get("display_pid") or pid.title()
    slug = slugify(pid)
    friendly = f"{display_pid}"
    image = (row.get("image") or "").strip()

    min_light_mmol = to_float(row.get("min_light_mmol"))
    max_light_mmol = to_float(row.get("max_light_mmol"))
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

    # Route through central MiFlora selector (one probe shared among plants)
    moisture = sensors.get("moisture", f"sensor.{slug}_moisture_routed")
    temperature = sensors.get("temperature", f"sensor.{slug}_temperature_routed")
    brightness = sensors.get("brightness", f"sensor.{slug}_illuminance_routed")
    conductivity = sensors.get("conductivity", f"sensor.{slug}_conductivity_routed")

    constants_block = f"""\
# ---------------- thresholds from CSV (edit freely) ----------------
# Light mmol: min={min_light_mmol or 'null'}, max={max_light_mmol or 'null'}
# Light lux:  min={min_light_lux or 'null'},  max={max_light_lux or 'null'}
# Temp C:     min={min_temp or 'null'},       max={max_temp or 'null'}
# Humidity %: min={min_humid or 'null'},      max={max_humid or 'null'}
# Moisture%:  min={min_moist or 'null'},      max={max_moist or 'null'}
# EC µS/cm:   min={min_ec or 'null'},         max={max_ec or 'null'}
"""

    yaml = f"""{PACKAGE_HEADER.format(display_name=display_pid, pid=pid)}\
homeassistant:
  customize:
    plant.{slug}:
      friendly_name: "{friendly}"

plant:
  {slug}:
    sensors:
      moisture: {moisture}
      temperature: {temperature}
      brightness: {brightness}
      conductivity: {conductivity}

template:
  - sensor:
      - name: "{display_pid} Light Min Lux"
        unique_id: "{slug}_light_min_lux"
        state: "{min_light_lux if min_light_lux is not None else ''}"
        unit_of_measurement: "lx"
      - name: "{display_pid} Light Max Lux"
        unique_id: "{slug}_light_max_lux"
        state: "{max_light_lux if max_light_lux is not None else ''}"
        unit_of_measurement: "lx"
      - name: "{display_pid} Temp Min"
        unique_id: "{slug}_temp_min"
        state: "{min_temp if min_temp is not None else ''}"
        unit_of_measurement: "°C"
      - name: "{display_pid} Temp Max"
        unique_id: "{slug}_temp_max"
        state: "{max_temp if max_temp is not None else ''}"
        unit_of_measurement: "°C"
      - name: "{display_pid} Humidity Min"
        unique_id: "{slug}_humid_min"
        state: "{min_humid if min_humid is not None else ''}"
        unit_of_measurement: "%"
      - name: "{display_pid} Humidity Max"
        unique_id: "{slug}_humid_max"
        state: "{max_humid if max_humid is not None else ''}"
        unit_of_measurement: "%"
      - name: "{display_pid} Moisture Min"
        unique_id: "{slug}_moist_min"
        state: "{min_moist if min_moist is not None else ''}"
        unit_of_measurement: "%"
      - name: "{display_pid} Moisture Max"
        unique_id: "{slug}_moist_max"
        state: "{max_moist if max_moist is not None else ''}"
        unit_of_measurement: "%"
      - name: "{display_pid} EC Min"
        unique_id: "{slug}_ec_min"
        state: "{min_ec if min_ec is not None else ''}"
        unit_of_measurement: "µS/cm"
      - name: "{display_pid} EC Max"
        unique_id: "{slug}_ec_max"
        state: "{max_ec if max_ec is not None else ''}"
        unit_of_measurement: "µS/cm"

  - sensor:
      - name: ui_{slug}_temperature_routed
        state: "{{{{ states('sensor.{slug}_temperature_routed') }}}}"
        attributes:
          content: >
            {{%- from 'units/base.jinja' import u_convert_value, u_humanize_value, u_humanize_entity -%}}
            {{%- set temp_min_f = u_humanize_value(u_convert_value(states('sensor.{slug}_temp_min'), 'c', 'f'), '°F') -%}}
            {{%- set temp_max_f = u_humanize_value(u_convert_value(states('sensor.{slug}_temp_max'), 'c', 'f'), '°F') -%}}
            {{{{ 'Current: ' ~ u_humanize_entity(entity) }}}}
            {{{{ '\\nRange: ' ~ temp_min_f ~ '–' ~ temp_max_f }}}}
          color: "{{{{ 'green' if is_state('binary_sensor.{slug}_temperature_ok','on') else 'red' }}}}"
      - name: ui_{slug}_illuminance_routed
        state: "{{{{ states('sensor.{slug}_illuminance_routed') }}}}"
        attributes:
          content: >
            {{%- from 'units/base.jinja' import u_humanize_entity, u_humanize_value -%}}
            {{%- set light_min_lux = u_humanize_value(states('sensor.{slug}_light_min_lux')) -%}}
            {{%- set light_max_lux = u_humanize_value(states('sensor.{slug}_light_max_lux'), 'lx') -%}}
            {{{{ 'Current: ' ~ u_humanize_entity(entity) }}}}
            {{{{ '\\nRange: ' ~ light_min_lux ~ '–' ~ light_max_lux }}}}
          color: "{{{{ 'green' if is_state('binary_sensor.{slug}_light_ok','on') else 'red' }}}}"
      - name: ui_{slug}_moisture_routed
        state: "{{{{ states('sensor.{slug}_moisture_routed') }}}}"
        attributes:
          content: >
            {{%- from 'units/base.jinja' import u_humanize_entity, u_humanize_value -%}}
            {{%- set moist_min_pct = u_humanize_value(states('sensor.{slug}_moisture_min'), '%') -%}}
            {{%- set moist_max_pct = u_humanize_value(states('sensor.{slug}_moisture_max'), '%') -%}}
            {{{{ 'Current: ' ~ u_humanize_entity(entity) }}}}
            {{{{ '\\nRange: ' ~ moist_min_pct ~ '–' ~ moist_max_pct }}}}
          color: "{{{{ 'green' if is_state('binary_sensor.{slug}_moisture_ok','on') else 'red' }}}}"
      - name: ui_{slug}_conductivity_routed
        state: "{{{{ states('sensor.{slug}_conductivity_routed') }}}}"
        attributes:
          content: >
            {{%- from 'units/base.jinja' import u_humanize_entity, u_humanize_value -%}}
            {{%- set cond_min_uscm = u_humanize_value(states('sensor.{slug}_ec_min')) -%}}
            {{%- set cond_max_uscm = u_humanize_value(states('sensor.{slug}_ec_max')) -%}}
            {{{{ 'Current: ' ~ u_humanize_entity(entity) }}}}
            {{{{ '\\nRange: ' ~ cond_min_uscm ~ '–' ~ cond_max_uscm ~ ' µS/cm' }}}}
          color: "{{{{ 'green' if is_state('binary_sensor.{slug}_ec_ok','on') else 'red' }}}}"

  - binary_sensor:
      - name: "{display_pid} Temperature OK"
        unique_id: "{slug}_temp_ok"
        device_class: problem
        state: >-
          {{% from 'units/base.jinja' import u_convert_entity %}}
          {{% set t = u_convert_entity('{temperature.split()[0]}', 'c')|float(none) %}}
          {{% set tmin = states('sensor.{slug}_temp_min')|float(none) %}}
          {{% set tmax = states('sensor.{slug}_temp_max')|float(none) %}}
          {{{{ t is not none and tmin is not none and tmax is not none and (tmin <= t <= tmax) }}}}
      - name: "{display_pid} Light OK"
        unique_id: "{slug}_light_ok"
        device_class: problem
        state: >-
          {{% set l = states('{brightness.split()[0]}')|float(none) %}}
          {{% set lmin = states('sensor.{slug}_light_min_lux')|float(none) %}}
          {{% set lmax = states('sensor.{slug}_light_max_lux')|float(none) %}}
          {{{{ l is not none and lmin is not none and lmax is not none and (lmin <= l <= lmax) }}}}
      - name: "{display_pid} Moisture OK"
        unique_id: "{slug}_moist_ok"
        device_class: problem
        state: >-
          {{% set m = states('{moisture.split()[0]}')|float(none) %}}
          {{% set mmin = states('sensor.{slug}_moisture_min')|float(none) %}}
          {{% set mmax = states('sensor.{slug}_moisture_max')|float(none) %}}
          {{{{ m is not none and mmin is not none and mmax is not none and (mmin <= m <= mmax) }}}}
      - name: "{display_pid} EC OK"
        unique_id: "{slug}_ec_ok"
        device_class: problem
        state: >-
          {{% set e = states('{conductivity.split()[0]}')|float(none) %}}
          {{% set emin = states('sensor.{slug}_ec_min')|float(none) %}}
          {{% set emax = states('sensor.{slug}_ec_max')|float(none) %}}
          {{{{ e is not none and emin is not none and emax is not none and (emin <= e <= emax) }}}}
      - name: "{display_pid} All OK"
        unique_id: "{slug}_all_ok"
        device_class: problem
        state: >-
          {{{{ is_state('binary_sensor.{slug}_temperature_ok','on')
             and is_state('binary_sensor.{slug}_light_ok','on')
             and is_state('binary_sensor.{slug}_moisture_ok','on')
             and is_state('binary_sensor.{slug}_ec_ok','on') }}}}

  - sensor:
      - name: "{display_pid} Care Notes"
        unique_id: "{slug}_care_notes"
        icon: mdi:leaf
        state: >-
          {{% from 'units/base.jinja' import u_convert_value, u_convert_entity, u_humanize_value, u_humanize_entity %}}
          {{% set ns = namespace(out=[]) %}}
          {{% set t = u_convert_entity('{temperature.split()[0]}', 'c')|float(none) %}}
          {{% set l = states('{brightness.split()[0]}')|float(none) %}}
          {{% set m = states('{moisture.split()[0]}')|float(none) %}}
          {{% set e = states('{conductivity.split()[0]}')|float(none) %}}
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
              {{% set ns.out = ns.out + ['Reduce direct light; target ' ~ u_humanize_value(lmin) ~ '–' ~ u_humanize_value(lmax,'lx') ~ ' .'] %}}
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
{yaml_attr('image', image, 10)}
{yaml_attr('alias', row.get('alias'), 10)}
{yaml_attr('origin', row.get('origin'), 10)}
{yaml_attr('production', row.get('production'), 10)}
{yaml_attr('category', row.get('category'), 10)}
{yaml_attr('floral_language', row.get('floral_language'), 10)}
{yaml_attr('blooming', row.get('blooming'), 10)}
{yaml_attr('color', row.get('color'), 10)}
{yaml_attr('size', row.get('size'), 10)}
{yaml_attr('soil', row.get('soil'), 10)}
{yaml_attr('sunlight', row.get('sunlight'), 10)}
{yaml_attr('watering', row.get('watering'), 10)}
{yaml_attr('fertilization', row.get('fertilization'), 10)}
{yaml_attr('pruning', row.get('pruning'), 10)}

{indent(constants_block, '')}
"""
    return yaml


def build_dashboard_section(row: Dict[str, Any]) -> str:
    # Names
    pid = row["pid"]  # scientific name as-is (may include spaces)
    scientific = (row.get("display_pid") or pid).strip()
    alias = best_common_name(scientific) or (row.get("alias") or "").strip()
    common = alias.title() if alias else scientific

    # Entity slug
    slug = slugify(pid)

    # Match your Bodhi example image path style: local/Images/<scientific name>.jpg (spaces kept, no leading slash)
    image_path = f"local/Images/{pid}.jpg"

    # Escape helpers for YAML double-quoted strings
    def _dq(text: str) -> str:
        return text.replace("\\", "\\\\").replace('"', '\\"')

    common_q = _dq(common)
    scientific_q = _dq(scientific)

    # Section YAML (kept as close to your Bodhi card as possible)
    section = f"""\
type: horizontal-stack
cards:
  - type: vertical-stack
    cards:
      # -------------- Section for {common} --------------
      - type: custom:mushroom-title-card
        title: "{common_q}"
        subtitle: "{scientific_q}"
        card_mod:
          attributes:
            title: "{common_q}"

      # Centered chip row (overall + per-signal)
      - type: custom:mushroom-chips-card
        alignment: center
        chips:
          - type: template
            entity: binary_sensor.{slug}_all_ok
            content: "{{{{ 'All Good' if is_state(entity, 'on') else 'Needs Attention' }}}}"
            icon: "{{{{ 'mdi:check-circle' if is_state(entity,'on') else 'mdi:alert-circle' }}}}"
            icon_color: "{{{{ 'green' if is_state(entity,'on') else 'red' }}}}"
          - type: template
            entity: binary_sensor.{slug}_light_ok
            content: "Light Level: {{{{ 'OK' if is_state(entity, 'on') else 'Problem' }}}}"
            icon: "{{{{ 'mdi:check-circle' if is_state(entity,'on') else 'mdi:alert-circle' }}}}"
            icon_color: "{{{{ 'green' if is_state(entity,'on') else 'red' }}}}"
          - type: template
            entity: binary_sensor.{slug}_temperature_ok
            content: "Temperature: {{{{ 'OK' if is_state(entity, 'on') else 'Problem' }}}}"
            icon: "{{{{ 'mdi:check-circle' if is_state(entity,'on') else 'mdi:alert-circle' }}}}"
            icon_color: "{{{{ 'green' if is_state(entity,'on') else 'red' }}}}"
          - type: template
            entity: binary_sensor.{slug}_moisture_ok
            content: "Moisture: {{{{ 'OK' if is_state(entity, 'on') else 'Problem' }}}}"
            icon: "{{{{ 'mdi:check-circle' if is_state(entity,'on') else 'mdi:alert-circle' }}}}"
            icon_color: "{{{{ 'green' if is_state(entity,'on') else 'red' }}}}"
          - type: template
            entity: binary_sensor.{slug}_ec_ok
            content: "Conductivity: {{{{ 'OK' if is_state(entity, 'on') else 'Problem' }}}}"
            icon: "{{{{ 'mdi:check-circle' if is_state(entity,'on') else 'mdi:alert-circle' }}}}"
            icon_color: "{{{{ 'green' if is_state(entity,'on') else 'red' }}}}"

      # 2-column metric grid (Temperature, Light, Moisture, Conductivity)
      - square: false
        type: grid
        columns: 2
        cards:
          - type: custom:mushroom-template-card
            entity: sensor.{slug}_temperature_routed
            primary: Temperature
            secondary: "{{{{ state_attr('sensor.ui_{slug}_temperature_routed','content') }}}}"
            icon: mdi:thermometer
            color: "{{{{ state_attr('sensor.ui_{slug}_temperature_routed','color') }}}}"
            multiline_secondary: true

          - type: custom:mushroom-template-card
            entity: sensor.{slug}_illuminance_routed
            primary: Light
            secondary: "{{{{ state_attr('sensor.ui_{slug}_illuminance_routed','content') }}}}"
            icon: mdi:white-balance-sunny
            color: "{{{{ state_attr('sensor.ui_{slug}_illuminance_routed','color') }}}}"
            multiline_secondary: true

          - type: custom:mushroom-template-card
            entity: sensor.{slug}_moisture_routed
            primary: Moisture
            secondary: "{{{{ state_attr('sensor.ui_{slug}_moisture_routed','content') }}}}"
            icon: mdi:water-percent
            color: "{{{{ state_attr('sensor.ui_{slug}_moisture_routed','color') }}}}"
            multiline_secondary: true

          - type: custom:mushroom-template-card
            entity: sensor.{slug}_conductivity_routed
            primary: Conductivity
            secondary: "{{{{ state_attr('sensor.ui_{slug}_conductivity_routed','content') }}}}"
            icon: mdi:flash
            color: "{{{{ state_attr('sensor.ui_{slug}_conductivity_routed','color') }}}}"
            multiline_secondary: true

      # Care summary (markdown-like), matching your Bodhi pattern
      - type: markdown
        content: |
          {{% set ok = {{
            'temp': is_state('binary_sensor.{slug}_temperature_ok','on'),
            'light': is_state('binary_sensor.{slug}_light_ok','on'),
            'moist': is_state('binary_sensor.{slug}_moisture_ok','on'),
            'cond': is_state('binary_sensor.{slug}_ec_ok','on')
          }} %}}
          {{% set overall_ok = (ok.temp and ok.light and ok.moist and ok.cond) %}}
          **{{{{ '✅ All Good!' if overall_ok else '⚠️ Needs Attention' }}}}:** {{{{ states('sensor.{slug}_care_notes') }}}}

          ---
          **🌤 Sunlight:** {{{{ state_attr('sensor.{slug}_care_notes','sunlight') or states('sensor.{slug}_care_notes') }}}}
          **🚿 Watering:** {{{{ state_attr('sensor.{slug}_care_notes','watering') or '—' }}}}
          **🌱 Fertilization:** {{{{ state_attr('sensor.{slug}_care_notes','fertilization') or '—' }}}}
          **✂️ Pruning:** {{{{ state_attr('sensor.{slug}_care_notes','pruning') or '—' }}}}
          **🪴 Soil:** {{{{ state_attr('sensor.{slug}_care_notes','soil') or '—' }}}}
          **📝 Notes:** {{{{ state_attr('sensor.{slug}_care_notes','floral_language') or '—' }}}}

  # Photo (exactly like your Bodhi example uses local/ with spaces)
  - type: picture
    image: "{image_path}"
"""
    return section


def build_router_package(rows: List[Dict[str, Any]], mif_temp: str, mif_lux: str, mif_moist: str, mif_ec: str) -> str:
    """
    Build a central router package that:
      - Defines input_select.plant_sensor_location with scientific names for provided rows
      - Mirrors raw MiFlora sensors (optional, convenient)
      - Creates 4 '..._routed' sensors per plant that output values only when selected
      - Converts °F -> °C for temperature to match CSV thresholds
    """
    # Scientific names list (as-is, keep spaces/case from pid)
    names = [r["pid"] for r in rows if r.get("pid")]
    # Sorted, lower-case for consistent selector values (use original case if you prefer)
    options_yaml = "\n".join([f"      - {n.lower()}" for n in sorted(names, key=lambda x: x.lower())])

    def routed_block(row: Dict[str, Any]) -> str:
        pid = row["pid"]
        slug = slugify(pid)
        sel = pid.lower()
        return f"""
      - name: "{pid} Temperature Routed"
        unique_id: {slug}_temperature_routed
        state: "{{{{ states('{mif_temp}') }}}}"
        availability: "{{{{ is_state('input_select.plant_sensor_location','{sel}') and has_value('{mif_temp}') }}}}"
        unit_of_measurement: "°F"
      - name: "{pid} Illuminance Routed"
        unique_id: {slug}_illuminance_routed
        state: "{{{{ states('{mif_lux}') }}}}"
        availability: "{{{{ is_state('input_select.plant_sensor_location','{sel}') and has_value('{mif_lux}') }}}}"
        unit_of_measurement: "lx"
      - name: "{pid} Moisture Routed"
        unique_id: {slug}_moisture_routed
        state: "{{{{ states('{mif_moist}') }}}}"
        availability: "{{{{ is_state('input_select.plant_sensor_location','{sel}') and has_value('{mif_moist}') }}}}"
        unit_of_measurement: "%"
      - name: "{pid} Conductivity Routed"
        unique_id: {slug}_conductivity_routed
        state: "{{{{ states('{mif_ec}') }}}}"
        availability: "{{{{ is_state('input_select.plant_sensor_location','{sel}') and has_value('{mif_ec}') }}}}"
        unit_of_measurement: "µS/cm"
"""

    routed_all = "\n".join(routed_block(r) for r in rows)

    pkg = f"""\
###############################################################################
# MiFlora plant probe routing (generated)
###############################################################################

input_select:
  plant_sensor_location:
    name: MiFlora probe is in
    icon: mdi:leaf-maple
    options:
{options_yaml}

template:
  - sensor:
      # Optional mirrors of raw MiFlora sensors (keep, edit, or remove)
      - name: "MiFlora Temperature F"
        unique_id: miflora_temperature_f
        availability: "{{{{ has_value('{mif_temp}') }}}}"
        state: "{{{{ states('{mif_temp}') }}}}"
        unit_of_measurement: "°F"
      - name: "MiFlora Illuminance"
        unique_id: miflora_illuminance
        availability: "{{{{ has_value('{mif_lux}') }}}}"
        state: "{{{{ states('{mif_lux}') }}}}"
        unit_of_measurement: "lx"
      - name: "MiFlora Moisture"
        unique_id: miflora_moisture
        availability: "{{{{ has_value('{mif_moist}') }}}}"
        state: "{{{{ states('{mif_moist}') }}}}"
        unit_of_measurement: "%"
      - name: "MiFlora Conductivity"
        unique_id: miflora_conductivity
        availability: "{{{{ has_value('{mif_ec}') }}}}"
        state: "{{{{ states('{mif_ec}') }}}}"
        unit_of_measurement: "µS/cm"

  - sensor:
{routed_all}
"""
    return pkg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to plant database CSV")
    ap.add_argument("--names", nargs="+", required=True, help="One or more scientific names (pid)")
    ap.add_argument("--out-packages", default="./packages", help="Output folder for package YAMLs")
    ap.add_argument("--out-sections", default="./sections", help="Output folder for dashboard section YAMLs")
    ap.add_argument("--sensor-map", default=None, help="Optional JSON mapping of slug -> sensor entities")
    # MiFlora sensor entity ids (defaults from your post)
    ap.add_argument(
        "--miflora-temperature",
        default="sensor.plant_sensor_d455_temperature",
        help="Entity id of the MiFlora temperature (°F)",
    )
    ap.add_argument(
        "--miflora-illuminance",
        default="sensor.plant_sensor_d455_illuminance",
        help="Entity id of the MiFlora illuminance (lx)",
    )
    ap.add_argument(
        "--miflora-moisture", default="sensor.plant_sensor_d455_moisture", help="Entity id of the MiFlora moisture (%%)"
    )
    ap.add_argument(
        "--miflora-conductivity",
        default="sensor.plant_sensor_d455_conductivity",
        help="Entity id of the MiFlora conductivity (µS/cm)",
    )
    # Where to write the central router package
    ap.add_argument(
        "--router-file",
        default="./packages/plant_sensor_router.yaml",
        help="Output path for the generated MiFlora router package",
    )
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

    # 1) Write per-plant packages & sections
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

    # 2) Write central MiFlora router package
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
