#!/usr/bin/env python3
"""
Watch Home Assistant responsiveness and event-loop lag, and trigger HA Profiler
actions when lag spikes so you can see what's filling the async loop.

Requires:
  pip install websockets python-dateutil psutil
"""

import asyncio
import json
import os
import time
import subprocess
from collections import Counter, deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional, Tuple

import psutil
import websockets
from dateutil import parser as dtparser
from datetime import datetime, timezone


HA_WS = os.environ.get("HA_WS", "ws://127.0.0.1:8123/api/websocket")
HA_TOKEN = os.environ.get("HA_TOKEN")
WINDOW_S = int(os.environ.get("WINDOW_S", "120"))            # rolling stats window
PRINT_EVERY_S = int(os.environ.get("PRINT_EVERY_S", "10"))    # periodic summary
PING_EVERY_S = int(os.environ.get("PING_EVERY_S", "5"))

# Trigger thresholds (tune these)
LAG_TRIGGER_S = float(os.environ.get("LAG_TRIGGER_S", "2.0"))         # event.time_fired lag
PING_TRIGGER_S = float(os.environ.get("PING_TRIGGER_S", "0.75"))      # ping RTT
EVENTRATE_TRIGGER = float(os.environ.get("EVENTRATE_TRIGGER", "25"))  # events/sec

# Profiler actions to trigger when lagging
ENABLE_PROFILER_START = os.environ.get("ENABLE_PROFILER_START", "1") == "1"
PROFILER_SECONDS = float(os.environ.get("PROFILER_SECONDS", "30.0"))
TRIGGER_COOLDOWN_S = int(os.environ.get("TRIGGER_COOLDOWN_S", "300")) # don't spam profiler

# Optional: grab docker container PIDs for correlated host stats
DOCKER_CONTAINERS = [c.strip() for c in os.environ.get("DOCKER_CONTAINERS", "").split(",") if c.strip()]


@dataclass
class WsPing:
    sent_monotonic: float


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_ha_time(s: str) -> datetime:
    # HA uses ISO8601 with timezone, like "2025-12-26T01:12:40.119711+00:00"
    return dtparser.isoparse(s)


def safe_run(cmd: list[str], timeout: float = 2.0) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=timeout)
        return out.decode("utf-8", "replace").strip()
    except Exception as e:
        return f"<error running {' '.join(cmd)}: {e}>"


def docker_pid(container: str) -> Optional[int]:
    if not container:
        return None
    out = safe_run(["docker", "inspect", "-f", "{{.State.Pid}}", container])
    try:
        pid = int(out.strip())
        return pid if pid > 0 else None
    except Exception:
        return None


def proc_snapshot(pid: int) -> Dict[str, float | int | str]:
    try:
        p = psutil.Process(pid)
        with p.oneshot():
            return {
                "pid": pid,
                "name": p.name(),
                "cpu_pct": p.cpu_percent(interval=None),
                "mem_rss_mb": round(p.memory_info().rss / (1024 * 1024), 1),
                "threads": p.num_threads(),
                "fds": p.num_fds() if hasattr(p, "num_fds") else -1,
            }
    except Exception as e:
        return {"pid": pid, "error": str(e)}


def host_snapshot() -> Dict[str, object]:
    load1, load5, load15 = os.getloadavg()
    vm = psutil.virtual_memory()
    cpu_times = psutil.cpu_times_percent(interval=None)
    return {
        "load": {"1": round(load1, 2), "5": round(load5, 2), "15": round(load15, 2)},
        "cpu": {
            "user": round(cpu_times.user, 1),
            "system": round(cpu_times.system, 1),
            "iowait": round(getattr(cpu_times, "iowait", 0.0), 1),
            "idle": round(cpu_times.idle, 1),
        },
        "mem": {
            "used_gb": round((vm.total - vm.available) / (1024**3), 2),
            "avail_gb": round(vm.available / (1024**3), 2),
            "pct": vm.percent,
        },
    }


async def ws_call_service(ws, msg_id: int, domain: str, service: str, service_data: Optional[dict] = None) -> None:
    payload = {
        "id": msg_id,
        "type": "call_service",
        "domain": domain,
        "service": service,
        "service_data": service_data or {},
    }
    await ws.send(json.dumps(payload))


async def main():
    if not HA_TOKEN:
        raise SystemExit("Set HA_TOKEN env var to a Long-Lived Access Token.")

    # Rolling window of events: (recv_monotonic, entity_id, attr_only, lag_s)
    events: Deque[Tuple[float, str, bool, float]] = deque()

    pending_pings: Dict[int, WsPing] = {}
    last_ping_rtt: Optional[float] = None
    max_lag_recent: float = 0.0
    last_trigger: float = 0.0

    next_id = 1

    async with websockets.connect(HA_WS, max_size=25_000_000) as ws:
        # auth
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_required":
            raise RuntimeError(f"Unexpected: {msg}")
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_ok":
            raise RuntimeError(f"Auth failed: {msg}")

        # enable coalescing so HA can batch websocket messages (reduces overhead)
        # Must be id=1 per docs.
        await ws.send(json.dumps({"id": 1, "type": "supported_features", "features": {"coalesce_messages": 1}}))
        _ = json.loads(await ws.recv())
        next_id = 2

        # subscribe to state_changed
        await ws.send(json.dumps({"id": next_id, "type": "subscribe_events", "event_type": "state_changed"}))
        sub_resp = json.loads(await ws.recv())
        if not (sub_resp.get("type") == "result" and sub_resp.get("success")):
            raise RuntimeError(f"subscribe_events failed: {sub_resp}")
        next_id += 1

        async def ping_loop():
            nonlocal next_id
            while True:
                await asyncio.sleep(PING_EVERY_S)
                pid = next_id
                next_id += 1
                pending_pings[pid] = WsPing(sent_monotonic=time.monotonic())
                await ws.send(json.dumps({"id": pid, "type": "ping"}))

        async def printer_loop():
            nonlocal last_ping_rtt, max_lag_recent
            while True:
                await asyncio.sleep(PRINT_EVERY_S)

                now_m = time.monotonic()
                cutoff = now_m - WINDOW_S
                while events and events[0][0] < cutoff:
                    events.popleft()

                # Stats
                total = len(events)
                if total:
                    lag_vals = [e[3] for e in events]
                    max_lag = max(lag_vals)
                    max_lag_recent = max_lag
                    # crude p95
                    lag_vals_sorted = sorted(lag_vals)
                    p95 = lag_vals_sorted[int(0.95 * (len(lag_vals_sorted) - 1))]
                    rate = total / WINDOW_S
                else:
                    max_lag = p95 = rate = 0.0
                    max_lag_recent = 0.0

                # top talkers in window
                c_state = Counter()
                c_attr_only = Counter()
                for _, ent, attr_only, _ in events:
                    c_state[ent] += 1
                    if attr_only:
                        c_attr_only[ent] += 1

                print("=" * 90)
                print(f"{utc_now().isoformat()} window={WINDOW_S}s  events={total}  rate={rate:.2f}/s  "
                      f"lag_p95={p95:.3f}s  lag_max={max_lag:.3f}s  ping_rtt={last_ping_rtt if last_ping_rtt is not None else 'n/a'}")
                print("Top state_changed:")
                for ent, n in c_state.most_common(10):
                    print(f"  {n:5d}  {ent}")
                if c_attr_only:
                    print("Top attr-only:")
                    for ent, n in c_attr_only.most_common(10):
                        print(f"  {n:5d}  {ent}")

                # Host + container correlation
                hs = host_snapshot()
                print(f"Host: load={hs['load']} cpu={hs['cpu']} mem={hs['mem']}")
                if DOCKER_CONTAINERS:
                    for c in DOCKER_CONTAINERS:
                        pid = docker_pid(c)
                        if pid:
                            print(f"ContainerPID: {c} -> {proc_snapshot(pid)}")
                        else:
                            print(f"ContainerPID: {c} -> <no pid>")

        asyncio.create_task(ping_loop())
        asyncio.create_task(printer_loop())

        while True:
            raw = await ws.recv()
            decoded = json.loads(raw)

            # HA may coalesce multiple websocket messages into a JSON list
            msgs = decoded if isinstance(decoded, list) else [decoded]

            for data in msgs:
                # Handle pong RTT
                if data.get("type") == "pong":
                    pid = data.get("id")
                    ping = pending_pings.pop(pid, None)
                    if ping:
                        last_ping_rtt = round(time.monotonic() - ping.sent_monotonic, 3)
                    continue

                if data.get("type") != "event":
                    continue

                ev = data.get("event", {})
                tf = ev.get("time_fired")
                if not tf:
                    continue

                lag_s = (utc_now() - parse_ha_time(tf)).total_seconds()
                d = ev.get("data", {})
                ent = d.get("entity_id")
                if not ent:
                    continue

                old = d.get("old_state")
                new = d.get("new_state")
                attr_only = False
                try:
                    if old and new and old.get("state") == new.get("state"):
                        attr_only = True
                except Exception:
                    pass

                events.append((time.monotonic(), ent, attr_only, lag_s))

                # --- trigger logic unchanged below ---
                now_m = time.monotonic()
                cutoff = now_m - WINDOW_S
                while events and events[0][0] < cutoff:
                    events.popleft()

                rate = (len(events) / WINDOW_S) if WINDOW_S else 0.0
                lag_triggered = lag_s >= LAG_TRIGGER_S
                ping_triggered = (last_ping_rtt is not None and last_ping_rtt >= PING_TRIGGER_S)
                rate_triggered = rate >= EVENTRATE_TRIGGER

                if (lag_triggered or ping_triggered or rate_triggered) and (now_m - last_trigger) >= TRIGGER_COOLDOWN_S:
                    last_trigger = now_m
                    stamp = utc_now().isoformat()
                    print("\n" + "!" * 90)
                    print(f"{stamp} TRIGGER: lag={lag_s:.3f}s (thr {LAG_TRIGGER_S}) "
                          f"ping={last_ping_rtt} (thr {PING_TRIGGER_S}) rate={rate:.2f}/s (thr {EVENTRATE_TRIGGER})")
                    print("Calling Profiler actions... (check HA logs + persistent notifications)")

                    await ws_call_service(ws, next_id, "profiler", "log_current_tasks"); next_id += 1
                    await ws_call_service(ws, next_id, "profiler", "log_event_loop_scheduled"); next_id += 1
                    await ws_call_service(ws, next_id, "profiler", "log_thread_frames"); next_id += 1

                    if ENABLE_PROFILER_START:
                        await ws_call_service(ws, next_id, "profiler", "start", {"seconds": PROFILER_SECONDS})
                        next_id += 1

                    print("!" * 90 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
