#!/usr/bin/env python3
import argparse, os, sys, json, hashlib
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Undefined
try:
    import yaml  # PyYAML
except Exception:
    yaml = None

def write_if_changed(path: Path, data: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if hashlib.sha256(old.encode()).hexdigest() == hashlib.sha256(data.encode()).hexdigest():
        return False
    path.write_text(data, encoding="utf-8")
    return True

def render_one(env, template_path: str, out_path: str, variables: dict):
    tpl = env.get_template(template_path)
    out = tpl.render(**variables)
    changed = write_if_changed(Path(out_path), out)
    status = "UPDATED" if changed else "OK"
    print(f"[{status}] {template_path} -> {out_path}")
    return changed

def load_vars_from_kv(kvs):
    result = {}
    for kv in kvs or []:
        if "=" not in kv:
            raise SystemExit(f"--var expects key=value; got: {kv}")
        k, v = kv.split("=", 1)
        try:
            result[k] = json.loads(v)  # allow numbers, bool, lists via JSON
        except Exception:
            result[k] = v
    return result

def main():
    p = argparse.ArgumentParser(description="Render Jinja2 templates to includes/")
    p.add_argument("--template-root", default=".", help="Root path for templates (default: current dir)")
    p.add_argument("--template", action="append", help="Template path (relative to template-root). Repeatable.")
    p.add_argument("--out", action="append", help="Output path matching --template order. Repeatable.")
    p.add_argument("--var", action="append", help="Template variable as key=value (JSON accepted). Repeatable.")
    p.add_argument("--config", help="YAML config listing multiple renders")
    p.add_argument("--strict", action="store_true", help="Fail if a variable is undefined")
    args = p.parse_args()

    loader = FileSystemLoader(Path(args.template_root).resolve())
    common_kwargs = dict(loader=loader, keep_trailing_newline=True)
    if args.strict:
        env = Environment(undefined=StrictUndefined, **common_kwargs)
    else:
        # either omit 'undefined' entirely or set to the base Undefined class
        env = Environment(undefined=Undefined, **common_kwargs)
    # Expose environment variables as `env.*`
    env.globals["env"] = dict(os.environ)

    any_changed = False

    if args.config:
        if not yaml:
            raise SystemExit("PyYAML not installed. `pip install pyyaml`")
        cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
        for item in cfg.get("renders", []):
            tpl = item["template"]
            out = item["out"]
            vars_inline = item.get("vars", {})
            any_changed |= render_one(env, tpl, out, vars_inline)
    else:
        if not args.template or not args.out or len(args.template) != len(args.out):
            raise SystemExit("Provide equal counts of --template and --out, or use --config")
        vars_inline = load_vars_from_kv(args.var)
        for tpl, out in zip(args.template, args.out):
            any_changed |= render_one(env, tpl, out, vars_inline)

    sys.exit(0 if not any_changed else 0)

if __name__ == "__main__":
    main()
