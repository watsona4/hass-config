# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Home Assistant configuration repository running in Docker with PostgreSQL backend. Configuration is organized into modular packages, includes, and dashboards with heavy use of Jinja2 templating.

## Common Commands

### Validate Configuration
```bash
# Run pre-commit hooks (yamllint + HA config check)
pre-commit run --all-files

# Manual HA config validation via Docker
docker run --rm -v "$PWD/config":/config ghcr.io/home-assistant/home-assistant:stable python -m homeassistant --script check_config -c /config
```

### Build and Deploy
```bash
# Build custom image locally
docker compose build

# Deploy/restart Home Assistant
docker compose up -d

# View logs
docker compose logs -f homeassistant
```

### Generate Plant Assets
Plant packages and dashboard sections are auto-generated at container startup via prestart tasks. To regenerate manually:
```bash
cd config && python3 scripts/generate_plant_assets.py \
  --csv=custom_components/PlantDB_5335_U0.csv \
  --names "ficus religiosa" "hedera helix" "haworthia fasciata" \
  --out-packages=packages/plants \
  --out-sections=dashboards/environment/plant_sections \
  --router-file=packages/plants/plant_sensor_router.yaml
```

## Architecture

### Package System (`config/packages/`)
Feature-organized YAML modules loaded via `homeassistant.packages` in `configuration.yaml`. Each package is self-contained with its own sensors, automations, and templates. Examples: `blinds.yaml`, `energy_monitoring.yaml`, `garage_engine_audio.yaml`.

### Includes (`config/includes/`)
Shared components loaded via `!include`:
- `templates/` - Jinja2 template sensors (`base.yaml`, `computers.yaml`, `distance.yaml`)
- `sensors/sensors.yaml` - REST, filter, min_max sensor platforms
- `utility_meters.yaml` - Energy/water metering aggregation

### Dashboards (`config/dashboards/`)
Multi-dashboard setup with numbered view files (e.g., `01_overview.yaml`, `02_climate.yaml`). Uses:
- `decluttering-card` for reusable card templates defined in `decluttering.yaml`
- Mushroom cards (`custom:mushroom-*`) for modern UI
- Template variables with `[[entity]]`, `[[name]]` syntax

### Custom Jinja2 Templates (`config/custom_templates/`)
Macro libraries for consistent formatting:
- `units/base.jinja` - Unit conversions
- `device_class/` - Device class handling
- Import via: `{% from 'units/base.jinja' import u_convert_value %}`

### UI Template Sensors (`config/packages/ui/`)
YAML anchor pattern for dashboard-bound sensors:
```yaml
homeassistant:
  customize:
    anchor_container:
      .variables: &variables
        entity_id: ""
template:
  - trigger:
      platform: state
      entity_id: input_boolean.someone_is_home
    variables:
      <<: *variables
      entity_id: input_boolean.someone_is_home
```

## Key Patterns

### Sensor Pipelines
Energy monitoring follows this pattern:
```
binary_sensor.<appliance>_heating_state
  → sensor.<appliance>_gas_flow
  → sensor.<appliance>_gas_meter (integrated)
  → sensor.<appliance>_gas_energy_total
  → utility_meter.<appliance>_gas_energy_today
```

### Generated vs Hand-Written
- **Generated (don't edit):** `packages/plants/`, `dashboards/environment/plant_sections/`
- **Hand-written:** All other packages and dashboards

### Naming Conventions
- Dashboard views: Numeric prefix for ordering (`01_`, `02_`)
- Template sensors: Feature prefix (`ui_*`, `garage_*`, `rv_*`)
- Packages: Underscore-separated descriptors

## Container Setup

Custom Docker image (`ghcr.io/watsona4/hass-config`) extends official HA with:
- Geospatial libraries (GEOS, GDAL, Proj, geopandas)
- Data science packages (numpy, pandas, scipy, matplotlib)
- Fitness parsing (fitparse)

Prestart tasks in `/prestart/` execute before HA starts for asset generation.

## Commit Convention

Commits use emoji prefixes:
- ✨ Feature addition
- ♻️ Refactoring
- 📝 Documentation
- 🐛 Bug fix
