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
from homeassistant.helpers import area_registry, device_registry, entity_registry, floor_registry

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
    # Broader pages; each page contains multiple device-type sections.
    "10_power": {
        "title": "Lighting, Fans, Outlets",
        "groups": [
            {"title": "Lighting", "domains": ["light"]},
            {"title": "Airflow", "domains": ["fan"]},
            {"title": "Outlets", "domains": ["switch"], "outlets_only": True},
        ],
    },
    "20_switch_status": {
        "title": "Switches & Status",
        "groups": [
            {"title": "Switches", "domains": ["switch"], "exclude_outlets": True},
            {"title": "Binary Sensors", "domains": ["binary_sensor"]},
        ],
    },
    "30_comfort": {
        "title": "Comfort Sensors",
        "groups": [
            {"title": "Temperature", "domains": ["sensor"], "device_classes": ["temperature"], "app": "ambient"},
            {"title": "Humidity", "domains": ["sensor"], "device_classes": ["humidity"], "app": "indoor"},
        ],
    },
    "40_climate": {
        "title": "Climate",
        "groups": [
            {"title": "Thermostats", "domains": ["climate"]},
            {"title": "Humidifiers", "domains": ["humidifier"]},
        ],
    },
    "50_access_media": {
        "title": "Covers, Locks, Media, Cameras",
        "groups": [
            {"title": "Covers", "domains": ["cover"]},
            {"title": "Locks", "domains": ["lock"]},
            {"title": "Media Players", "domains": ["media_player"]},
            {"title": "Cameras", "domains": ["camera"]},
        ],
    },
    "60_automation": {
        "title": "Automations & Scripts",
        "groups": [
            {"title": "Automations", "domains": ["automation"]},
            {"title": "Scripts", "domains": ["script"]},
        ],
    },
    "70_utilities": {
        "title": "Utility Meters",
        "charts": [
            {
                "title": "Electric Daily",
                "domains": ["sensor"],
                "device_classes": ["energy"],
                "utility_meter_only": True,
                "card": {
                    "type": "statistics-graph",
                    "chart_type": "line",
                    "period": "day",
                    "days_to_show": 14,
                    "stat_types": ["state"],
                    "hide_legend": True,
                },
            },
            {
                "title": "Electric Monthly",
                "domains": ["sensor"],
                "device_classes": ["energy"],
                "utility_meter_only": True,
                "card": {
                    "type": "statistics-graph",
                    "chart_type": "line",
                    "period": "month",
                    "days_to_show": 365,
                    "stat_types": ["state"],
                    "hide_legend": True,
                },
            },
            {
                "title": "Gas Daily",
                "domains": ["sensor"],
                "device_classes": ["gas"],
                "utility_meter_only": True,
                "card": {
                    "type": "statistics-graph",
                    "chart_type": "line",
                    "period": "day",
                    "days_to_show": 30,
                    "stat_types": ["state"],
                    "hide_legend": True,
                },
            },
        ],
        "groups": [
            {
                "title": "Electric Meters",
                "domains": ["sensor"],
                "device_classes": ["energy"],
                "utility_meter_only": True,
                "app": "ambient",
            },
            {
                "title": "Gas Meters",
                "domains": ["sensor"],
                "device_classes": ["gas"],
                "utility_meter_only": True,
                "app": "ambient",
            },
        ],
    },
}

APP_TABLES: Dict[str, Dict[str, str]] = {
    "gas": {"daily_total": "daily_appliance", "daily": "daily"},
    # add more special cases here
}
APP_DEFAULT: Dict[str, str] = {"daily_total": "energy_daily_house", "daily": "energy_daily_area"}

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


def _device_class(eid: str) -> str:
    st = hass.states.get(eid)
    return (st and st.attributes.get("device_class")) or ""


def _is_utility_meter_sensor(eid: str) -> bool:
    """Heuristic: utility_meter sensors commonly expose last_period and/or meter_period attributes."""
    if _dom(eid) != "sensor":
        return False
    st = hass.states.get(eid)
    if not st:
        return False
    attrs = st.attributes or {}
    return ("last_period" in attrs) or ("meter_period" in attrs)


def _is_outlet_switch(eid: str) -> bool:
    # Prefer device_class when present, fall back to name heuristics.
    if _dom(eid) != "switch":
        return False
    dc = _device_class(eid)
    if dc == "outlet":
        return True
    n = _fname(eid).lower()
    return ("outlet" in n) or ("plug" in n)


def _sorted(eids: List[str]) -> List[str]:
    pairs = [(_fname(e).lower(), e) for e in eids]
    pairs.sort(key=lambda p: p[0])
    return [e for _, e in pairs]


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    return [i for i in items if not (i in seen or seen.add(i))]


def _grid(cards: List[dict], cols: int = 2) -> dict:
    return {"type": "grid", "columns": cols, "square": False, "cards": cards}


def _title(subtitle: str, title: str = "") -> dict:
    if title and not subtitle:
        return {"type": "heading", "heading": title, "heading_style": "title"}
    if not title and subtitle:
        return {"type": "heading", "heading": subtitle, "heading_style": "subtitle"}
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


async def _floor_lookup() -> Dict[str, str]:
    """Return {floor_id: floor_name}. Handles either id or floor_id attributes."""
    fr = await floor_registry.async_get(hass)
    lookup: Dict[str, str] = {}
    for f in fr.async_list_floors():
        fid = getattr(f, "floor_id", None) or getattr(f, "id", None)
        if not fid:
            continue
        lookup[fid] = getattr(f, "name", fid) or fid
    return lookup


async def _areas_grouped_by_floor(area_ids: List[str]) -> List[Dict]:
    """Group areas by floor while preserving the order provided by area_ids."""
    ar = await area_registry.async_get(hass)
    floor_names = await _floor_lookup()

    ordering: List[str] = []
    grouped: Dict[str, Dict] = {}

    for aid in area_ids:
        area = await _find_area_by_name(ar, aid)
        floor_id = getattr(area, "floor_id", None) if area else None
        key = floor_id or "__unassigned__"

        if key not in grouped:
            ordering.append(key)
            grouped[key] = {
                "floor_id": floor_id,
                "floor_name": floor_names.get(floor_id) if floor_id else "Other Areas",
                "areas": [],
            }

        grouped[key]["areas"].append(aid)

    return [grouped[k] for k in ordering]


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
            _title("Climate Trends"),
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
            _title("Utility Trends"),
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


def _card_for_entity_system(eid: str, app_override: str = None) -> dict:
    dom = _dom(eid)

    if dom == "light":
        return {
            "type": "custom:mushroom-light-card",
            "entity": eid,
            "tap_action": {"action": "more-info"},
        }

    if dom == "switch":
        return {"type": "custom:mushroom-entity-card", "entity": eid, "tap_action": {"action": "more-info"}}

    if dom == "fan":
        return {
            "type": "custom:mushroom-fan-card",
            "entity": eid,
            "tap_action": {"action": "more-info"},
        }

    if dom == "cover":
        return {"type": "custom:mushroom-cover-card", "entity": eid, "tap_action": {"action": "more-info"}}

    if dom == "lock":
        return {
            "type": "custom:mushroom-lock-card",
            "entity": eid,
            "tap_action": {"action": "more-info"},
        }

    if dom == "media_player":
        return {"type": "custom:mushroom-media-player-card", "entity": eid, "tap_action": {"action": "more-info"}}

    if dom == "climate":
        return {
            "type": "custom:mushroom-climate-card",
            "entity": eid,
            "tap_action": {"action": "more-info"},
        }

    if dom == "humidifier":
        return {
            "type": "custom:mushroom-humidifier-card",
            "entity": eid,
            "tap_action": {"action": "more-info"},
        }

    if dom == "camera":
        # Keep it lightweight; swap to picture-entity if you want live thumbnails
        return {"type": "custom:mushroom-entity-card", "entity": eid, "tap_action": {"action": "more-info"}}

    # Sensors and binary_sensors, reuse your decluttering template_card so names/icons/colors stay consistent
    if dom in ["sensor", "binary_sensor"]:
        st = hass.states.get(eid)
        dc = (st and st.attributes.get("device_class")) or "default"
        mt = (st and st.attributes.get("meter")) or None
        vertical_opts = []

        if mt:
            app_override = APP_TABLES.get(dc, APP_DEFAULT)[mt]
            vertical_opts.append({"project_daily": "true"})

        return {
            "type": "custom:decluttering-card",
            "template": "template_card",
            "variables": [{"entity": eid}, {"app": app_override or dc}] + vertical_opts,
        }

    # Fallback
    return {"type": "custom:mushroom-entity-card", "entity": eid, "tap_action": {"action": "more-info"}}


def _statistics_graph_card(title: str, entities: List[str], card_opts: Dict) -> dict:
    # card_opts should contain the keys supported by statistics-graph, e.g. chart_type/period/days_to_show/stat_types
    c = dict(card_opts)
    c["title"] = title
    c["entities"] = entities
    return c


def _filter_entities(all_eids: List[str], rule: Dict) -> List[str]:
    domains = set(rule.get("domains", []))
    dclasses = set(rule.get("device_classes", [])) if rule.get("device_classes") else None

    out: List[str] = []
    for e in all_eids:
        if domains and _dom(e) not in domains:
            continue
        if dclasses is not None and _device_class(e) not in dclasses:
            continue
        if rule.get("outlets_only") and not _is_outlet_switch(e):
            continue
        if rule.get("exclude_outlets") and _is_outlet_switch(e):
            continue
        if rule.get("utility_meter_only") and not _is_utility_meter_sensor(e):
            continue
        out.append(e)
    return _sorted(out)


async def _cards_for_system_groups(sys_def: Dict) -> List[dict]:
    """Systems dashboard: sections per device type, with floor subsections."""
    areas = await _all_areas_in_order()
    floor_groups = await _areas_grouped_by_floor(areas)

    # Collect all entities across all areas for shared charts
    all_eids: List[str] = []
    for area_id in areas:
        all_eids.extend(await _entities_in_area(area_id))

    all_eids = _dedupe_preserve_order(all_eids)

    view_cards: List[dict] = []

    # Optional charts at top of the view (used for Utility Meters)
    for ch in sys_def.get("charts", []):
        ents = _filter_entities(all_eids, ch)
        if not ents:
            continue
        view_cards += [
            _statistics_graph_card(ch["title"], ents, ch["card"]),
        ]

    # Device-type groupings, organized with per-floor subsections
    for g in sys_def.get("groups", []):
        group_cards: List[dict] = []

        for fg in floor_groups:
            floor_eids: List[str] = []
            for area_id in fg["areas"]:
                floor_eids.extend(await _entities_in_area(area_id))
            floor_eids = _dedupe_preserve_order(floor_eids)

            filtered = _filter_entities(floor_eids, g)
            if not filtered:
                continue

            group_cards += [
                _title(fg["floor_name"]),
                _grid([_card_for_entity_system(e, app_override=g.get("app")) for e in _sorted(filtered)], cols=2),
            ]

        if group_cards:
            group_cards = [_title("", g["title"])] + group_cards
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
                "cards": group_cards,
            })

    return view_cards


# ----- view builder ---------------------------------------------------


async def _write_view_file(view_key: str, view_title: str, areas: List[str]) -> None:

    view_cards: List[dict] = []

    for area in areas:
        try:
            area_cards = await _cards_for_area(area)
        except Exception as e:
            logger.error(f"[area-views] building cards failed for '{area}': {e}")
            area_cards = [{"type": "markdown", "content": f"**Error building area '{area}':** `{e}`"}]

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

    area_count = len(areas)
    logger.info(f"[area-views] wrote {path} ({area_count} area blocks)")


async def _write_system_view_file(view_key: str, view_title: str, sys_def: Dict) -> None:
    try:
        view_cards = await _cards_for_system_groups(sys_def)
    except Exception as e:
        logger.error(f"[system-views] building cards failed for '{view_key}': {e}")
        view_cards = [{"type": "markdown", "content": f"**Error building view '{view_key}':** `{e}`"}]

    await task.executor(os.makedirs, SYSTEMS_OUT_DIR, 0o777, True)

    yaml_str = yaml.safe_dump({"title": view_title, "type": "masonry", "cards": view_cards}, sort_keys=False)
    path = f"{SYSTEMS_OUT_DIR}/{view_key}.yaml"
    await task.executor(Path(path).write_text, yaml_str, "utf-8")

    logger.info(f"[system-views] wrote {path} ({len(view_cards)} cards)")


async def _build_all_system_views() -> None:
    for key, sys_def in SYSTEM_DEFS.items():
        try:
            await _write_system_view_file(key, sys_def["title"], sys_def)
        except Exception as e:
            logger.error(f"[system-views] failed writing {key}: {e}")


@service
async def build_system_views(view: str = None):
    """Manual rebuild. Call with view='10_lighting' or empty to build all."""
    if view:
        sys_def = SYSTEM_DEFS.get(view)
        if not sys_def:
            logger.error(f"[system-views] unknown view '{view}'")
            return
        await _write_system_view_file(view, sys_def["title"], sys_def)
    else:
        await _build_all_system_views()


# ----- triggers & service --------------------------------------------


@time_trigger("startup")
async def build_all_on_change(**kwargs):
    for key, val in VIEW_DEFS.items():
        try:
            await _write_view_file(key, val["title"], val["areas"])
        except Exception as e:
            logger.error(f"[area-views] failed writing {key}: {e}")
    await _build_all_system_views()


@service
async def build_area_views(view: str = None):
    """Manual rebuild. Call with view='downstairs' or empty to build all."""
    if view:
        val = VIEW_DEFS.get(view)
        if not val:
            logger.error(f"[area-views] unknown view '{view}'")
            return
        await _write_view_file(view, val["title"], val["areas"])
    else:
        await build_all_on_change()
