#!/usr/bin/env python3
# Usage: zwift_player_status.py <relay_host> <world_id> <player_id> <token> [token_type]
# token_type: "id" or "access" (default: auto)

import sys, json, requests
sys.path.insert(0, "/config/scripts")
import zwift_messages_pb2 as zmsg  # make sure this file is next to this script

def fetch_player_state(relay_host, world_id, player_id, bearer, accept):
    url = f"https://{relay_host}/relay/worlds/{world_id}/players/{player_id}"
    r = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {bearer}",
            # try different Accepts; caller may vary
            "Accept": accept,
            # UA similar to real app helps some edges
            "User-Agent": "ZwiftMobileLink/5.0 (HA)"
        },
        timeout=10,
    )
    return r

def main():
    if len(sys.argv) < 5:
        print("Usage: zwift_player_status.py <relay_host> <world_id> <player_id> <token> [token_type]", file=sys.stderr)
        sys.exit(1)

    relay_host, world_id, player_id, token = sys.argv[1:5]
    token_type = (sys.argv[5] if len(sys.argv) >= 6 else "").lower()

    # Try a couple of Accept headers (some relays prefer different ones)
    accepts = [
        "application/octet-stream",
        "application/x-protobuf",
        "application/vnd.google.protobuf",
        "*/*",
    ]

    # If caller didn’t force token type, just try with the given token first.
    # If we get 401/406, suggest switching to id_token.
    last_err = None
    for accept in accepts:
        try:
            r = fetch_player_state(relay_host, world_id, player_id, token, accept)
            if r.status_code == 200:
                ps = zmsg.PlayerState()
                ps.ParseFromString(r.content)
                speed_mps = ps.speed / 1_000_000.0
                speed_kmh = speed_mps * 3.6
                cadence_rpm = int((ps.cadenceUHz * 60) / 1_000_000)
                altitude_m = (float(ps.altitude) - 9000.0) / 2.0
                out = {
                    "id": ps.id,
                    "distance_m": float(ps.distance),
                    "speed_mps": speed_mps,
                    "speed_kmh": speed_kmh,
                    "heartrate_bpm": int(ps.heartrate),
                    "power_w": int(ps.power),
                    "cadence_rpm": cadence_rpm,
                    "altitude_m": altitude_m,
                    "world_time": int(ps.worldTime),
                    "just_watching": int(ps.justWatching),
                    "calories": int(ps.calories),
                    "climbing": ps.climbing,
                    "customization_id": ps.customisationId,
                    "group_id": ps.groupId,
                    "heading": ps.heading,
                    "laps": ps.laps,
                    "lean": ps.lean,
                    "progress": ps.progress,
                    "road_position": ps.roadPosition,
                    "road_time": ps.roadTime,
                    "sport": ps.sport,
                    "time": ps.time,
                    "watching_rider_id": ps.watchingRiderId,
                    "x": ps.x,
                    "y": ps.y,
                }
                print(json.dumps(out))
                return
            else:
                last_err = f"HTTP {r.status_code} (Accept={accept})"
                # 406/401 → try next Accept or token type
                continue
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            continue

    # If we still failed and user passed "access", hint to try id_token
    if last_err and token_type == "access":
        print(json.dumps({"error": last_err, "hint": "Try id_token for relay endpoints"}))
        sys.exit(2)
    else:
        print(json.dumps({"error": last_err}))
        sys.exit(2)

if __name__ == "__main__":
    main()
