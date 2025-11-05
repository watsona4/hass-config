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
from typing import List, Optional, Tuple

import requests
from fitparse import FitFile, StandardUnitsDataProcessor

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    ZoneInfo = None
    ZoneInfoNotFoundError = Exception


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: zwift_parse_fit.py <fit_url> <output_prefix>\n")
        sys.exit(1)

    fit_url = sys.argv[1]
    _output_prefix = sys.argv[2]  # retained for CLI compatibility; assets now written via _write_* helpers.

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
        _write_apex_payload(
            title=session_title,
            version=version,
            points=json_points,
            epoch_ms=epoch_ms,
            laps=laps,
        )
        _write_route_payload(
            title=session_title,
            version=version,
            latitudes=latitudes,
            longitudes=longitudes,
            powers=powers,
            speeds=speeds,
            laps=laps,
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


if __name__ == "__main__":
    main()
