# Pyscript: build_area_views.py
# Creates static YAML card lists per "view" from areas, using HA registries.
# Files written to: /config/dashboards/_generated/<view_key>.yaml
#
# Call manually:  pyscript.build_area_views()   or   pyscript.build_area_views(view="downstairs")
# Auto-rebuilds on startup and when registries change.

import builtins
import logging
import os
from pathlib import Path
from typing import Dict, List

import yaml
from homeassistant.helpers import area_registry, device_registry, entity_registry

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Customize log message format
)
logger = logging.getLogger(__name__)  # This gets the logger for your script

OUT_DIR = "/config/dashboards/spaces/views"
SYSTEMS_OUT_DIR = "/config/dashboards/systems/views"

VIEW_DEFS: Dict[str, Dict] = {
    "01_downstairs": {
        "title": "Downstairs",
        "areas": [
            "parlor",
            "living_room",
            "dining_room",
            "breakfast_room",
            "kitchen",
            "pantry",
            "laundry_room",
        ],
    },
    "02_upstairs": {
        "title": "Upstairs",
        "areas": [
            "front_hallway",
            "study",
            "guest_bedroom",
            "master_bedroom",
            "master_bathroom",
            "back_hallway",
            "eleanor_s_room",
            "michael_s_room",
            "kids_bathroom",
        ],
    },
    "03_exterior": {
        "title": "Exterior",
        "areas": [
            "exterior",
            "chicken_coop",
            "rv",
        ],
    },
    "04_garage": {
        "title": "Garage",
        "areas": [
            "garage",
            "shop",
        ],
    },
    "05_garage_rooms": {
        "title": "Garage Rooms",
        "areas": [
            "exercise_room",
            "playroom",
        ],
    },
    "06_attic_basement": {
        "title": "Attic & Basement",
        "areas": [
            "attic",
            "basement",
        ],
    },
}

SYSTEM_DEFS: Dict[str, Dict] = {
    "10_lighting": {
        "title": "Lighting",
        "domains": ["light"],
    },
    "11_switches": {
        "title": "Switches & Outlets",
        "domains": ["switch"],
    },
    "12_climate": {
        "title": "Climate",
        "domains": ["climate", "humidifier"],
    },
    "13_fans": {
        "title": "Fans",
        "domains": ["fan"],
    },
    "14_covers": {
        "title": "Shades & Covers",
        "domains": ["cover"],
    },
    "15_locks": {
        "title": "Locks",
        "domains": ["lock"],
    },
    "16_media": {
        "title": "Media Players",
        "domains": ["media_player"],
    },
    "17_cameras": {
        "title": "Cameras",
        "domains": ["camera"],
    },
    # Sensors split by “type” so you do not end up with one massive Sensors page
    "30_temp": {
        "title": "Temperature Sensors",
        "domains": ["sensor"],
        "device_classes": ["temperature"],
    },
    "31_humidity": {
        "title": "Humidity Sensors",
        "domains": ["sensor"],
        "device_classes": ["humidity"],
    },
    "32_power": {
        "title": "Power & Energy Sensors",
        "domains": ["sensor"],
        "device_classes": ["power", "energy", "gas", "volume_flow_rate"],
    },
    "40_binary": {
        "title": "Binary Sensors",
        "domains": ["binary_sensor"],
    },
}

# --------------------------------------------------------------------

# ----- helpers --------------------------------------------------------


async def _find_area_by_name(ar, area_name: str):
    areas = ar.async_list_areas()
    for a in areas:
        if a.id == area_name:
            return a
    return None


async def _entities_in_area(area_name: str) -> List[str]:
    """Collect entity_ids that belong to an area (by area_id on entity or via device.area_id)."""
    ar = await area_registry.async_get(hass)
    dr = await device_registry.async_get(hass)
    er = await entity_registry.async_get(hass)

    area = await _find_area_by_name(ar, area_name)
    if not area:
        return []

    device_ids = {d.id for d in dr.devices.values() if d.area_id == area.id}
    ents = []
    for ent in er.entities.values():
        if (ent.area_id == area.id or (ent.device_id and ent.device_id in device_ids)) and ent.disabled_by is None:
            ents.append(ent.entity_id)
    return ents


def _dom(eid: str) -> str:
    return eid.split(".", 1)[0]


def _fname(eid: str) -> str:
    st = hass.states.get(eid)
    return (st and st.attributes.get("friendly_name")) or eid


def _sorted(eids: List[str]) -> List[str]:
    pairs = [(_fname(e).lower(), e) for e in eids]
    pairs.sort(key=lambda p: p[0])
    return [e for _, e in pairs]


def _grid(cards: List[dict], cols: int = 2) -> dict:
    return {"type": "grid", "columns": cols, "square": False, "cards": cards}


def _title(subtitle: str, title: str = "") -> dict:
    return {"type": "custom:mushroom-title-card", "title": title, "subtitle": subtitle}


def _preferred_area_order() -> List[str]:
    """All areas in the order implied by VIEW_DEFS, plus any others appended alphabetically."""
    preferred: List[str] = []
    seen = set()

    for _, v in VIEW_DEFS.items():
        for a in v["areas"]:
            if a not in seen:
                preferred.append(a)
                seen.add(a)

    return preferred


async def _all_areas_in_order() -> List[str]:
    ar = await area_registry.async_get(hass)
    preferred = _preferred_area_order()
    preferred_set = set(preferred)

    # Add any areas not already in VIEW_DEFS, sorted by display name
    others = [a.id for a in ar.async_list_areas() if a.id not in preferred_set]
    others.sort(key=lambda aid: (_area_friendly_name(aid) or aid).lower())

    return preferred + others


def _area_friendly_name(area_id: str) -> str:
    # safe sync accessor by id via hass registries is not available here,
    # so we fall back to id for sorting; display name is handled in cards below.
    return area_id


# ----- area → cards ---------------------------------------------------


async def _cards_for_area(area_name: str) -> List[dict]:
    eids = await _entities_in_area(area_name)
    cards: List[dict] = []

    # Area header card
    cards.append({
        "type": "area",
        "area": area_name,
        "features": [{"type": "area-controls", "controls": ["light", "switch"]}],
        "alert_classes": ["motion", "moisture", "problem"],
        "sensor_classes": ["temperature", "humidity", "power"],
        "tap_action": {"action": "more-info"},
    })

    # Binary sensors → chips (quick status)
    bin_e = [e for e in eids if _dom(e) == "binary_sensor"]
    if bin_e:
        chips = []
        for e in _sorted(bin_e):
            dc = (hass.states.get(e).attributes.get("device_class") if hass.states.get(e) else "") or "default"
            chips.append({
                "type": "template",
                "entity": e,
                "content": (
                    f"{{% from 'main.jinja' import get_name, get_short_desc %}}{{{{ get_name(entity, app='{dc}') }}}}:"
                    f" {{{{ get_short_desc(entity, app='{dc}') }}}}"
                ),
                "icon": f"{{% from 'main.jinja' import get_icon %}}{{{{ get_icon(entity, app='{dc}') }}}}",
                "icon_color": f"{{% from 'main.jinja' import get_color %}}{{{{ get_color(entity, app='{dc}') }}}}",
                "tap_action": {"action": "more-info"},
            })
        cards.append({"type": "custom:mushroom-chips-card", "alignment": "center", "chips": chips})

    vertical_opts = [{"layout": "vertical"}, {"multiline_secondary": False}, {"options": "vert_delim= • "}]

    # Comfort & Climate
    temp = [
        e
        for e in eids
        if _dom(e) == "sensor"
        and (hass.states.get(e) and hass.states.get(e).attributes.get("device_class") == "temperature")
    ]
    hum = [
        e
        for e in eids
        if _dom(e) == "sensor"
        and (hass.states.get(e) and hass.states.get(e).attributes.get("device_class") == "humidity")
    ]
    climates = [e for e in eids if _dom(e) == "climate"]
    humidifiers = [e for e in eids if _dom(e) == "humidifier"]

    if temp or hum or climates or humidifiers:
        sec_cards = []
        for e in _sorted(temp):
            sec_cards.append({
                "type": "custom:decluttering-card",
                "template": "template_card",
                "variables": [{"entity": e}, {"app": "ambient"}] + vertical_opts,
            })
        for e in _sorted(hum):
            sec_cards.append({
                "type": "custom:decluttering-card",
                "template": "template_card",
                "variables": [{"entity": e}, {"app": "indoor"}] + vertical_opts,
            })
        for e in _sorted(climates):
            sec_cards.append({
                "type": "custom:mushroom-climate-card",
                "entity": e,
                "tap_action": {"action": "more-info"},
                "layout": "vertical",
            })
        for e in _sorted(humidifiers):
            sec_cards.append({
                "type": "custom:mushroom-humidifier-card",
                "entity": e,
                "tap_action": {"action": "more-info"},
                "layout": "vertical",
            })

        cards += [
            _title("Comfort & Climate"),
            _grid(sec_cards, cols=2),
        ]

    # Switches
    switches = [e for e in eids if _dom(e) == "switch"]
    if switches:
        cards += [
            _title("Switches & Outlets"),
            _grid(
                [
                    {
                        "type": "custom:mushroom-entity-card",
                        "entity": e,
                        "tap_action": {"action": "more-info"},
                    }
                    for e in _sorted(switches)
                ],
                cols=2,
            ),
        ]

    # Lights
    lights = [e for e in eids if _dom(e) == "light"]
    if lights:
        cards += [
            _title("Lighting"),
            _grid(
                [
                    {
                        "type": "custom:mushroom-light-card",
                        "entity": e,
                        "tap_action": {"action": "more-info"},
                        "layout": "vertical",
                    }
                    for e in _sorted(lights)
                ],
                cols=2,
            ),
        ]

    # Fans
    fans = [e for e in eids if _dom(e) == "fan"]
    if fans:
        cards += [
            _title("Airflow"),
            _grid(
                [
                    {
                        "type": "custom:mushroom-fan-card",
                        "entity": e,
                        "tap_action": {"action": "more-info"},
                        "layout": "vertical",
                    }
                    for e in _sorted(fans)
                ],
                cols=2,
            ),
        ]

    # Power & Energy
    gas_rate = [
        e
        for e in eids
        if _dom(e) == "sensor"
        and (hass.states.get(e) and hass.states.get(e).attributes.get("device_class") == "volume_flow_rate")
    ]
    power = [
        e
        for e in eids
        if _dom(e) == "sensor" and (hass.states.get(e) and hass.states.get(e).attributes.get("device_class") == "power")
    ]

    if gas_rate or power:
        sec_cards = []
        for e in _sorted(gas_rate):
            sec_cards.append({
                "type": "custom:decluttering-card",
                "template": "template_card",
                "variables": [{"entity": e}, {"app": "gas_rate"}, {"width": "narrow"}],
            })
        for e in _sorted(power):
            app = "mains" if hass.states.get(e).attributes.get("friendly_name").lower() == "mains power" else "default"
            sec_cards.append({
                "type": "custom:decluttering-card",
                "template": "template_card",
                "variables": [{"entity": e}, {"app": app}, {"width": "narrow"}],
            })

        cards += [
            _title("Power & Energy"),
            _grid(sec_cards, cols=2),
        ]

    # Utility Meters
    logger.debug(f"Entities being processed: {eids}")
    for e in eids:
        entity = hass.states.get(e)
        if entity:
            device_class = entity.attributes.get("device_class")
            meter = entity.attributes.get("meter")
            logger.debug(f"Entity: {e}, Device Class: {device_class}, Meter: {meter}")
    gas_daily = [
        e
        for e in eids
        if _dom(e) == "sensor"
        and (
            hass.states.get(e)
            and hass.states.get(e).attributes.get("device_class") == "gas"
            and hass.states.get(e).attributes.get("meter") in ["daily", "daily_total"]
        )
    ]
    energy_daily = [
        e
        for e in eids
        if _dom(e) == "sensor"
        and (
            hass.states.get(e)
            and hass.states.get(e).attributes.get("device_class") == "energy"
            and hass.states.get(e).attributes.get("meter") in ["daily", "daily_total"]
        )
    ]

    if gas_daily or energy_daily:
        sec_cards = []
        for e in _sorted(gas_daily):
            app = "daily" if hass.states.get(e).attributes.get("meter") == "daily" else "daily_appliance"
            sec_cards.append({
                "type": "custom:decluttering-card",
                "template": "template_card",
                "variables": [{"entity": e}, {"app": app}, {"project_daily": "true"}] + vertical_opts,
            })
        for e in _sorted(energy_daily):
            app = (
                "energy_daily_house"
                if hass.states.get(e).attributes.get("meter") == "daily_total"
                else "energy_daily_area"
            )
            sec_cards.append({
                "type": "custom:decluttering-card",
                "template": "template_card",
                "variables": [{"entity": e}, {"app": app}, {"project_daily": "true"}] + vertical_opts,
            })

        cards += [
            _title("Utility Meters"),
            _grid(sec_cards, cols=2),
        ]

    # Covers
    covers = [e for e in eids if _dom(e) == "cover"]
    if covers:
        cards += [
            _title("Shades & Covers"),
            {
                "type": "vertical-stack",
                "cards": [
                    {
                        "type": "custom:mushroom-cover-card",
                        "entity": e,
                        "tap_action": {"action": "more-info"},
                    }
                    for e in _sorted(covers)
                ],
            },
        ]

    # Locks
    locks = [e for e in eids if _dom(e) == "lock"]
    if locks:
        cards += [
            _title("Access & Locks"),
            _grid(
                [
                    {
                        "type": "custom:mushroom-lock-card",
                        "entity": e,
                        "tap_action": {"action": "more-info"},
                        "layout": "vertical",
                    }
                    for e in _sorted(locks)
                ],
                cols=2,
            ),
        ]

    # Media players
    media = [e for e in eids if _dom(e) == "media_player"]
    if media:
        cards += [
            _title("Audio & Video"),
            {
                "type": "vertical-stack",
                "cards": [
                    {
                        "type": "custom:mushroom-media-player-card",
                        "entity": e,
                        "tap_action": {"action": "more-info"},
                    }
                    for e in _sorted(media)
                ],
            },
        ]

    # Automations
    automations = [e for e in eids if _dom(e) == "automation"]
    if automations:
        cards += [
            _title("Automations & Scripts"),
            _grid(
                [
                    {
                        "type": "custom:mushroom-entity-card",
                        "entity": e,
                        "tap_action": {"action": "more-info"},
                    }
                    for e in _sorted(automations)
                ],
                cols=2,
            ),
        ]

    # Climate History
    if temp or hum:

        series = [
            {
                "entity": e,
                "yaxis_id": "temp",
                "transform": (
                    "return x*9/5 + 32;"
                    if hass.states.get(e).attributes.get("unit_of_measurement") == "°C"
                    else "return x;"
                ),
            }
            for e in temp
        ] + [{"entity": e, "yaxis_id": "hum"} for e in hum]

        cards += [
            _title("Climate Trends (24 hours)"),
            {
                "type": "custom:apexcharts-card",
                "graph_span": "24h",
                "apex_config": {
                    "yaxis": [
                        {
                            "id": "temp",
                            "opposite": False,
                            "forceNiceScale": True,
                            "title": {"text": "Temperature (°F)"},
                            "labels": {"formatter": "EVAL:function(val) { return Number(val).toFixed(1); }"},
                        },
                        {
                            "id": "hum",
                            "opposite": True,
                            "forceNiceScale": True,
                            "title": {"text": "Humidity (%)"},
                            "labels": {"formatter": "EVAL:function(val) { return Number(val).toFixed(0); }"},
                        },
                    ],
                    "tooltip": {
                        "shared": True,
                        "y": {"formatter": "EVAL:function(val) { return Number(val).toFixed(2); }"},
                    },
                },
                "series": series,
            },
        ]

    # Utility History
    if gas_daily or energy_daily:

        series = [
            {
                "entity": e,
                "yaxis_id": "energy",
                "transform": (
                    "return x/1000;"
                    if hass.states.get(e).attributes.get("unit_of_measurement") == "Wh"
                    else "return x;"
                ),
                "type": "column",
                "group_by": {
                    "duration": "1d",
                    "func": "max",
                },
            }
            for e in energy_daily
        ] + [
            {
                "entity": e,
                "yaxis_id": "gas",
                "transform": (
                    "return x*35.3147;"
                    if hass.states.get(e).attributes.get("unit_of_measurement") == "m³"
                    else (
                        "return x/100;"
                        if hass.states.get(e).attributes.get("unit_of_measurement") == "CCF"
                        else "return x;"
                    )
                ),
                "type": "column",
                "group_by": {
                    "duration": "1d",
                    "func": "max",
                },
            }
            for e in gas_daily
        ]

        cards += [
            _title("Utility Trends (7 days)"),
            {
                "type": "custom:apexcharts-card",
                "graph_span": "7d",
                "apex_config": {
                    "yaxis": [
                        {
                            "id": "energy",
                            "opposite": False,
                            "forceNiceScale": True,
                            "title": {"text": f"Energy (kWh)"},
                            "labels": {"formatter": "EVAL:function(val) { return Number(val).toFixed(1); }"},
                        },
                        {
                            "id": "gas",
                            "opposite": True,
                            "forceNiceScale": True,
                            "title": {"text": f"Gas (ft³)"},
                            "labels": {"formatter": "EVAL:function(val) { return Number(val).toFixed(1); }"},
                        },
                    ],
                    "tooltip": {
                        "shared": True,
                        "y": {"formatter": "EVAL:function(val) { return Number(val).toFixed(2); }"},
                    },
                },
                "series": series,
            },
        ]

    return cards

async def _area_display_name(area_id: str) -> str:
    ar = await area_registry.async_get(hass)
    a = await _find_area_by_name(ar, area_id)
    return (a and a.name) or area_id


def _card_for_entity_system(eid: str) -> dict:
    dom = _dom(eid)

    if dom == "light":
        return {"type": "custom:mushroom-light-card", "entity": eid, "layout": "vertical", "tap_action": {"action": "more-info"}}

    if dom == "switch":
        return {"type": "custom:mushroom-entity-card", "entity": eid, "tap_action": {"action": "more-info"}}

    if dom == "fan":
        return {"type": "custom:mushroom-fan-card", "entity": eid, "layout": "vertical", "tap_action": {"action": "more-info"}}

    if dom == "cover":
        return {"type": "custom:mushroom-cover-card", "entity": eid, "tap_action": {"action": "more-info"}}

    if dom == "lock":
        return {"type": "custom:mushroom-lock-card", "entity": eid, "layout": "vertical", "tap_action": {"action": "more-info"}}

    if dom == "media_player":
        return {"type": "custom:mushroom-media-player-card", "entity": eid, "tap_action": {"action": "more-info"}}

    if dom == "climate":
        return {"type": "custom:mushroom-climate-card", "entity": eid, "layout": "vertical", "tap_action": {"action": "more-info"}}

    if dom == "humidifier":
        return {"type": "custom:mushroom-humidifier-card", "entity": eid, "layout": "vertical", "tap_action": {"action": "more-info"}}

    if dom == "camera":
        # Keep it lightweight; swap to picture-entity if you want live thumbnails
        return {"type": "custom:mushroom-entity-card", "entity": eid, "tap_action": {"action": "more-info"}}

    # Sensors and binary_sensors, reuse your decluttering template_card so names/icons/colors stay consistent
    if dom in ["sensor", "binary_sensor"]:
        st = hass.states.get(eid)
        dc = (st and st.attributes.get("device_class")) or "default"
        vertical_opts = [{"layout": "vertical"}, {"multiline_secondary": False}, {"options": "vert_delim= • "}]

        return {
            "type": "custom:decluttering-card",
            "template": "template_card",
            "variables": [{"entity": eid}, {"app": dc}] + vertical_opts,
        }

    # Fallback
    return {"type": "custom:mushroom-entity-card", "entity": eid, "tap_action": {"action": "more-info"}}


async def _cards_for_area_system(area_id: str, sys_def: Dict) -> List[dict]:
    eids = await _entities_in_area(area_id)

    domains = set(sys_def.get("domains", []))
    device_classes = set(sys_def.get("device_classes", [])) if sys_def.get("device_classes") else None

    filtered: List[str] = []
    for e in eids:
        if _dom(e) not in domains:
            continue
        if device_classes is not None:
            st = hass.states.get(e)
            dc = (st and st.attributes.get("device_class")) or None
            if dc not in device_classes:
                continue
        filtered.append(e)

    if not filtered:
        return []

    area_name = await _area_display_name(area_id)

    cards: List[dict] = []
    cards.append({"type": "custom:mushroom-title-card", "title": area_name})

    # Grid feels best for most “device type” pages
    cards.append(_grid([_card_for_entity_system(e) for e in _sorted(filtered)], cols=2))

    return cards

# ----- view builder ---------------------------------------------------


async def _write_view_file(view_key: str, view_title: str, areas: List[str]) -> None:

    view_cards: List[dict] = []

    for area in areas:
        try:
            area_cards = await _cards_for_area(area)
        except Exception as e:
            log.error(f"[area-views] building cards failed for '{area}': {e}")
            area_cards = [{"type": "markdown", "content": f"**Error building area '{area}':** `{e}`"}]

        # if you use a mod wrapper:
        view_cards.append({
            "type": "custom:stack-in-card",
            "mode": "vertical",
            "keep": {
                "background": True,
                "box_shadow": True,
                "border_radius": True,
            },
            "card_mod": {
                "style": (
                    "ha-card { border-radius: 12px; background: var(--card-background-color);"
                    " box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,.2)); padding:"
                    " 8px; }"
                ),
            },
            "cards": area_cards,
        })

    # 1) Ensure directory (stdlib function; pass exist_ok=True positionally)
    await task.executor(os.makedirs, OUT_DIR, 0o777, True)  # name, mode, exist_ok

    # 2) Serialize YAML in-memory (cheap CPU, fine on event loop)
    yaml_str = yaml.safe_dump({"title": view_title, "type": "masonry", "cards": view_cards}, sort_keys=False)

    # 3) Write using a stdlib bound method as the callable
    path = f"{OUT_DIR}/{view_key}.yaml"
    await task.executor(Path(path).write_text, yaml_str, "utf-8")

    log.info(f"[area-views] wrote {path} ({len(view_cards)} area blocks)")

async def _write_system_view_file(view_key: str, view_title: str, sys_def: Dict) -> None:
    view_cards: List[dict] = []

    areas = await _all_areas_in_order()

    for area_id in areas:
        try:
            area_cards = await _cards_for_area_system(area_id, sys_def)
        except Exception as e:
            log.error(f"[system-views] building cards failed for '{area_id}': {e}")
            area_cards = [{"type": "markdown", "content": f"**Error building area '{area_id}':** `{e}`"}]

        if not area_cards:
            continue  # skip empty areas to keep the page tight

        view_cards.append({
            "type": "custom:stack-in-card",
            "mode": "vertical",
            "keep": {"background": True, "box_shadow": True, "border_radius": True},
            "card_mod": {
                "style": (
                    "ha-card { border-radius: 12px; background: var(--card-background-color);"
                    " box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,.2)); padding: 8px; }"
                ),
            },
            "cards": area_cards,
        })

    await task.executor(os.makedirs, SYSTEMS_OUT_DIR, 0o777, True)

    yaml_str = yaml.safe_dump({"title": view_title, "type": "masonry", "cards": view_cards}, sort_keys=False)
    path = f"{SYSTEMS_OUT_DIR}/{view_key}.yaml"
    await task.executor(Path(path).write_text, yaml_str, "utf-8")

    log.info(f"[system-views] wrote {path} ({len(view_cards)} area blocks)")


async def _build_all_system_views() -> None:
    for key, sys_def in SYSTEM_DEFS.items():
        try:
            await _write_system_view_file(key, sys_def["title"], sys_def)
        except Exception as e:
            log.error(f"[system-views] failed writing {key}: {e}")


@service
async def build_system_views(view: str = None):
    """Manual rebuild. Call with view='10_lighting' or empty to build all."""
    if view:
        sys_def = SYSTEM_DEFS.get(view)
        if not sys_def:
            log.error(f"[system-views] unknown view '{view}'")
            return
        await _write_system_view_file(view, sys_def["title"], sys_def)
    else:
        await _build_all_system_views()

# ----- triggers & service --------------------------------------------


@time_trigger("startup")
@event_trigger("area_registry_updated")
@event_trigger("device_registry_updated")
@event_trigger("entity_registry_updated")
async def build_all_on_change(**kwargs):
    for key, val in VIEW_DEFS.items():
        try:
            await _write_view_file(key, val["title"], val["areas"])
        except Exception as e:
            log.error(f"[area-views] failed writing {key}: {e}")
    await _build_all_system_views()


@service
async def build_area_views(view: str = None):
    """Manual rebuild. Call with view='downstairs' or empty to build all."""
    if view:
        val = VIEW_DEFS.get(view)
        if not val:
            log.error(f"[area-views] unknown view '{view}'")
            return
        await _write_view_file(view, val["title"], val["areas"])
    else:
        await build_all_on_change()
