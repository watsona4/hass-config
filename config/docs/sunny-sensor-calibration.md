# Sunny Sensor Calibration — Instructions for a Future Claude Session

**Goal:** improve `binary_sensor.sunny` so it correctly reports "is it sunny
outside" despite (a) heavy trees that block the Ambient weather station's
pyranometer from much of the sky, and (b) the sun's path moving through the
year (this site is far enough north that July vs December sun geometry differs
a lot). The owner will, over time, tell you "day X was sunny" / "day Y was
cloudy." Use those labels + the recorder history to fit a better model and
re-encode the sensor.

Read this whole file before changing anything. Follow the project style guides
(`config/yaml-style-guide.md`, `config/jinja2-style-guide.md`).

---

## 1. Current state (starting point)

- **`binary_sensor.sunny`** — `config/includes/template.yaml`. Current rule:
  `sun elevation > 3 AND sensor.solar_radiation_max_20m >= 300 W/m²`.
  (delay_on 2m, delay_off 5m.) This is a **direct-beam spike detector**: the
  beam punching through canopy gaps spikes solar radiation past any overcast
  value. It works once the sun reaches the sensor but reads "off" while the sun
  is fully behind trees — even on a clear day.
- **`sensor.solar_radiation_max_20m`** — `config/includes/sensor.yaml`
  (statistics, `value_max`, 20 min). The rolling peak the rule above uses.
- Data entities:
  - `sensor.ambient_solarradiation` (W/m²) — the real measurement. **Entity ID
    has changed before** (was `sensor.ambient_solar_radiation`, briefly
    `sensor.ecowitt_solarradiation` — see the Gotcha in Section 9 about what
    an entity rename does to your ability to pull historical data). Confirm
    the current name against `includes/sensor.yaml`/`includes/template.yaml`
    before trusting this doc.
  - `sensor.ambient_illuminance` (lux) — **derived** as `solar_radiation * 126.7`
    (there is no independent lux sensor), so it carries no extra information
    beyond solar radiation. Treat solar radiation as the ground truth.
  - `sensor.sun_solar_elevation` (°), `sensor.sun_solar_azimuth` (°) — sun
    position, recorded in the DB. These have NOT been renamed and are safe to
    trust across the whole history.

## 2. The two physical facts to exploit

1. **The trees occupy FIXED sky sectors.** Whether the beam reaches the sensor
   depends only on the sun's **(azimuth, elevation)** — a sky position, not a
   clock time. So if you model everything as a function of (az, el), the model
   is **season-invariant**: a low winter sun at some (az, el) behind a tree is
   the same block as any other time the sun sits at that (az, el). Season only
   matters because the sun *visits different (az, el) paths* in different
   months — which is exactly why you need labeled days spread across the year:
   to populate the (az, el) regions winter vs summer sun reaches.

2. **Diffuse light while the beam is blocked — TESTED, and it is INVERTED
   (do not use a naive "dimmer = cloudy" rule).** The original hypothesis was
   that a clear sky is brighter than overcast even under the canopy. The first
   cloudy reference (2026-07-14, a bright overcast) disproved it: at matching
   blocked-morning sky positions the OVERCAST day read *higher* than the sunny
   reference days (blocked-morning median cloudy 66 vs sunny 52 W/m²; ratios up
   to 2.2 at el 20-30). Physics: while the direct beam is tree-blocked the
   sensor sees only diffuse light, and an overcast dome radiates strong diffuse
   from all directions (incl. the gaps), whereas a clear blue sky has weak
   diffuse and hides its energy in the blocked beam. So under the canopy cloudy
   is often BRIGHTER than clear, and the separation is noisy (depends on cloud
   thickness — a thick dark storm would read low). **Conclusion: the robust
   clear-vs-cloudy discriminator is the direct-beam SPIKE, not the diffuse
   level.** Only revisit a diffuse-based rule if many cloudy references (thick
   AND thin) reveal a consistent, monotonic band — otherwise leave it out.

## 3. Target model

Build two references over sky position (az, el):

- `clear_ref(az, el)`  = irradiance seen on **labeled sunny** days at that (az, el).
- `cloudy_ref(az, el)` = irradiance seen on **labeled cloudy** days at that (az, el).

Classification at runtime, given the current (az, el) and the current reading:

```
midpoint(az, el) = geometric_mean(clear_ref, cloudy_ref)   # or clear-weighted, tune it
sunny = reading is closer to clear_ref than cloudy_ref  (reading >= midpoint)
```

Keep the **beam-spike** term too — combine as OR:
`sunny = (recent_max_solar >= beam_threshold(el))  OR  (reading >= midpoint(az, el))`.
The first catches obvious direct sun; the second catches clear-but-still-blocked
skies via the diffuse level. Each day is a 1-D path through (az, el) space, so
sunny/cloudy days each contribute a curve; many days across seasons fill the map.

## 4. CRITICAL constraint — recorder purges after 30 days

`recorder.purge_keep_days: 30`. Raw history for a labeled day **disappears after
~30 days.** Therefore you MUST extract and persist each labeled day's aggregated
(az, el) → irradiance curve *promptly* (within 30 days of the date), into a
durable file. Never rely on being able to re-pull an old labeled day.

- Labels live in `config/docs/sunny-sensor-labels.csv` (`date,label,notes`).
- Persisted per-day aggregates live in `config/docs/sunny-sensor-references.csv`
  (create it if missing; schema below). Each calibration run: for every label
  not yet represented in the references file AND still inside the recorder
  window, extract and append its curve. Then fit from the references file — it
  outlives the raw data and accumulates all seasons.

`sunny-sensor-references.csv` schema (one row per (day, az-bin, el-bin)):
```
date,label,az_bin,el_bin,sr_median,sr_p90,sr_max,n
```
Bin suggestion: az in 5° bins, el in 5° bins.

## 5. How to pull the data

Get the recorder DSN from `config/configuration.yaml` (`recorder.db_url`) — do
not hardcode the password. Connect with `psql`/pandas. **The DB session
timezone is local (America/New_York); `to_timestamp()` returns local time.** Be
deliberate about UTC vs local.

Per-entity history for a given local date:
```sql
SELECT s.last_updated_ts, s.state
FROM states s JOIN states_meta m ON s.metadata_id = m.metadata_id
WHERE m.entity_id = :entity
  AND s.state ~ '^-?[0-9.]+$'
  AND to_timestamp(s.last_updated_ts)::date = DATE :day
ORDER BY s.last_updated_ts;
```
Pull `sensor.ambient_solarradiation` (verify the current name first — see
Section 9), `sensor.sun_solar_elevation`, `sensor.sun_solar_azimuth`; align
with pandas `merge_asof` (nearest, 3 min tolerance); then
`groupby([az_bin, el_bin])` and aggregate median/p90/max. (Elevation/azimuth
are recorded less often than solar radiation, hence asof.)

## 6. Procedure for the session

1. Read `sunny-sensor-labels.csv` and `sunny-sensor-references.csv`.
2. For each label missing from references and still within ~30 days: pull +
   aggregate (Section 5), append to `sunny-sensor-references.csv`. Log any
   labeled day already purged (data unrecoverable) so the owner knows.
3. Fit `clear_ref` and `cloudy_ref` over (az, el) from the references file.
   Start simple: bin/interpolate; only fit a smooth function if it clearly
   helps. Sanity-check separation — clear should sit well above cloudy at the
   sky positions where the sensor sees sky.
4. Choose `beam_threshold(el)` and the midpoint blend; validate against every
   labeled day (each should classify correctly) and spot-check the last few
   days vs the owner's memory.
5. Re-encode the model (Section 7), run the config check (Section 8), report
   what changed, and ask before leaving it live if the change is large.
6. **Housekeeping:** append any newly-cached days to the references file, add a
   dated "last calibrated / points used" note at the bottom of this file, and
   update the memory `[[sunny-sensor-tree-obstruction]]`.

## 7. Encoding the model back into HA

Keep runtime logic simple and inspectable. Preferred: embed a compact lookup in
the `binary_sensor.sunny` template — e.g. a Jinja list of
`[el_lo, az_lo, az_hi, clear_ref, cloudy_ref]` rows, pick the row matching the
current (el, az), compare. If the table gets large, generate it into a small
helper file the way `scripts/generate_plant_assets.py` generates packages, and
keep the raw table in `config/docs/`. Whatever you choose:
- `binary_sensor.sunny` must stay in YAML (it uses `delay_on`/`delay_off`).
- Preserve the `elevation > 3` guard and the availability template.
- Keep `sensor.solar_radiation_max_20m` for the beam term.

## 8. Validate

```bash
docker exec homeassistant python -m homeassistant --script check_config -c /config
```
Then have the owner reload (Developer Tools → YAML → Reload all YAML, or
`homeassistant.reload_all`) — no restart needed. There is usually no
service-capable token available in the Claude shell, so expect to hand the
reload to the owner.

## 9. Gotchas

- DB timezone is local, not UTC (Section 5).
- 30-day purge (Section 4) — persist promptly.
- `ambient_illuminance` is just `solar_radiation × 126.7`; don't treat it as an
  independent sensor.
- If the Ambient feed shows `unavailable` gaps, drop those rows before fitting.
- Don't over-fit to one or two days; prefer more labeled points across seasons.
- **An entity rename orphans raw `states` history for that name, even if
  long-term `statistics` were separately migrated to preserve it (found
  2026-08-01).** The weather source has been renamed at least twice
  (`ambient_*` → `ecowitt_*` → back to `ambient_*`, matching whichever prefix
  `ecowitt2mqtt`'s `HASS_ENTITY_ID_PREFIX` was set to at the time). A prior
  session migrated the **`statistics`/`statistics_short_term`** tables
  (hourly/5-min aggregates) to carry old history onto the new name — so
  `sensor.ambient_solarradiation`'s hourly stats correctly go back to
  2026-06-29. But the **raw `states` table** (Section 5's per-timestamp query,
  needed to bin by (az, el) since `statistics` doesn't carry azimuth/elevation)
  was NOT migrated and starts fresh at whatever moment the current name first
  went live — check with:
  ```sql
  select min(to_timestamp(s.last_updated_ts))
  from states s join states_meta m on s.metadata_id=m.metadata_id
  where m.entity_id='sensor.ambient_solarradiation';
  ```
  If a labeled day predates that timestamp, look it up in `states_meta` under
  the OLD entity name instead (e.g. `select entity_id from states_meta where
  entity_id ilike '%solarradiation%'` to see every name this metric has ever
  been recorded under) — as long as that old name's raw states haven't been
  purged (30 days), the (az, el) data for that day is still there under it.
  Bottom line: **always confirm the raw-states start date for whatever entity
  name you're about to query, per label date, before assuming it covers that
  day** — don't just trust this doc's Section 1 name.

---

## Smoke / PM2.5 (added 2026-07-15)

Wildfire smoke is a recurring summer regime and is a THIRD sky state, distinct
from clear and cloudy. Optically it scatters the direct beam (pyranometer reads
low, like cloud) but is obvious in PM2.5. Reference 2026-07-15: outdoor PM2.5
avg 41 / max 93 µg/m³ vs 6-13 avg (≤30 peak) on the clear/cloudy days; beam
~90% killed (solar peak 99 vs 1009 clear at the same late-morning window).

**Owner decision:** a smoky-but-cloudless day should read `sunny = on` (clear
sky, just hazy). Implemented as:
- `sensor.outdoor_pm25_mean_1h` (statistics mean, 60 min) and
  `binary_sensor.smoky` = mean > 35 µg/m³ (delays 10m/20m).
- `binary_sensor.sunny` gains an OR branch `smoky and peak >= 50`: on a smoky
  day the ≥400 beam requirement is relaxed to a low daylight floor.

**Assumption + limitation:** this treats "smoky" as "otherwise clear" — true for
the typical high-pressure smoke event, but a smoky AND genuinely cloudy/rainy
day would false-positive to sunny. To refine: have the owner label a
smoky-AND-cloudy day, then find a discriminator (e.g. the afternoon open-sky
level in the az 220-260 clear window, or signal smoothness/variance) and tighten
the smoke branch. The 35 µg/m³ threshold may also need seasonal/site tuning.

## Calibration log

- 2026-07-12 — Initial spike-detector model installed (`solar_radiation_max_20m
  >= 400`). Reference days: 2026-07-11 sunny, 2026-07-12 sunny.
- 2026-07-14 — First cloudy reference (bright overcast). Cached per-(az,el)
  aggregates for all three days into `sunny-sensor-references.csv` (durable vs
  the 30-day purge). **Key result: the diffuse clear-vs-cloudy discriminator is
  inverted/unreliable (see Section 2.2) — dropped from the plan.** The
  spike-detector was validated: overcast peaked at 136 W/m² and never
  approached 400, so the new rule correctly stays "off." Owner clarified this
  was a THIN/BRIGHT overcast (near-worst-case luminance), not dark/heavy — so
  400 has comfortable headroom above even bright overcast, which also means
  `beam_threshold(el)` can be safely lowered for low winter sun (weaker sunny
  spikes) without risking bright-overcast false positives. NOTE: as of this date
  the reload had not yet been run, so the OLD `illuminance > 10000` rule was
  still live and (wrongly) reported "on" on this overcast day. Still need: the
  reload, and more labeled days across seasons to tune `beam_threshold(el)` and
  map when the sun clears the trees at lower winter elevations.
- 2026-07-15 — Added smoke handling (PM2.5). New `sensor.outdoor_pm25_mean_1h` +
  `binary_sensor.smoky` (>35 µg/m³ 1h mean); `binary_sensor.sunny` gains a
  `smoky and peak >= 50` branch so smoky-but-clear days read sunny (owner
  decision "on if cloudless"). Smoke ~90% killed the beam (peak 99 vs 1009
  clear). Cached 07-15 smoky aggregates to `sunny-sensor-references.csv`. Needs
  reload_all. Still open: a smoky-AND-cloudy reference day to let the smoke
  branch tell cloud from clear-behind-smoke.
- 2026-07-17 — Lowered the beam threshold from 400 to 300 W/m². Trigger: a
  ~5:43pm reading (sun elevation ~28°, azimuth ~274°, visibly direct sun on the
  west side) peaked at only 340 W/m², reading "not sunny" and causing the
  west-facing window-closing automations to open instead of stay closed. 400
  had no margin left for weaker spikes at lower sun elevation/later afternoon
  than the 2026-07-11 reference. 300 is still comfortably above both known
  non-sunny ceilings (≤250 blocked-clear, 136 bright-overcast on 2026-07-14),
  so it shouldn't introduce false positives on cloudy days. This was a live
  owner-reported reading, not a formally labeled reference day -- not added to
  `sunny-sensor-references.csv`. Still open: confirm 300 holds up across more
  low-elevation late-afternoon/winter readings.
- 2026-07-19 — Identified a second, distinct obstruction: a church steeple
  blocks the station's pyranometer independent of the tree shading above.
  Owner reported the west-facing blinds opening while visibly still sunny
  (azimuth 279); investigation traced it to `binary_sensor.sunny` going "off"
  at azimuth ~280, elevation ~20. Pulled 21 days of
  `sensor.solar_radiation_max_20m` from the recorder, binned by (azimuth,
  elevation) holding elevation fixed to rule out normal evening dimming: a
  sharp radiation crater (190-330 -> 63-66 W/m2) appears at azimuth 278-282,
  elevation 15-25, and a milder but still clear suppression (150-270 vs
  322-693 W/m2 at comparable azimuths one elevation band up) across azimuth
  266-276 at elevation 25-35 -- vanishing by elevation 35-45. Cross-checked
  against `sensor.living_room_{left,right}_window_light_level` (a different,
  unaffected vantage point) over the same azimuth range: only the expected
  smooth evening decline, no comparable dip -- confirms a station-specific
  artifact, not genuine dimming. Added a `steeple` branch to
  `binary_sensor.sunny` (azimuth 264-286, elevation < 30) that holds the
  sensor's last computed value in that zone instead of trusting the radiation
  reading (owner's choice over cross-checking against OpenMeteo cloud cover or
  the living-room light-level sensor, to avoid a new dependency). Not
  integrated into the clear_ref/cloudy_ref model in Section 3 -- this is a
  hard geometric exclusion for a known-invalid reading window, not a
  clear-vs-cloudy classification problem, so it doesn't fit the
  `sunny-sensor-references.csv` schema. Still open: confirm the 264-286/<30
  zone holds up across more evenings and seasons; the steeple's angular
  footprint from the station's exact mounting point was estimated from this
  one data pull, not a full-year survey.
- 2026-08-01 — Monthly calibration report (owner, per the 1st/15th reminder).
  Owner described: today sunny until ~11:00am then ~50% cloud came in;
  yesterday (07-31) hazy/humid from recent rain; "a couple of days" of heavy
  rain before that, exact dates uncertain — resolved against the recorder's
  daily rain totals: 07-28 1.13in, **07-29 3.67in (the big day)**, 07-30
  0.55in, 07-31 0.04in. Pulled (az, el)-binned solar radiation for the two
  clean whole-day cases (07-28 and 07-30 were mixed sun/cloud days, not
  useable as a single-label reference — see below) and added both to
  `sunny-sensor-references.csv`:
  - **07-29 = cloudy, first DARK/HEAVY-overcast reference** (vs. 07-14's
    thin/bright). Across all 61 (az, el) bins covering the whole day, **peak
    never exceeded 204 W/m²** — including in the az 220-260 open western gap,
    the sensor's one unobstructed view, where a clear day reads 500-900+. This
    is well below the existing 300 W/m² threshold, with more margin than the
    07-14 reference. Had to pull this from the legacy entity name
    `sensor.ambient_solar_radiation` (see the new Gotcha in Section 9) since
    the current `sensor.ambient_solarradiation`'s raw states don't go back
    that far.
  - **07-31 = sunny, despite being described as "hazy/humid."** This is
    ordinary post-rain atmospheric haze, not wildfire smoke (contrast the
    2026-07-15 smoke event) — and unlike smoke, it barely dents the beam:
    peak 913 W/m² in the open window, and 1243 W/m² for the day overall
    (hourly stats), actually *exceeding* the 07-11 primary reference's 1193
    peak. No new discriminator needed; logged mainly so a future session
    doesn't mistake "described as hazy" for "should be treated like the
    07-15 smoke case."
  - 07-28 and 07-30 were genuine mixed days (broken clouds with strong sun
    breaks, and overcast-morning-clearing-to-sunny-afternoon, respectively) —
    intentionally NOT added as single-label references, since either label
    would contaminate one side of the clear/cloudy split with the other
    condition's readings.
  - Live spot-check same day: `binary_sensor.sunny` turned "on" at 9:50am and
    was still "on" into the afternoon (matches the owner's "sunny until 11am"
    account extending a bit further); the ~50% cloud arriving after 11am
    reduced the reading but a live check at query time showed 311 W/m² — just
    above the 300 threshold, i.e. a real, still-legitimate beam spike getting
    through gaps in partial cloud cover, not a misclassification. Consistent
    with 07-29's proof that genuine heavy overcast caps out far lower (≤204).
  - **Conclusion: no parameter change this cycle.** The two new references
    only reinforce the existing 300 W/m² threshold (now checked against the
    worst-case-so-far dark overcast AND the best-case-so-far sunny/hazy day,
    both consistent with the current model). Recorded here per Section 6 step
    6 rather than changing Section 7's encoding for the sake of it — an
    "update" can be adding evidence without moving the number.
