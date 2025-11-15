#!/usr/bin/env python3

"""Execute pre-start tasks defined in a YAML configuration file.

The configuration schema is intentionally minimal:

tasks:
  - name: generate plant assets            # optional identifier for logging
    enabled: true                          # optional toggle, default true
    cwd: .                                 # optional working directory, relative to --root
    env:                                   # optional environment variables
      EXAMPLE_VAR: value
    run:                                   # command to execute; string or list
      - python3
      - scripts/generate_plant_assets.py
      - --csv=custom_components/PlantDB_5335_U0.csv
      - --names
      - "ficus religiosa"
      - "hedera helix"
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence

import yaml


class ConfigError(Exception):
    """Raised when the configuration file is invalid."""


def _normalise_command(raw_cmd: object) -> List[str]:
    """Convert the configured command into a list of arguments."""
    if isinstance(raw_cmd, str):
        return shlex.split(raw_cmd)

    if isinstance(raw_cmd, Sequence):
        try:
            return [str(part) for part in raw_cmd]
        except Exception as exc:  # pragma: no cover - defensive
            raise ConfigError(f"invalid command contents: {exc}") from exc

    raise ConfigError("task 'run' must be a string or list of arguments")


def _resolve_cwd(root: Path, task: Mapping[str, object]) -> Path:
    """Determine the working directory for a task."""
    cwd_value = task.get("cwd")
    if not cwd_value:
        return root

    cwd_path = Path(str(cwd_value))
    if cwd_path.is_absolute():
        return cwd_path

    return (root / cwd_path).resolve()


def _task_enabled(task: Mapping[str, object]) -> bool:
    enabled = task.get("enabled", True)
    if isinstance(enabled, bool):
        return enabled
    if isinstance(enabled, str):
        return enabled.lower() not in {"false", "0", "no", "off"}
    raise ConfigError("task 'enabled' must be a boolean")


def _load_config(config_path: Path) -> Mapping[str, object]:
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, Mapping):
        raise ConfigError("configuration root must be a mapping")
    return data


def _build_environment(task_env: Mapping[str, object]) -> MutableMapping[str, str]:
    env = os.environ.copy()
    for key, value in task_env.items():
        env[str(key)] = str(value)
    return env


def run_tasks(config_path: Path, root: Path) -> int:
    config = _load_config(config_path)
    tasks = config.get("tasks", [])
    if not tasks:
        print(f"[prestart] no tasks defined in {config_path}", flush=True)
        return 0

    if not isinstance(tasks, Iterable):
        raise ConfigError("'tasks' must be a list")

    for index, task in enumerate(tasks, start=1):
        if not isinstance(task, Mapping):
            raise ConfigError(f"task #{index} must be a mapping")

        if not _task_enabled(task):
            continue

        name = task.get("name") or f"task_{index}"
        try:
            cmd = _normalise_command(task.get("run"))
        except ConfigError as exc:
            raise ConfigError(f"{name}: {exc}") from exc

        if not cmd:
            raise ConfigError(f"{name}: 'run' command must not be empty")

        cwd = _resolve_cwd(root, task)

        task_env = task.get("env", {})
        if task_env and not isinstance(task_env, Mapping):
            raise ConfigError(f"{name}: 'env' must be a mapping")

        env = _build_environment(task_env or {})

        cmd_display = " ".join(shlex.quote(part) for part in cmd)
        print(f"[prestart] running {name}: {cmd_display}", flush=True)
        try:
            subprocess.run(cmd, cwd=str(cwd), env=env, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"[prestart] {name} failed with exit code {exc.returncode}", file=sys.stderr, flush=True)
            return exc.returncode

    return 0


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run pre-start tasks defined in YAML.")
    parser.add_argument("--config", required=True, help="Path to the YAML file describing tasks.")
    parser.add_argument(
        "--root",
        default=None,
        help="Root directory used to resolve relative paths (defaults to directory containing the config file).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config_path = Path(args.config)

    if not config_path.exists():
        print(f"[prestart] configuration not found: {config_path}", file=sys.stderr)
        return 0

    root = Path(args.root) if args.root else config_path.parent

    try:
        return run_tasks(config_path=config_path, root=root)
    except ConfigError as exc:
        print(f"[prestart] configuration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
