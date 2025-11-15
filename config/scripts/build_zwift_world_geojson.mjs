#!/usr/bin/env node

/**
 * Build GeoJSON FeatureCollections for Zwift worlds using data from
 * https://github.com/andipaetzold/zwift-data.
 *
 * The script reads the TypeScript sources in that repository, resolves the
 * list of routes (including their world slug and Strava segment identifier),
 * downloads the public route stream from Strava to obtain the polyline, and
 * then writes one GeoJSON file per Zwift world containing a Feature for every
 * route we were able to resolve.
 *
 * Usage:
 *   node build_zwift_world_geojson.mjs \
 *     --data /path/to/zwift-data \
 *     --out /path/to/output \
 *     [--cache /path/to/cache]
 *
 * Options:
 *   --data   Location of the cloned andipaetzold/zwift-data repository.
 *            Defaults to $ZWIFT_DATA_DIR or "../zwift-data" relative to the
 *            current working directory.
 *   --out    Directory where GeoJSON files should be written. Defaults to
 *            "./zwift-world-geojson".
 *   --cache  Directory where downloaded Strava streams should be cached.
 *            Defaults to "<out>/.cache".
 *
 * Notes:
 *   - The Strava stream endpoint used here is the same unauthenticated
 *     endpoint utilised by the original zwift-data tooling. If Strava rate
 *     limits you, delete the cache and retry later or provide your own cached
 *     exports.
 *   - Only routes with a Strava segment id are exported. Event-only routes
 *     without a linked segment will be skipped with a warning.
 */

import fs from "node:fs/promises";
import { readFileSync, existsSync, statSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import os from "node:os";
import crypto from "node:crypto";
import vm from "node:vm";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const DEFAULT_USER_AGENT = "ZwiftGeoJSONBuilder/1.0";
const STRAVA_STREAM_URL =
  "https://www.strava.com/stream/segments/{segmentId}?streams%5B%5D=latlng&streams%5B%5D=distance";

let fetchFn = globalThis.fetch;

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const { dataDir, outDir, cacheDir } = await resolvePaths(args);
  await fs.mkdir(outDir, { recursive: true });
  await fs.mkdir(cacheDir, { recursive: true });

  await ensureFetchAvailable(dataDir);
  const ts = await loadTypeScript(dataDir);
  const { routes } = await loadModule(
    path.join(dataDir, "src/routes.ts"),
    ts,
    dataDir,
  );
  const { worlds } = await loadModule(
    path.join(dataDir, "src/worlds.ts"),
    ts,
    dataDir,
  );

  const worldLookup = new Map(worlds.map((world) => [world.slug, world]));
  const featuresByWorld = new Map();
  let fetched = 0;
  for (const route of routes) {
    if (!route.stravaSegmentId) {
      console.warn(
        `[SKIP] Route "${route.slug}" has no Strava segment id; skipping`,
      );
      continue;
    }
    if (!worldLookup.has(route.world)) {
      console.warn(
        `[SKIP] Route "${route.slug}" references unknown world "${route.world}"`,
      );
      continue;
    }

    const stream = await loadSegmentStream(
      route.stravaSegmentId,
      cacheDir,
      fetched,
    );
    if (!stream) {
      console.warn(
        `[WARN] Unable to load lat/lng for "${route.slug}" (${route.stravaSegmentId})`,
      );
      continue;
    }
    fetched += stream.fetched ? 1 : 0;

    const { latlng } = stream;
    if (!Array.isArray(latlng) || latlng.length === 0) {
      console.warn(
        `[WARN] Lat/Lng stream empty for "${route.slug}" (${route.stravaSegmentId})`,
      );
      continue;
    }

    const feature = {
      type: "Feature",
      properties: {
        id: route.id ?? null,
        name: route.name,
        slug: route.slug,
        world: route.world,
        distance_km: route.distance ?? null,
        elevation_m: route.elevation ?? null,
        strava_segment_id: route.stravaSegmentId,
        strava_segment_url: route.stravaSegmentUrl ?? null,
        zwift_insider_url: route.zwiftInsiderUrl ?? null,
        whats_on_zwift_url: route.whatsOnZwiftUrl ?? null,
        sports: route.sports ?? [],
        event_only: route.eventOnly ?? false,
        lap: route.lap ?? false,
      },
      geometry: {
        type: "LineString",
        coordinates: latlng.map(([lat, lon]) => [lon, lat]),
      },
    };

    if (!featuresByWorld.has(route.world)) {
      featuresByWorld.set(route.world, []);
    }
    featuresByWorld.get(route.world).push(feature);
  }

  const fileManifest = [];
  for (const [worldSlug, features] of featuresByWorld.entries()) {
    if (features.length === 0) {
      continue;
    }
    const output = {
      type: "FeatureCollection",
      name: worldSlug,
      features,
    };
    const filename = `${worldSlug}.geojson`;
    const filePath = path.join(outDir, filename);
    await fs.writeFile(
      filePath,
      JSON.stringify(output, null, 2),
      "utf8",
    );
    fileManifest.push({
      world: worldSlug,
      file: filename,
      featureCount: features.length,
    });
    console.log(
      `[OK] Wrote ${features.length} features for world "${worldSlug}" -> ${filePath}`,
    );
  }

  if (fileManifest.length === 0) {
    console.warn("[WARN] No GeoJSON files were produced.");
  } else {
    const manifestPath = path.join(outDir, "manifest.json");
    await fs.writeFile(
      manifestPath,
      JSON.stringify(
        {
          generated_at: new Date().toISOString(),
          worlds: fileManifest,
        },
        null,
        2,
      ),
      "utf8",
    );
    console.log(`[OK] Manifest written to ${manifestPath}`);
  }
}

function parseArgs(argv) {
  const result = {
    data: process.env.ZWIFT_DATA_DIR,
    out: undefined,
    cache: undefined,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--data") {
      result.data = argv[++i];
    } else if (arg === "--out") {
      result.out = argv[++i];
    } else if (arg === "--cache") {
      result.cache = argv[++i];
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else {
      console.warn(`Unknown argument: ${arg}`);
      printHelp();
      process.exit(1);
    }
  }

  return result;
}

function printHelp() {
  console.log(`Usage: node build_zwift_world_geojson.mjs [options]

Options:
  --data <dir>   Directory containing the zwift-data repository
  --out <dir>    Output directory for GeoJSON files
  --cache <dir>  Cache directory for Strava stream responses
  --help         Show this help message
`);
}

async function resolvePaths(options) {
  const cwd = process.cwd();
  const defaultData =
    options.data ??
    path.resolve(cwd, "..", "zwift-data");
  const dataDir = path.resolve(defaultData);
  const outDir = path.resolve(
    options.out ?? path.join(cwd, "zwift-world-geojson"),
  );
  const cacheDir = path.resolve(
    options.cache ?? path.join(outDir, ".cache"),
  );

  await fs.access(dataDir).catch((err) => {
    console.error(
      `Unable to access zwift-data directory at ${dataDir}: ${err.message}`,
    );
    process.exit(1);
  });

  return { dataDir, outDir, cacheDir };
}

async function loadTypeScript(dataDir) {
  const localTSPath = path.join(dataDir, "node_modules", "typescript");
  try {
    await fs.access(localTSPath);
    const mod = await import(
      pathToFileURL(path.join(localTSPath, "lib", "typescript.js"))
    );
    return mod.default ?? mod;
  } catch {
    try {
      const mod = await import("typescript");
      return mod.default ?? mod;
    } catch (error) {
      console.error(
        "Unable to locate the TypeScript compiler. Run `npm install` inside the zwift-data repository or make sure `typescript` is available.",
      );
      throw error;
    }
  }
}

async function loadModule(filename, ts, dataDir) {
  const loader = createTSLoader(ts);
  return loader.requireTS(filename);
}

function createTSLoader(ts) {
  const moduleCache = new Map();

  function transpileFile(filename) {
    const source = readFileSync(filename, "utf8");
    const { outputText } = ts.transpileModule(source, {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2020,
        esModuleInterop: true,
        moduleResolution: ts.ModuleResolutionKind.Node10,
      },
      fileName: filename,
    });
    return outputText;
  }

  function requireTS(request, parentFilename) {
    let resolved;
    if (parentFilename) {
      resolved = resolveRequest(request, parentFilename);
    } else {
      resolved = path.resolve(request);
    }

    if (moduleCache.has(resolved)) {
      return moduleCache.get(resolved).exports;
    }

    const ext = path.extname(resolved);
    if (ext === ".ts") {
      const mod = { exports: {} };
      moduleCache.set(resolved, mod);
      const code = transpileFile(resolved);
      const sandbox = {
        exports: mod.exports,
        module: mod,
        require: (specifier) => requireTS(specifier, resolved),
        __dirname: path.dirname(resolved),
        __filename: resolved,
        console,
      };
      vm.runInNewContext(code, sandbox, { filename: resolved });
      return mod.exports;
    }

    const req = createRequire(pathToFileURL(parentFilename ?? resolved));
    const exports = req(resolved);
    moduleCache.set(resolved, { exports });
    return exports;
  }

  function resolveRequest(request, parentFilename) {
    if (request.startsWith(".") || request.startsWith("/")) {
      const base = path.resolve(path.dirname(parentFilename), request);
      if (path.extname(base)) {
        return base;
      }
      const withTs = `${base}.ts`;
      if (existsSync(withTs)) {
        return withTs;
      }
      const withJs = `${base}.js`;
      if (existsSync(withJs)) {
        return withJs;
      }
      if (existsSync(base) && statSync(base).isDirectory()) {
        const idxTs = path.join(base, "index.ts");
        if (existsSync(idxTs)) {
          return idxTs;
        }
        const idxJs = path.join(base, "index.js");
        if (existsSync(idxJs)) {
          return idxJs;
        }
      }
      return base;
    }
    const req = createRequire(pathToFileURL(parentFilename));
    return req.resolve(request);
  }

  return { requireTS };
}

async function loadSegmentStream(segmentId, cacheDir, fetchedCount) {
  const cacheKey = crypto
    .createHash("sha1")
    .update(String(segmentId))
    .digest("hex");
  const cacheFile = path.join(cacheDir, `${cacheKey}.json`);

  const cached = await readCache(cacheFile);
  if (cached) {
    return { ...cached, fetched: false };
  }

  // Avoid hammering Strava on repeated runs.
  if (fetchedCount > 0) {
    await delay(250);
  }

  const url = STRAVA_STREAM_URL.replace("{segmentId}", String(segmentId));
  console.log(`[FETCH] ${url}`);
  const response = await fetchFn(url, {
    headers: {
      "user-agent": DEFAULT_USER_AGENT,
      accept: "application/json",
    },
  });

  if (!response.ok) {
    console.warn(
      `[WARN] Strava response ${response.status} for segment ${segmentId}`,
    );
    return null;
  }

  const data = await response.json();
  if (!data || data.error || !Array.isArray(data.latlng)) {
    console.warn(
      `[WARN] Unexpected Strava payload for segment ${segmentId}`,
      data?.error ?? "",
    );
    return null;
  }

  await fs.writeFile(cacheFile, JSON.stringify(data), "utf8");
  return { ...data, fetched: true };
}

async function readCache(cacheFile) {
  try {
    const raw = await fs.readFile(cacheFile, "utf8");
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function ensureFetchAvailable(dataDir) {
  if (fetchFn) {
    return;
  }

  try {
    const mod = await import("node-fetch");
    fetchFn = mod.default ?? mod;
  } catch (error) {
    console.error(
      "Fetch API not available in this Node.js version. Install `node-fetch` or upgrade to Node 18+.",
    );
    throw error;
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
