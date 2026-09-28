# app/config/config.py
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent  # energy-ai-factory/

# Database configuration
DB_PATH = BASE_DIR / "app/database/energy_data.db"
API_CALLS_TRACKING = BASE_DIR / "app/database/api_calls.json"

# Timezone (critical for RTE data)
TIMEZONE = "Africa/Algiers"

# API Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

# RTE API Configuration (V2 endpoint)
RTE_API_URL_V2 = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records"

# API Quota Management (RTE allows 50k calls/month)
API_QUOTA_LIMIT = 50000  # Monthly quota
API_CALLS_TRACKING = BASE_DIR / "api_calls.json"

# ── Universal Energy Platform Schema ────────────────────────────────────────
# Source-agnostic internal schema. Every external API (solar farm, wind farm,
# grid operator, IoT sensor, etc.) maps its own field names to these standard
# internal names via the field_mapping config in sources.json.
UNIVERSAL_SCHEMA = [
    "timestamp",              # Reading timestamp (ISO8601 with timezone)
    "consumption_mw",         # Total energy consumption / load (MW)
    "solar_mw",               # Solar PV generation (MW)
    "wind_mw",                # Wind generation (MW)
    "hydro_mw",               # Hydroelectric generation (MW)
    "gas_mw",                 # Gas / CCGT generation (MW)
    "nuclear_mw",             # Nuclear generation (MW)
    "biomass_mw",             # Biomass / bioenergy (MW)
    "storage_mw",             # Battery/pumped storage (+charge / -discharge) (MW)
    "grid_exchange_mw",       # Cross-border physical exchanges (MW)
    "carbon_intensity_g_kwh", # CO2 intensity (g/kWh)
    "total_production_mw",    # Sum of all generation sources (MW)
    "capacity_mw",            # Installed / available capacity (MW)
    "availability_pct",       # % of capacity currently available
    "peak_load_mw",           # Peak demand in the period (MW)
    "forecast_mw",            # Day-ahead generation forecast (MW)
]

# Backward-compat alias so existing code referencing CRITICAL_FIELDS keeps working
# during migration. Remove once all files are updated.
CRITICAL_FIELDS = UNIVERSAL_SCHEMA

# Scheduler Configuration
FETCH_INTERVAL_MINUTES = 16  # RTE updates every 15min + 1min buffer