#!/usr/bin/env python3
# zwift_parse_fit.py
# Download a FIT from Zwift S3, parse "record" messages, and render plots

import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

import matplotlib
import requests

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

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

from fitparse import FitFile, StandardUnitsDataProcessor

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
        latitudes: List[float] = []
        longitudes: List[float] = []
        powers: List[float] = []
        cadences: List[float] = []
        heartrates: List[float] = []

        local_tz = datetime.now().astimezone().tzinfo

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

            timestamps.append(_to_local_time(timestamp, local_tz))
            latitudes.append(float(lat) if isinstance(lat, (int, float)) else math.nan)
            longitudes.append(float(lng) if isinstance(lng, (int, float)) else math.nan)
            powers.append(float(power) if isinstance(power, (int, float)) else math.nan)
            cadences.append(float(cadence) if isinstance(cadence, (int, float)) else math.nan)
            heartrates.append(float(heartrate) if isinstance(heartrate, (int, float)) else math.nan)

        if not timestamps:
            sys.stderr.write("No usable record data found in FIT file.\n")
            sys.exit(4)

        metrics_path, map_path = _resolve_output_paths(output_base, output_arg)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.parent.mkdir(parents=True, exist_ok=True)

        _plot_metrics(timestamps, powers, cadences, heartrates, metrics_path)
        _plot_route(latitudes, longitudes, map_path)
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
    ax_cadence.spines["right"].set_position(("axes", 1.08))
    _make_spine_visible(ax_cadence)
    ax_cadence.plot(timestamps, cadences, color=color_cadence, linewidth=1.0)
    ax_cadence.set_ylabel("Cadence (rpm)", color=color_cadence)
    ax_cadence.tick_params(axis="y", colors=color_cadence)

    ax_hr = host.twinx()
    ax_hr.spines["right"].set_position(("axes", 1.16))
    _make_spine_visible(ax_hr)
    ax_hr.plot(timestamps, heartrates, color=color_hr, linewidth=1.0)
    ax_hr.set_ylabel("Heart Rate (bpm)", color=color_hr)
    ax_hr.tick_params(axis="y", colors=color_hr)

    host.set_xlabel("Time")
    host.grid(True, linewidth=0.3, linestyle="--", alpha=0.6)

    fig.autofmt_xdate()
    fig.tight_layout(rect=[0, 0, 1, 0.96])
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
    ax.patch.set_visible(False)
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


def _to_local_time(ts: datetime, local_tz) -> datetime:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if local_tz is None:
        return ts.astimezone()
    return ts.astimezone(local_tz)


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

    natural_earth_url = (
        "https://naturalearth.s3.amazonaws.com/110m_cultural/"
        "ne_110m_admin_0_countries.zip"
    )
    try:
        return gpd.read_file(natural_earth_url).to_crs("EPSG:4326")
    except Exception as exc:
        raise RuntimeError(
            "Failed to load Natural Earth background. Ensure network access is available "
            "or provide a local shapefile."
        ) from exc


if __name__ == "__main__":
    main()
