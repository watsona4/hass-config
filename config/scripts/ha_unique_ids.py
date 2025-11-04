#!/usr/bin/env python3
import argparse, uuid, sys, pathlib, re
from typing import Any, Set, List, Mapping

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString as DQ
from ruamel.yaml.scalarstring import ScalarString  # includes Literal/Folded scalars

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)

# list-style containers (lists of entity dicts)
LIST_CONTAINERS = {
    "sensor", "binary_sensor", "switch", "light", "number", "select", "button", "text",
    "alarm_control_panel", "device_tracker", "cover", "climate", "fan", "humidifier",
    "media_player", "water_heater", "lock", "valve", "update", "camera"
    # NOTE: do NOT include "template" here; it's a wrapper
}

# dict-style containers (mapping of key -> entity dict)
DICT_CONTAINERS = {
    "utility_meter",
}

# keys that make a dict "look like" an entity config
ENTITY_HINT_KEYS = {
    "name", "state", "platform", "unique_id", "device_class", "state_class", "unit_of_measurement",
    "value_template", "command_topic", "state_topic"
}

# Platforms that do not support unique_id
PLATFORMS_WITHOUT_UNIQUE_ID = {
    "derivative"  # You can add other platforms here that do not support unique_id
}

def is_uuid(val: Any) -> bool:
    return isinstance(val, str) and UUID_RE.match(val) is not None

def new_uuid(used: Set[str]) -> str:
    while True:
        u = str(uuid.uuid4())
        if u not in used:
            used.add(u)
            return u

def dq_if_needed(val: Any) -> Any:
    """Quote only string VALUES that contain a space or a colon. Leave block scalars as-is."""
    if isinstance(val, ScalarString):
        return val  # preserve literal/folded scalars (Jinja blocks etc.)
    if isinstance(val, str) and (" " in val or ":" in val):
        return DQ(val)
    return val

def is_entity_dict(d: Mapping) -> bool:
    """Heuristic: looks like an entity if it has typical entity keys."""
    if not isinstance(d, Mapping):
        return False
    # if dict only contains container keys, it's not an entity
    if all(isinstance(k, str) and (k in LIST_CONTAINERS or k in DICT_CONTAINERS) for k in d.keys()):
        return False
    return any(k in d for k in ENTITY_HINT_KEYS)

def collect_existing_uuids(node: Any, acc: Set[str]) -> None:
    if isinstance(node, Mapping):
        uid = node.get("unique_id")
        if is_uuid(uid):
            acc.add(uid)
        for v in node.values():
            collect_existing_uuids(v, acc)
    elif isinstance(node, (list, CommentedSeq)):
        for v in node:
            collect_existing_uuids(v, acc)

def order_unique_id(ent: CommentedMap, dict_container: bool = False) -> None:
    """
    Place unique_id in a nice spot:
      - For list-style entities: after 'name' if present, else after 'source'.
      - For dict-style container entries: make unique_id the very first key.
    """
    if not isinstance(ent, CommentedMap) or "unique_id" not in ent:
        return

    if dict_container:
        # Pull out and insert at index 0
        uid_val = ent.pop("unique_id")
        ent.insert(0, "unique_id", uid_val)
        return

    keys = list(ent.keys())

    def insert_after(anchor_key: str) -> bool:
        if anchor_key in ent:
            i = keys.index(anchor_key)
            uid_val = ent.pop("unique_id")
            ent.insert(i + 1, "unique_id", uid_val)
            return True
        return False

    # If already directly after name or source, skip
    for anchor in ("name", "source"):
        if anchor in ent:
            i = keys.index(anchor)
            if i + 1 < len(keys) and keys[i + 1] == "unique_id":
                return

    if not insert_after("name"):
        insert_after("source")

def ensure_unique_id_on_entity(ent: CommentedMap, used: Set[str], force: bool,
                               dict_container: bool = False) -> None:
    platform = ent.get("platform", "")
    
    # Skip entities for platforms that don't support unique_id
    if platform in PLATFORMS_WITHOUT_UNIQUE_ID:
        return

    if "unique_id" in ent:
        if force or not is_uuid(ent["unique_id"]):
            ent["unique_id"] = new_uuid(used)
        else:
            ent["unique_id"] = str(ent["unique_id"])
    elif "default_entity_id" not in ent:
        ent["unique_id"] = new_uuid(used)

    for k in list(ent.keys()):
        ent[k] = dq_if_needed(ent[k])

    order_unique_id(ent, dict_container=dict_container)

def process(node: Any, used: Set[str], force: bool, parent_stack: List[str]) -> Any:
    # Dicts
    if isinstance(node, Mapping):
        # Handle dict-style containers
        for k in list(node.keys()):
            v = node[k]
            if isinstance(k, str) and k in DICT_CONTAINERS and isinstance(v, Mapping):
                for ek in list(v.keys()):
                    ev = v[ek]
                    if isinstance(ev, Mapping):
                        ensure_unique_id_on_entity(ev, used, force, dict_container=True)
        # Recurse into all items
        for k, v in list(node.items()):
            parent_stack.append(k if isinstance(k, str) else str(k))
            node[k] = process(v, used, force, parent_stack)
            parent_stack.pop()
        return node

    # Lists
    if isinstance(node, (list, CommentedSeq)):
        add_here = False
        if parent_stack:
            pk = parent_stack[-1]
            if pk in LIST_CONTAINERS:
                add_here = True
        for idx, item in enumerate(list(node)):
            node[idx] = process(item, used, force, parent_stack)
            if add_here and isinstance(node[idx], Mapping) and is_entity_dict(node[idx]):
                ensure_unique_id_on_entity(node[idx], used, force)
        return node

    # Scalars
    if isinstance(node, ScalarString):
        return node
    if isinstance(node, str):
        return dq_if_needed(node)
    return node

def main():
    ap = argparse.ArgumentParser(
        description="Assign UUIDv4 unique_id to Home Assistant YAML, preserve formatting, "
                    "and keep existing UUIDs by default."
    )
    ap.add_argument("file", help="Path to YAML file")
    ap.add_argument("--force", action="store_true", help="Overwrite existing UUIDs with fresh v4 values")
    ap.add_argument("--dry-run", action="store_true", help="Print to stdout without writing")
    ap.add_argument("--backup", action="store_false", help="Write a .bak alongside the file")
    args = ap.parse_args()

    path = pathlib.Path(args.file)
    text = path.read_text(encoding="utf-8")

    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096  # avoid line wrapping

    try:
        docs = list(yaml.load_all(text))
    except Exception as e:
        print(f"YAML parse error: {e}", file=sys.stderr)
        sys.exit(1)

    used: Set[str] = set()
    for d in docs:
        collect_existing_uuids(d, used)

    processed_docs = [process(d, used, args.force, []) for d in docs]

    if args.dry_run:
        yaml.dump_all(processed_docs, sys.stdout)
        return

    if args.backup:
        path.with_suffix(path.suffix + ".bak").write_text(text, encoding="utf-8")

    with path.open("w", encoding="utf-8") as f:
        yaml.dump_all(processed_docs, f)

    print(f"Updated {path}")

if __name__ == "__main__":
    main()
