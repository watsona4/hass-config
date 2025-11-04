#!/usr/bin/env python3
import argparse
import copy
import glob
import os
import re
import sys
from typing import Any, Dict, List, Optional, Union

import yaml

# ---------------- YAML loader with root-aware !include ----------------


class LoaderWithIncludes(yaml.SafeLoader):
    def __init__(self, stream, current_dir: Optional[str] = None, root: Optional[str] = None):
        super().__init__(stream)
        if hasattr(stream, "name"):
            p = os.path.abspath(stream.name)
            self._current_dir = os.path.dirname(p)
        else:
            self._current_dir = os.path.abspath(current_dir or os.getcwd())
        self._root = os.path.abspath(root or self._current_dir)


def _resolve_path(loader: LoaderWithIncludes, relpath: str) -> str:
    if os.path.isabs(relpath):
        return relpath
    cand1 = os.path.abspath(os.path.join(loader._current_dir, relpath))
    if os.path.exists(cand1):
        return cand1
    cand2 = os.path.abspath(os.path.join(loader._root, relpath))
    return cand2


def load_yaml(path: str, root: Optional[str] = None):
    with open(path, "r", encoding="utf-8") as f:
        loader = LoaderWithIncludes(f, root=root)
        try:
            return loader.get_single_data()
        finally:
            loader.dispose()


def _construct_include(loader: LoaderWithIncludes, node: yaml.Node):
    rel = loader.construct_scalar(node)
    file_path = _resolve_path(loader, rel)
    return load_yaml(file_path, root=loader._root)


def _construct_include_dir_merge_named(loader: LoaderWithIncludes, node: yaml.Node):
    rel = loader.construct_scalar(node)
    dir_path = _resolve_path(loader, rel)
    out: Dict[str, Any] = {}
    for path in sorted(glob.glob(os.path.join(dir_path, "*.yaml")) + glob.glob(os.path.join(dir_path, "*.yml"))):
        data = load_yaml(path, root=loader._root)
        if isinstance(data, dict):
            out.update(data)
    return out


def _construct_include_dir_list(loader: LoaderWithIncludes, node: yaml.Node):
    rel = loader.construct_scalar(node)
    dir_path = _resolve_path(loader, rel)
    out: List[Any] = []
    for path in sorted(glob.glob(os.path.join(dir_path, "*.yaml")) + glob.glob(os.path.join(dir_path, "*.yml"))):
        data = load_yaml(path, root=loader._root)
        if isinstance(data, list):
            out.extend(data)
        elif data is not None:
            out.append(data)
    return out


LoaderWithIncludes.add_constructor("!include", _construct_include)
LoaderWithIncludes.add_constructor("!include_dir_merge_named", _construct_include_dir_merge_named)
LoaderWithIncludes.add_constructor("!include_dir_list", _construct_include_dir_list)

# ---------------- Decluttering expansion ----------------

# Only substitute decluttering placeholders [[var]] (do NOT touch Jinja)
RE_DBLBRACK = re.compile(r"\[\[\s*([A-Za-z_]\w*)\s*\]\]")


def normalize_variables(vars_in: Union[None, Dict[str, Any], List[Dict[str, Any]], Any]) -> Dict[str, Any]:
    if vars_in is None:
        return {}
    if isinstance(vars_in, dict):
        return dict(vars_in)
    out: Dict[str, Any] = {}
    if isinstance(vars_in, list):
        for item in vars_in:
            if isinstance(item, dict):
                if len(item) == 1:
                    k, v = next(iter(item.items()))
                    out[k] = v
                else:
                    out.update(item)
    return out


def substitute_declutter_in_str(s: str, vars_map: Dict[str, Any]) -> str:
    def _rep(m: re.Match) -> str:
        key = m.group(1)
        return str(vars_map.get(key, m.group(0)))

    return RE_DBLBRACK.sub(_rep, s)


def deep_substitute_declutter(obj: Any, vars_map: Dict[str, Any]) -> Any:
    if isinstance(obj, dict):
        return {k: deep_substitute_declutter(v, vars_map) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_substitute_declutter(x, vars_map) for x in obj]
    if isinstance(obj, str):
        # leave {{ ... }} / {% ... %} / {# ... #} untouched
        return substitute_declutter_in_str(obj, vars_map)
    return obj


def collect_decluttering_templates(obj: Any) -> Dict[str, Any]:
    found: Dict[str, Any] = {}

    def _walk(node: Any):
        if isinstance(node, dict):
            if "decluttering_templates" in node and isinstance(node["decluttering_templates"], dict):
                for k, v in node["decluttering_templates"].items():
                    if k not in found:
                        found[k] = v
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for v in node:
                _walk(v)

    _walk(obj)
    return found


def deep_merge(a: Any, b: Any) -> Any:
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = deep_merge(out[k], v) if k in out else copy.deepcopy(v)
        return out
    if isinstance(a, list) and isinstance(b, list):
        return a + copy.deepcopy(b)
    return copy.deepcopy(b)


def apply_template_single(template_body: Any, vars_map: Dict[str, Any]) -> Any:
    tpl = copy.deepcopy(template_body)
    return deep_substitute_declutter(tpl, vars_map)


def expand_decluttering_nodes(node: Any, templates: Dict[str, Any]) -> Any:
    if isinstance(node, list):
        return [expand_decluttering_nodes(n, templates) for n in node]
    if isinstance(node, dict):
        node = {k: expand_decluttering_nodes(v, templates) for k, v in node.items()}
        if node.get("type") == "custom:decluttering-card":
            tpl_spec = node.get("template")
            vars_map = normalize_variables(node.get("variables"))
            if tpl_spec is None:
                return node
            names = tpl_spec if isinstance(tpl_spec, list) else [tpl_spec]
            result: Any = {}
            for name in names:
                if name not in templates:
                    raise KeyError(f"Decluttering template '{name}' not found")
                body = templates[name]
                expanded = apply_template_single(body, vars_map)
                result = deep_merge(result, expanded)
            overrides = {k: v for k, v in node.items() if k not in ("type", "template", "variables")}
            result = deep_merge(result, overrides)
            return expand_decluttering_nodes(result, templates)
        return node
    return node


def strip_keys(obj: Any, keys: List[str]) -> Any:
    if isinstance(obj, dict):
        return {k: strip_keys(v, keys) for k, v in obj.items() if k not in keys}
    if isinstance(obj, list):
        return [strip_keys(x, keys) for x in obj]
    return obj


# ---------------- YAML dump that preserves Jinja literally ----------------


class LiteralDumper(yaml.SafeDumper):
    pass


def _repr_str_preserve(data: str):
    """
    Represent strings:
    - If they contain newlines OR Jinja delimiters, write as literal block (|) without folding.
    - Otherwise write as plain scalars.
    """
    has_newline = "\n" in data
    has_jinja = ("{{" in data) or ("{%" in data) or ("{#" in data)
    node = yaml.ScalarNode(tag="tag:yaml.org,2002:str", value=data, style="|" if (has_newline or has_jinja) else None)
    return node


LiteralDumper.add_representer(str, lambda dumper, data: _repr_str_preserve(data))

# Avoid line-wrapping which could reflow Jinja
LiteralDumper.width = 10**9  # effectively no wrap

# ---------------- CLI ----------------


def main():
    ap = argparse.ArgumentParser(
        description="Expand decluttering-card templates into literal Lovelace YAML (no templates, Jinja preserved)."
    )
    ap.add_argument("-i", "--input", required=True, help="Input dashboard YAML")
    ap.add_argument("-o", "--output", required=True, help="Output expanded YAML")
    ap.add_argument("--root", help="UI root (e.g. /config) for resolving top-level includes", default=None)
    args = ap.parse_args()

    data = load_yaml(os.path.abspath(args.input), root=args.root)

    templates = collect_decluttering_templates(data)
    expanded = expand_decluttering_nodes(data, templates)

    # strip decluttering_templates from the result
    expanded = strip_keys(expanded, ["decluttering_templates"])

    with open(args.output, "w", encoding="utf-8") as f:
        yaml.dump(expanded, f, Dumper=LiteralDumper, sort_keys=False, allow_unicode=True)

    print(f"Wrote expanded dashboard to {args.output}")


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    main()
