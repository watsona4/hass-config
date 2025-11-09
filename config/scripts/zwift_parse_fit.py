#!/usr/bin/env python3
# zwift_parse_fit.py
# Download a FIT from Zwift S3, parse "record" messages, and emit JSON payloads for dashboards.

import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import requests
from fitparse import FitFile, StandardUnitsDataProcessor

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    ZoneInfo = None
    ZoneInfoNotFoundError = Exception


ZWIFT_WORLDS = [
    {"id": 1, "slug": "watopia", "name": "Watopia", "bounds": ((-11.74087, 166.87747), (-11.62597, 167.03255))},
    {"id": 2, "slug": "richmond", "name": "Richmond", "bounds": ((37.5014, -77.48954), (37.5774, -77.394))},
    {"id": 3, "slug": "london", "name": "London", "bounds": ((51.4601, -0.1776), (51.5362, -0.0555))},
    {"id": 4, "slug": "new-york", "name": "New York", "bounds": ((40.74085, -74.0227), (40.81725, -73.9222))},
    {"id": 5, "slug": "innsbruck", "name": "Innsbruck", "bounds": ((47.2055, 11.3501), (47.2947, 11.4822))},
    {"id": 6, "slug": "bologna", "name": "Bologna", "bounds": ((44.45463821, 11.26261748), (44.5308037, 11.36991729102076))},
    {"id": 7, "slug": "yorkshire", "name": "Yorkshire", "bounds": ((53.9491, -1.632), (54.0254, -1.5022))},
    {"id": 8, "slug": "crit-city", "name": "Crit City", "bounds": ((-10.4038, 165.7824), (-10.3657, 165.8207))},
    {"id": 9, "slug": "makuri-islands", "name": "Makuri Islands", "bounds": ((-10.85234, 165.76591), (-10.73746, 165.88222))},
    {"id": 10, "slug": "france", "name": "France", "bounds": ((-21.7564, 166.1384), (-21.64155, 166.26125))},
    {"id": 11, "slug": "paris", "name": "Paris", "bounds": ((48.82945, 2.2561), (48.9058, 2.3722))},
    {"id": 13, "slug": "scotland", "name": "Scotland", "bounds": ((55.61845, -5.2802), (55.67595, -5.17798))},
]

WORLD_BY_ID = {world["id"]: world for world in ZWIFT_WORLDS if "id" in world}
WORLD_BY_SLUG = {world["slug"]: world for world in ZWIFT_WORLDS}
WORLD_BY_NAME = {world["name"].strip().lower(): world for world in ZWIFT_WORLDS}


def main():
    if len(sys.argv) not in (3, 4):
        sys.stderr.write("Usage: zwift_parse_fit.py <fit_url> <output_prefix> [world_hint]\n")
        sys.exit(1)

    fit_url = sys.argv[1]
    _output_prefix = sys.argv[2]  # retained for CLI compatibility; assets now written via _write_* helpers.
    world_hint = sys.argv[3] if len(sys.argv) == 4 else None

    try:
        resp = requests.get(fit_url, timeout=30)
        resp.raise_for_status()
        raw = resp.content
    except Exception as e:
        sys.stderr.write(f"Error downloading FIT: {e}\n")
        sys.exit(2)

    try:
        ff = FitFile(raw, data_processor=StandardUnitsDataProcessor())
        records = (m for m in ff.get_messages() if m.name == "record")
        timestamps: List[datetime] = []
        epoch_ms: List[int] = []
        latitudes: List[float] = []
        longitudes: List[float] = []
        powers: List[float] = []
        cadences: List[float] = []
        heartrates: List[float] = []
        speeds: List[float] = []
        json_points: List[List[Optional[float]]] = []

        local_tz = _get_local_timezone()

        for m in records:
            d = {f.name: f.value for f in m}
            timestamp = d.get("timestamp")
            lat = d.get("position_lat")
            lng = d.get("position_long")
            power = d.get("power")
            cadence = d.get("cadence")
            heartrate = d.get("heart_rate")

            # Skip records that lack a timestamp; without it we can't line up values.
            if not isinstance(timestamp, datetime):
                continue

            dt_local, ts_epoch_ms = _convert_timestamp(timestamp, local_tz)
            timestamps.append(dt_local)
            epoch_ms.append(ts_epoch_ms)
            latitudes.append(float(lat) if isinstance(lat, (int, float)) else math.nan)
            longitudes.append(float(lng) if isinstance(lng, (int, float)) else math.nan)
            powers.append(float(power) if isinstance(power, (int, float)) else math.nan)
            cadences.append(float(cadence) if isinstance(cadence, (int, float)) else math.nan)
            heartrates.append(float(heartrate) if isinstance(heartrate, (int, float)) else math.nan)
            power_value = _coerce_float(power)
            hr_value = _coerce_float(heartrate)
            cadence_value = _coerce_float(cadence)
            speed_value = _coerce_float(d.get("enhanced_speed"), d.get("speed"))
            speeds.append(speed_value if speed_value is not None else math.nan)
            elevation_value = _coerce_float(d.get("enhanced_altitude"), d.get("altitude"))
            json_points.append([
                ts_epoch_ms,
                power_value,
                hr_value,
                cadence_value,
                speed_value,
                elevation_value,
            ])

        if not timestamps:
            sys.stderr.write("No usable record data found in FIT file.\n")
            sys.exit(4)
        session_title = _session_title(ff) or "Zwift Ride"
        version = int(time.time())
        laps = _extract_laps(ff, local_tz, epoch_ms, latitudes, longitudes)
        world = _resolve_world(ff, latitudes, longitudes, world_hint)
        world_payload = _world_payload(world)
        _write_apex_payload(
            title=session_title,
            version=version,
            points=json_points,
            epoch_ms=epoch_ms,
            laps=laps,
            world=world_payload,
        )
        _write_route_payload(
            title=session_title,
            version=version,
            latitudes=latitudes,
            longitudes=longitudes,
            powers=powers,
            speeds=speeds,
            laps=laps,
            world=world_payload,
        )

        summary = _summarize_ride(heartrates)
        if summary is not None:
            print(json.dumps(summary))
    except Exception as e:
        sys.stderr.write(f"Error parsing FIT: {e}\n")
        sys.exit(3)


def _convert_timestamp(ts: datetime, local_tz) -> Tuple[datetime, int]:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if local_tz is None:
        localized = ts.astimezone()
    else:
        localized = ts.astimezone(local_tz)
    epoch_ms = int(localized.timestamp() * 1000)
    # Matplotlib prefers naive datetimes in local time for plotting.
    return localized.replace(tzinfo=None), epoch_ms


def _get_local_timezone():
    tz_name = os.environ.get("TZ")
    if tz_name and ZoneInfo is not None:
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            sys.stderr.write(f"Warning: TZ environment set to unknown zone '{tz_name}'; falling back to system tz.\n")
        except Exception:
            pass
    try:
        return datetime.now().astimezone().tzinfo
    except Exception:
        return timezone.utc


def _summarize_ride(heartrates: List[float]) -> Optional[dict]:
    valid = [hr for hr in heartrates if isinstance(hr, (int, float)) and not math.isnan(hr)]
    if not valid:
        return None

    avg = sum(valid) / len(valid)
    max_hr = max(valid)
    return {
        "avg_heartrate": round(avg, 1),
        "max_heartrate": round(max_hr, 1),
    }


def _coerce_float(*values) -> Optional[float]:
    for value in values:
        if isinstance(value, (int, float)):
            val = float(value)
            if math.isnan(val):
                continue
            return val
    return None


def _extract_laps(
    ff: FitFile,
    local_tz,
    epoch_ms: List[int],
    latitudes: List[float],
    longitudes: List[float],
) -> List[dict]:
    laps: List[dict] = []
    for idx, lap_msg in enumerate(ff.get_messages("lap")):
        fields = {f.name: f.value for f in lap_msg}
        start_time = fields.get("start_time") or fields.get("timestamp")
        if not isinstance(start_time, datetime):
            continue
        _, ts_ms = _convert_timestamp(start_time, local_tz)
        label = fields.get("name")
        if not isinstance(label, str) or not label.strip():
            label = f"Lap {idx + 1}"
        entry = {"label": label, "ts": ts_ms}
        if epoch_ms:
            nearest = min(range(len(epoch_ms)), key=lambda i: abs(epoch_ms[i] - ts_ms))
            lat = latitudes[nearest] if nearest < len(latitudes) else math.nan
            lon = longitudes[nearest] if nearest < len(longitudes) else math.nan
            if not math.isnan(lat) and not math.isnan(lon):
                entry["lat"] = round(float(lat), 6)
                entry["lon"] = round(float(lon), 6)
        laps.append(entry)
    return laps


def _session_title(ff: FitFile) -> Optional[str]:
    session = next((ff.get_messages("session")), None)
    if session is None:
        return None
    fields = {f.name: f.value for f in session}
    for key in ("name", "event", "sub_sport", "sport"):
        value = fields.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    sport = fields.get("sport")
    if sport:
        return str(sport).strip().title()
    return None


def _write_apex_payload(
    title: str,
    version: int,
    points: List[List[Optional[float]]],
    epoch_ms: List[int],
    laps: List[dict],
    world: Optional[dict],
) -> None:
    if not points:
        return

    ride_dir = Path("/config/www/ride")
    ride_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "title": title,
        "version": version,
        "start_ts": int(epoch_ms[0] / 1000) if epoch_ms else None,
        "points": points,
        "laps": laps,
    }
    if world:
        payload["world"] = world
    payload_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    (ride_dir / "latest.json").write_text(payload_text, encoding="utf-8")


def _write_route_payload(
    title: str,
    version: int,
    latitudes: List[float],
    longitudes: List[float],
    powers: List[float],
    speeds: List[float],
    laps: List[dict],
    world: Optional[dict],
) -> None:
    route_points: List[List[float]] = []
    power_series: List[Optional[float]] = []
    speed_series: List[Optional[float]] = []
    for lat, lon, power, speed in zip(latitudes, longitudes, powers, speeds):
        if math.isnan(lat) or math.isnan(lon):
            continue
        route_points.append([round(float(lat), 6), round(float(lon), 6)])
        power_series.append(None if math.isnan(power) else round(float(power), 2))
        speed_series.append(None if math.isnan(speed) else round(float(speed), 2))

    if not route_points:
        return

    payload: dict[str, object] = {
        "title": title,
        "version": version,
        "points": route_points,
        "start": route_points[0],
        "end": route_points[-1],
    }
    if world:
        payload["world"] = world
    if any(p is not None for p in power_series):
        payload["power_w"] = power_series
    if any(s is not None for s in speed_series):
        payload["speed_mps"] = speed_series
    if laps:
        payload["laps"] = laps

    ride_dir = Path("/config/www/ride")
    ride_dir.mkdir(parents=True, exist_ok=True)
    route_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    (ride_dir / "route.json").write_text(route_text, encoding="utf-8")


def _resolve_world(
    ff: FitFile,
    latitudes: List[float],
    longitudes: List[float],
    world_hint: Optional[str],
):
    world = _match_world_from_hint(world_hint)
    if world:
        return world
    world = _match_world_from_metadata(ff)
    if world:
        return world
    return _match_world_from_coordinates(latitudes, longitudes)


def _normalize_world_token(value: str) -> str:
    return value.strip().lower().replace("_", "-").replace(" ", "-")


def _match_world_from_hint(world_hint: Optional[str]):
    if world_hint is None:
        return None
    hint = str(world_hint).strip()
    if not hint or hint.lower() in {"none", "null"}:
        return None
    if hint.isdigit():
        return WORLD_BY_ID.get(int(hint))
    try:
        possible_id = int(float(hint))
        return WORLD_BY_ID.get(possible_id)
    except (ValueError, TypeError):
        pass
    normalized = _normalize_world_token(hint)
    return WORLD_BY_SLUG.get(normalized) or WORLD_BY_NAME.get(hint.strip().lower())


def _match_world_from_metadata(ff: FitFile):
    candidates: List[str] = []
    for message_name in ("session", "sport", "event"):
        for msg in ff.get_messages(message_name):
            for field in msg:
                value = getattr(field, "value", None)
                if isinstance(value, str):
                    candidates.append(value)
    return _match_world_from_strings(candidates)


def _match_world_from_strings(strings: Iterable[str]):
    for text in strings:
        normalized = _normalize_world_token(text)
        if not normalized:
            continue
        exact = WORLD_BY_SLUG.get(normalized) or WORLD_BY_NAME.get(text.strip().lower())
        if exact:
            return exact
        for slug, world in WORLD_BY_SLUG.items():
            options = {
                slug,
                slug.replace("-", " "),
                world["name"].strip().lower(),
                world["name"].strip().lower().replace(" ", "-"),
            }
            if any(token in normalized for token in options):
                return world
    return None


def _match_world_from_coordinates(latitudes: List[float], longitudes: List[float]):
    coords = [
        (lat, lon)
        for lat, lon in zip(latitudes, longitudes)
        if isinstance(lat, (int, float))
        and isinstance(lon, (int, float))
        and not math.isnan(lat)
        and not math.isnan(lon)
    ]
    if not coords:
        return None
    for world in ZWIFT_WORLDS:
        (lat_a, lon_a), (lat_b, lon_b) = world["bounds"]
        lat_min, lat_max = sorted((lat_a, lat_b))
        lon_min, lon_max = sorted((lon_a, lon_b))
        for lat, lon in coords:
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return world
    return None


def _world_payload(world: Optional[dict]):
    if not world:
        return None
    payload = {"slug": world.get("slug")}
    if "name" in world and world["name"]:
        payload["name"] = world["name"]
    if "id" in world:
        payload["id"] = world["id"]
    return payload


if __name__ == "__main__":
    main()
