"""
Mock Telemetry Server — energy-ai-factory
==========================================
Simulates REAL-WORLD external vendor APIs with their OWN field names.

Purpose:
  This server acts as external data sources (solar farms, wind farms, etc.)
  Each endpoint deliberately uses vendor-specific field names (NOT the internal schema).
  Users map these external fields → internal CRITICAL_FIELDS via the Settings/Onboarding UI.
  The DynamicAPIProvider + field_mapping config handles the normalization.

Internal schema (what the main app stores — CRITICAL_FIELDS):
  date_heure       <- mapped FROM -> varies per source (e.g. "timestamp", "recorded_at")
  consommation     <- mapped FROM -> varies (e.g. "active_load_mw", "total_demand")
  nucleaire        <- mapped FROM -> varies (e.g. "nuclear_output_mw")
  eolien           <- mapped FROM -> varies (e.g. "wind_generation_mw", "power_output_kw")
  solaire          <- mapped FROM -> varies (e.g. "pv_generation_mw", "dc_power_w")
  hydraulique      <- mapped FROM -> varies (e.g. "hydro_production_mw")
  gaz              <- mapped FROM -> varies (e.g. "gas_generation_mw")
  taux_co2         <- mapped FROM -> varies (e.g. "carbon_intensity", "co2_g_kwh")
  ech_physiques    <- mapped FROM -> varies (e.g. "net_export_mw", "cross_border_flow")

Run with:
  python mock_server.py

Then use any URL in Onboarding / Settings to scan fields and map them.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import random

app = FastAPI(
    title="Mock External Energy APIs",
    description="Simulates real vendor APIs with their own field names for mapping tests.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def solar_output(hour: int) -> float:
    if 6 <= hour <= 19:
        factor = max(0, 1 - abs(hour - 12) / 7)
        return round(random.uniform(200, 5000) * factor, 2)
    return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Source 1: SolarEdge-style Solar Farm API
# Map: pv_generation_mw -> solaire | recorded_at -> date_heure
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/sources/solar-farm", tags=["External Sources"],
         summary="Solar Farm API (SolarEdge-style)",
         description="Map: pv_generation_mw->solaire, recorded_at->date_heure, dc_voltage_v->ignore")
async def solar_farm():
    hour = datetime.now().hour
    return {
        "recorded_at":        now_iso(),         # -> date_heure
        "site_id":            "SOLAR-DZ-001",
        "pv_generation_mw":   solar_output(hour), # -> solaire
        "dc_voltage_v":       round(random.uniform(600, 800), 1),
        "irradiance_w_m2":    round(random.uniform(0, 1050), 1),
        "panel_temp_c":       round(random.uniform(20, 70), 1),
        "efficiency_pct":     round(random.uniform(15, 22), 2),
        "carbon_intensity":   0.0,               # -> taux_co2
    }


# ─────────────────────────────────────────────────────────────────────────────
# Source 2: Vestas-style Wind Farm API
# Map: wind_generation_mw -> eolien | ts -> date_heure
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/sources/wind-farm", tags=["External Sources"],
         summary="Wind Farm API (Vestas-style)",
         description="Map: wind_generation_mw->eolien, ts->date_heure")
async def wind_farm():
    return {
        "ts":                  now_iso(),          # -> date_heure
        "farm_id":             "WIND-DZ-007",
        "wind_generation_mw":  round(random.uniform(1000, 8000), 2),  # -> eolien
        "wind_speed_ms":       round(random.uniform(3, 25), 1),
        "wind_direction_deg":  random.randint(0, 359),
        "turbines_online":     random.randint(50, 200),
        "turbines_total":      210,
        "availability_pct":    round(random.uniform(85, 99), 1),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Source 3: Grid Operator SCADA API
# Map: active_load_mw -> consommation | co2_g_kwh -> taux_co2 | net_export_mw -> ech_physiques
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/sources/grid-scada", tags=["External Sources"],
         summary="Grid Operator SCADA (Siemens-style)",
         description="Map: active_load_mw->consommation, co2_g_kwh->taux_co2, net_export_mw->ech_physiques")
async def grid_scada():
    return {
        "sample_time":         now_iso(),          # -> date_heure
        "grid_zone":           "DZ-NORTH",
        "active_load_mw":      round(random.uniform(40000, 60000), 2),  # -> consommation
        "co2_g_kwh":           round(random.uniform(20, 120), 2),        # -> taux_co2
        "net_export_mw":       round(random.uniform(-3000, 3000), 2),    # -> ech_physiques
        "frequency_hz":        round(random.uniform(49.95, 50.05), 3),
        "voltage_kv":          round(random.uniform(395, 405), 1),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Source 4: Hydro Plant API
# Map: production_mw -> hydraulique | reading_time -> date_heure
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/sources/hydro-plant", tags=["External Sources"],
         summary="Hydro Plant API",
         description="Map: production_mw->hydraulique, reading_time->date_heure")
async def hydro_plant():
    return {
        "reading_time":        now_iso(),          # -> date_heure
        "plant_id":            "HYDRO-TIP-001",
        "production_mw":       round(random.uniform(5000, 15000), 2),   # -> hydraulique
        "reservoir_level_m":   round(random.uniform(80, 140), 1),
        "reservoir_pct":       round(random.uniform(40, 95), 1),
        "flow_rate_m3s":       round(random.uniform(100, 500), 1),
        "head_m":              round(random.uniform(60, 120), 1),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Source 5: Gas / CCGT Plant API
# Map: generation_mw -> gaz | emission_factor_gkwh -> taux_co2
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/sources/gas-plant", tags=["External Sources"],
         summary="Gas / CCGT Plant API",
         description="Map: generation_mw->gaz, emission_factor_gkwh->taux_co2")
async def gas_plant():
    gen = round(random.uniform(2000, 10000), 2)
    return {
        "event_time":          now_iso(),          # -> date_heure
        "unit_id":             "CCGT-SK-001",
        "generation_mw":       gen,                # -> gaz
        "emission_factor_gkwh": round(gen * 0.009 + random.uniform(50, 90), 2),  # -> taux_co2
        "fuel_consumption_mscf": round(gen * 0.8, 1),
        "efficiency_pct":      round(random.uniform(50, 62), 1),
        "heat_rate_btu_kwh":   round(random.uniform(6000, 7500), 0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Source 6: Nuclear Plant API
# Map: net_output_mw -> nucleaire | utc_time -> date_heure
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/sources/nuclear-plant", tags=["External Sources"],
         summary="Nuclear Plant API",
         description="Map: net_output_mw->nucleaire, utc_time->date_heure")
async def nuclear_plant():
    return {
        "utc_time":            now_iso(),          # -> date_heure
        "station_id":          "NPP-AURES-01",
        "net_output_mw":       round(random.uniform(30000, 45000), 2),  # -> nucleaire
        "reactors_online":     random.randint(40, 56),
        "reactor_power_pct":   round(random.uniform(85, 100), 1),
        "coolant_temp_c":      round(random.uniform(280, 320), 1),
        "carbon_intensity":    round(random.uniform(5, 15), 2),          # -> taux_co2
    }


# ─────────────────────────────────────────────────────────────────────────────
# Source 7: All-in-one (combines all sources — good for testing full mapping)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/sources/combined", tags=["External Sources"],
         summary="Combined Telemetry Feed (all fields)",
         description="One endpoint with all fields for complete mapping. Best for Onboarding tests.")
async def combined():
    hour = datetime.now().hour
    gen   = round(random.uniform(2000, 10000), 2)
    load  = round(random.uniform(40000, 60000), 2)
    return {
        "recorded_at":           now_iso(),           # -> date_heure
        "active_load_mw":        load,                # -> consommation
        "nuclear_output_mw":     round(random.uniform(30000, 45000), 2),  # -> nucleaire
        "wind_generation_mw":    round(random.uniform(1000, 8000), 2),    # -> eolien
        "pv_generation_mw":      solar_output(hour),                       # -> solaire
        "hydro_production_mw":   round(random.uniform(5000, 15000), 2),   # -> hydraulique
        "gas_generation_mw":     gen,                                      # -> gaz
        "co2_g_kwh":             round(gen * 0.009 + random.uniform(20, 90), 2),  # -> taux_co2
        "net_cross_border_mw":   round(random.uniform(-3000, 3000), 2),   # -> ech_physiques
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Mock External Energy APIs — energy-ai-factory")
    print("=" * 60)
    print("Server: http://127.0.0.1:9001")
    print("Docs:   http://127.0.0.1:9001/docs")
    print("")
    print("Paste any URL in Onboarding > First Data Node, then map fields:")
    print("")
    print("  /api/sources/combined      <- Best for full mapping test")
    print("  /api/sources/solar-farm    <- pv_generation_mw -> solaire")
    print("  /api/sources/wind-farm     <- wind_generation_mw -> eolien")
    print("  /api/sources/grid-scada    <- active_load_mw -> consommation")
    print("  /api/sources/hydro-plant   <- production_mw -> hydraulique")
    print("  /api/sources/gas-plant     <- generation_mw -> gaz")
    print("  /api/sources/nuclear-plant <- net_output_mw -> nucleaire")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=9001)
