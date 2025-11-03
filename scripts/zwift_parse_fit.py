#!/usr/bin/env python3
# zwift_parse_fit.py
# Download a FIT from Zwift S3, parse "record" messages, and render plots

import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import requests
from fitparse import FitFile, StandardUnitsDataProcessor
from matplotlib.ticker import FuncFormatter

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    ZoneInfo = None
    ZoneInfoNotFoundError = Exception

try:
    import geopandas as gpd
except ImportError:
    gpd = None

try:
    from shapely.geometry import LineString
except ImportError:
    LineString = None

try:
    import contextily as ctx
except ImportError:
    ctx = None

matplotlib.use("Agg")

EARTH_RADIUS = 6378137.0


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: zwift_parse_fit.py <fit_url> <output_prefix>\n")
        sys.exit(1)

    fit_url = sys.argv[1]
    output_arg = sys.argv[2]
    output_base = Path(output_arg)

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

        metrics_path, map_path = _resolve_output_paths(output_base, output_arg)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.parent.mkdir(parents=True, exist_ok=True)

        _plot_metrics(timestamps, powers, cadences, heartrates, metrics_path)
        _plot_route(latitudes, longitudes, map_path)
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


def _resolve_output_paths(base: Path, raw_arg: str) -> Tuple[Path, Path]:
    is_dir_hint = raw_arg.endswith(("/", "\\"))

    if base.exists() and base.is_dir():
        target_dir = base
        stem = base.name or "zwift_fit"
    elif is_dir_hint:
        target_dir = base
        stem = base.name or "zwift_fit"
    elif base.suffix:
        target_dir = base.parent if base.parent != Path("") else Path(".")
        stem = base.stem
    else:
        target_dir = base.parent if base.parent != Path("") else Path(".")
        stem = base.name or "zwift_fit"

    metrics = target_dir / f"{stem}_metrics.png"
    route = target_dir / f"{stem}_map.png"
    return metrics, route


def _plot_metrics(
    timestamps: List[datetime],
    powers: List[float],
    cadences: List[float],
    heartrates: List[float],
    output_path: Path,
) -> None:
    formatter = mdates.DateFormatter("%H:%M:%S")

    fig, host = plt.subplots(figsize=(12, 6))
    fig.suptitle("Zwift Ride Metrics")

    color_power = "tab:red"
    color_cadence = "tab:green"
    color_hr = "tab:purple"

    host.plot(timestamps, powers, color=color_power, linewidth=1.2)
    host.set_ylabel("Power (W)", color=color_power)
    host.tick_params(axis="y", colors=color_power)
    host.xaxis.set_major_formatter(formatter)

    ax_cadence = host.twinx()
    # ax_cadence.spines["right"].set_position(("axes", 1.08))
    # _make_spine_visible(ax_cadence)
    ax_cadence.plot(timestamps, cadences, color=color_cadence, linewidth=1.0)
    ax_cadence.set_ylabel("Cadence (rpm)", color=color_cadence)
    ax_cadence.tick_params(axis="y", colors=color_cadence)

    ax_hr = host.twinx()
    ax_hr.spines["right"].set_position(("axes", 1.08))
    # _make_spine_visible(ax_hr)
    ax_hr.plot(timestamps, heartrates, color=color_hr, linewidth=1.0)
    ax_hr.set_ylabel("Heart Rate (bpm)", color=color_hr)
    ax_hr.tick_params(axis="y", colors=color_hr)

    host.set_xlabel("Time")
    host.grid(True, linewidth=0.3, linestyle="--", alpha=0.6)

    fig.autofmt_xdate()
    fig.tight_layout(
        rect=(0, 0, 1, 0.96),
    )
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _plot_route(latitudes: List[float], longitudes: List[float], output_path: Path) -> None:
    # Filter out missing coordinates and keep ordering for line plot.
    route = [(lat, lng) for lat, lng in zip(latitudes, longitudes) if not (math.isnan(lat) or math.isnan(lng))]

    if not route:
        raise ValueError("FIT data does not contain location points to plot the route.")

    if gpd is None or LineString is None:
        raise RuntimeError("geopandas and shapely are required for rendering the route map.")

    lats, lngs = zip(*route)
    route_line = LineString(zip(lngs, lats))
    route_gdf = gpd.GeoDataFrame({"geometry": [route_line]}, crs="EPSG:4326")

    if ctx is not None:
        try:
            _plot_route_with_basemap(route_gdf, output_path)
            return
        except Exception as err:
            sys.stderr.write(f"Warning: failed to render contextily basemap: {err}\n")

    world = _load_world_polygons()

    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lngs), max(lngs)
    lat_pad = max((lat_max - lat_min) * 0.1, 0.0005)
    lon_pad = max((lon_max - lon_min) * 0.1, 0.0005)
    lat_min -= lat_pad
    lat_max += lat_pad
    lon_min -= lon_pad
    lon_max += lon_pad

    try:
        world_subset = world.cx[lon_min:lon_max, lat_min:lat_max]
    except Exception:
        world_subset = world

    if world_subset.empty:
        world_subset = world

    fig, ax = plt.subplots(figsize=(8, 8))
    world_subset.plot(ax=ax, color="whitesmoke", edgecolor="lightgray", linewidth=0.5)
    route_gdf.plot(ax=ax, color="tab:orange", linewidth=2.0)

    ax.set_title("Route")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, linewidth=0.3, linestyle="--", alpha=0.6)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _make_spine_visible(ax: plt.Axes) -> None:
    ax.set_frame_on(True)
    ax.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["right"].set_visible(True)


def _plot_route_with_basemap(route_gdf: "gpd.GeoDataFrame", output_path: Path) -> None:
    route_web = route_gdf.to_crs(epsg=3857)
    minx, miny, maxx, maxy = route_web.total_bounds
    pad_x = max((maxx - minx) * 0.15, 150.0)
    pad_y = max((maxy - miny) * 0.15, 150.0)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    ctx.add_basemap(ax, crs=route_web.crs, source=ctx.providers.OpenStreetMap.Mapnik)
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    route_web.plot(ax=ax, color="tab:orange", linewidth=2.0)

    ax.set_title("Route")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, linewidth=0.3, linestyle="--", alpha=0.6)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{_mercator_to_lon(x):.4f}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{_mercator_to_lat(y):.4f}"))

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _mercator_to_lon(x: float) -> float:
    return math.degrees(x / EARTH_RADIUS)


def _mercator_to_lat(y: float) -> float:
    return math.degrees(2 * math.atan(math.exp(y / EARTH_RADIUS)) - math.pi / 2)


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


def _load_world_polygons():
    if gpd is None:
        raise RuntimeError("geopandas is required for rendering the route map.")

    datasets = getattr(gpd, "datasets", None)
    if datasets is not None:
        try:
            path = datasets.get_path("naturalearth_lowres")
            return gpd.read_file(path).to_crs("EPSG:4326")
        except Exception:
            pass

    natural_earth_url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
    try:
        return gpd.read_file(natural_earth_url).to_crs("EPSG:4326")
    except Exception as exc:
        raise RuntimeError(
            "Failed to load Natural Earth background. Ensure network access is available or provide a local shapefile."
        ) from exc


if __name__ == "__main__":
    main()
