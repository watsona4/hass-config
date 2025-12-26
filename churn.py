#!/usr/bin/env python3
import asyncio, json, os, time
from collections import Counter
import websockets

HA_URL = os.environ.get("HA_URL", "ws://127.0.0.1:8123/api/websocket")
TOKEN = os.environ["HA_TOKEN"]  # long-lived access token
DURATION = int(os.environ.get("DURATION", "60"))

async def main():
    counts = Counter()
    attr_only = Counter()
    start = time.time()

    async with websockets.connect(HA_URL, max_size=10_000_000) as ws:
        # auth
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_required":
            raise RuntimeError(msg)
        await ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_ok":
            raise RuntimeError(msg)

        # subscribe to state_changed
        await ws.send(json.dumps({"id": 1, "type": "subscribe_events", "event_type": "state_changed"}))
        msg = json.loads(await ws.recv())
        if not (msg.get("type") == "result" and msg.get("success")):
            raise RuntimeError(msg)

        # collect
        while time.time() - start < DURATION:
            data = json.loads(await ws.recv())
            if data.get("type") != "event":
                continue
            ev = data.get("event", {})
            ent = ev.get("data", {}).get("entity_id")
            if ent:
                counts[ent] += 1
            old = ev.get("data", {}).get("old_state")
            new = ev.get("data", {}).get("new_state")
            if old and new:
                if old.get("state") == new.get("state"):
                    attr_only[ent] += 1

    print(f"Top state_changed entities over {DURATION}s:")
    for ent, n in counts.most_common(30):
        print(f"{n:5d}  {ent}")

    print(f"Top attr_changed entities over {DURATION}s:")
    for ent, n in attr_only.most_common(30):
        print(f"{n:5d}  {ent}")

if __name__ == "__main__":
    asyncio.run(main())
