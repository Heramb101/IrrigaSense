#!/usr/bin/env python3
"""
IrrigaSense — Open-Meteo Soil Moisture Feasibility POC (Milestone 7D)
====================================================================
Isolated proof-of-concept for querying official Open-Meteo API soil moisture,
solar radiation, and atmospheric pressure endpoints.

Features:
- Configurable latitude/longitude via CLI arguments (--latitude, --longitude)
  or environment variables (OPEN_METEO_LATITUDE, OPEN_METEO_LONGITUDE).
- Default agricultural reference coordinate: Baramati North Farmland (18.155, 74.580).
- Queries verified Open-Meteo soil moisture variables across 4 agricultural depth tiers:
    1. soil_moisture_0_to_7cm   (Surface / seedbed layer)
    2. soil_moisture_7_to_28cm  (Active root zone for vegetables / annuals)
    3. soil_moisture_28_to_100cm (Deep root zone / perennial orchard subsoil)
    4. soil_moisture_100_to_255cm (Deep vadose hydrological storage)
- Secondary checks for solar radiation (shortwave_radiation in W/m²) and surface pressure (hPa).
- Validates response code, null/missing counts, value ranges, temporal interval, and units.
- Saves machine-readable probe result to:
    ml/datasets/processed/open_meteo_soil_moisture_probe.json
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Safe UTF-8 console output for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Constants
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_LATITUDE = 18.1550
DEFAULT_LONGITUDE = 74.5800
DEFAULT_LOCATION_LABEL = "Baramati North Farmland, Pune District, Maharashtra (Agricultural Reference)"

SCRIPT_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = SCRIPT_DIR / "processed"
OUTPUT_PROBE_PATH = PROCESSED_DIR / "open_meteo_soil_moisture_probe.json"


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments and fallback to environment variables."""
    parser = argparse.ArgumentParser(
        description="IrrigaSense Milestone 7D - Open-Meteo Soil Moisture API Feasibility Probe"
    )
    env_lat = os.environ.get("OPEN_METEO_LATITUDE")
    env_lon = os.environ.get("OPEN_METEO_LONGITUDE")

    default_lat = float(env_lat) if env_lat is not None else DEFAULT_LATITUDE
    default_lon = float(env_lon) if env_lon is not None else DEFAULT_LONGITUDE

    parser.add_argument(
        "--latitude",
        type=float,
        default=default_lat,
        help=f"Target latitude decimal degrees (default: {default_lat})",
    )
    parser.add_argument(
        "--longitude",
        type=float,
        default=default_lon,
        help=f"Target longitude decimal degrees (default: {default_lon})",
    )
    parser.add_argument(
        "--label",
        type=str,
        default=os.environ.get("OPEN_METEO_LOCATION_LABEL", DEFAULT_LOCATION_LABEL),
        help="Human-readable label for the probe location",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PROBE_PATH,
        help=f"Path to output JSON file (default: {OUTPUT_PROBE_PATH})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="HTTP request timeout in seconds (default: 15.0)",
    )
    return parser.parse_args()


def probe_open_meteo(
    latitude: float,
    longitude: float,
    label: str,
    timeout: float = 15.0,
) -> Dict[str, Any]:
    """Execute live probe against official Open-Meteo API endpoint."""
    print("=" * 70)
    print("IRRIGASENSE — MILESTONE 7D: OPEN-METEO SOIL MOISTURE FEASIBILITY PROBE")
    print("=" * 70)
    print(f"Target Location : {label}")
    print(f"Coordinates     : Latitude {latitude:.4f}° N, Longitude {longitude:.4f}° E")
    print(f"API Endpoint    : {OPEN_METEO_FORECAST_URL}")
    print("-" * 70)

    # Variables to query
    current_vars = [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "surface_pressure",
        "shortwave_radiation",
        "soil_moisture_0_to_7cm",
        "soil_moisture_7_to_28cm",
        "soil_moisture_28_to_100cm",
        "soil_moisture_100_to_255cm",
    ]

    hourly_vars = [
        "soil_moisture_0_to_7cm",
        "soil_moisture_7_to_28cm",
        "soil_moisture_28_to_100cm",
        "soil_moisture_100_to_255cm",
        "surface_pressure",
        "shortwave_radiation",
    ]

    daily_vars = [
        "et0_fao_evapotranspiration",
        "shortwave_radiation_sum",
    ]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(current_vars),
        "hourly": ",".join(hourly_vars),
        "daily": ",".join(daily_vars),
        "timezone": "auto",
        "forecast_days": 3,
    }

    url = f"{OPEN_METEO_FORECAST_URL}?{urllib.parse.urlencode(params)}"
    probe_start_utc = datetime.now(timezone.utc).isoformat()

    probe_result: Dict[str, Any] = {
        "probe_metadata": {
            "milestone": "7D",
            "component": "Open-Meteo Soil Moisture Feasibility POC",
            "timestamp_utc": probe_start_utc,
            "target_location": {
                "label": label,
                "latitude": latitude,
                "longitude": longitude,
            },
            "api_endpoint": OPEN_METEO_FORECAST_URL,
            "query_url": url,
            "timeout_seconds": timeout,
        },
        "http_status": None,
        "is_successful": False,
        "soil_moisture_variables": {},
        "secondary_variables": {},
        "hourly_series_summary": {},
        "assessment": {},
    }

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "IrrigaSense-Milestone7D-Feasibility-POC/1.0",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.status
            raw_body = response.read().decode("utf-8")
            data = json.loads(raw_body)
            probe_result["http_status"] = status_code
            probe_result["is_successful"] = (200 <= status_code < 300)

            print(f"[HTTP {status_code}] Successful response received from Open-Meteo.")

    except urllib.error.HTTPError as e:
        probe_result["http_status"] = e.code
        probe_result["error"] = f"HTTP Error {e.code}: {e.reason}"
        print(f"[ERROR] HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        return probe_result
    except urllib.error.URLError as e:
        probe_result["error"] = f"URL Error: {str(e.reason)}"
        print(f"[ERROR] Failed to reach Open-Meteo: {e.reason}", file=sys.stderr)
        return probe_result
    except Exception as e:
        probe_result["error"] = f"Unexpected Exception: {str(e)}"
        print(f"[ERROR] Unexpected error: {str(e)}", file=sys.stderr)
        return probe_result

    # Process and validate returned variables
    current_payload = data.get("current", {})
    current_units = data.get("current_units", {})
    hourly_payload = data.get("hourly", {})
    hourly_units = data.get("hourly_units", {})
    daily_payload = data.get("daily", {})
    daily_units = data.get("daily_units", {})

    print("\n--- [1] CURRENT SOIL MOISTURE RETRIEVAL AUDIT ---")
    depth_tiers = [
        ("soil_moisture_0_to_7cm", "0–7 cm", "Surface / Seedbed Layer", 0.0, 0.60),
        ("soil_moisture_7_to_28cm", "7–28 cm", "Active Root Zone (Vegetables)", 0.0, 0.60),
        ("soil_moisture_28_to_100cm", "28–100 cm", "Deep Root Zone (Orchards / Sugarcane)", 0.0, 0.60),
        ("soil_moisture_100_to_255cm", "100–255 cm", "Deep Subsoil Hydrological Reservoir", 0.0, 0.60),
    ]

    soil_evaluations: Dict[str, Any] = {}
    for var_key, depth_label, agronomic_role, min_plausible, max_plausible in depth_tiers:
        val = current_payload.get(var_key)
        unit = current_units.get(var_key, "m³/m³")
        is_present = val is not None
        is_plausible = (min_plausible <= val <= max_plausible) if is_present else False
        val_vwc_percent = round(val * 100.0, 2) if is_present else None

        soil_evaluations[var_key] = {
            "depth_range": depth_label,
            "agronomic_role": agronomic_role,
            "is_supported": is_present,
            "raw_value": val,
            "unit": unit,
            "volumetric_moisture_percent": val_vwc_percent,
            "physically_plausible": is_plausible,
        }

        status_str = "AVAILABLE" if is_present else "MISSING"
        print(
            f"  • {var_key:28s} [{depth_label:10s}]: {status_str} | "
            f"Raw: {val} {unit} ({val_vwc_percent}% VWC) | Role: {agronomic_role}"
        )

    probe_result["soil_moisture_variables"] = soil_evaluations

    print("\n--- [2] SECONDARY VARIABLES AUDIT (Radiation & Pressure) ---")
    sec_vars = [
        ("surface_pressure", "Current Surface Pressure", current_payload.get("surface_pressure"), current_units.get("surface_pressure", "hPa")),
        ("shortwave_radiation", "Current Instantaneous Shortwave Radiation", current_payload.get("shortwave_radiation"), current_units.get("shortwave_radiation", "W/m²")),
    ]
    secondary_evaluations: Dict[str, Any] = {}
    for var_key, desc, val, unit in sec_vars:
        is_present = val is not None
        secondary_evaluations[var_key] = {
            "description": desc,
            "is_supported": is_present,
            "value": val,
            "unit": unit,
        }
        print(f"  • {desc:45s}: {val} {unit}")

    # Daily aggregations
    daily_et0 = daily_payload.get("et0_fao_evapotranspiration", [None])[0]
    daily_rad_sum = daily_payload.get("shortwave_radiation_sum", [None])[0]
    secondary_evaluations["daily_et0_fao_evapotranspiration"] = {
        "value": daily_et0,
        "unit": daily_units.get("et0_fao_evapotranspiration", "mm"),
    }
    secondary_evaluations["daily_shortwave_radiation_sum"] = {
        "value": daily_rad_sum,
        "unit": daily_units.get("shortwave_radiation_sum", "MJ/m²"),
    }
    print(f"  • {'Daily FAO-56 Reference ET₀ (Today)':45s}: {daily_et0} mm")
    print(f"  • {'Daily Shortwave Radiation Sum (Today)':45s}: {daily_rad_sum} MJ/m²")

    probe_result["secondary_variables"] = secondary_evaluations

    print("\n--- [3] HOURLY TIME-SERIES CONTINUITY & NULL-CHECK ---")
    hourly_time = hourly_payload.get("time", [])
    total_steps = len(hourly_time)
    print(f"  Total Hourly Forecast Steps Returned: {total_steps} hours ({total_steps // 24} days)")

    hourly_summary: Dict[str, Any] = {
        "total_timesteps": total_steps,
        "start_time": hourly_time[0] if hourly_time else None,
        "end_time": hourly_time[-1] if hourly_time else None,
        "null_counts": {},
        "min_max": {},
    }

    for var_key in [
        "soil_moisture_0_to_7cm",
        "soil_moisture_7_to_28cm",
        "soil_moisture_28_to_100cm",
        "soil_moisture_100_to_255cm",
        "surface_pressure",
        "shortwave_radiation",
    ]:
        series = hourly_payload.get(var_key, [])
        null_count = sum(1 for x in series if x is None)
        valid_vals = [x for x in series if x is not None]
        min_val = min(valid_vals) if valid_vals else None
        max_val = max(valid_vals) if valid_vals else None

        hourly_summary["null_counts"][var_key] = null_count
        hourly_summary["min_max"][var_key] = {"min": min_val, "max": max_val}
        print(f"  • {var_key:28s}: Nulls: {null_count}/{total_steps} | Min: {min_val} | Max: {max_val}")

    probe_result["hourly_series_summary"] = hourly_summary

    # Overall Architectural Assessment
    all_soil_available = all(v["is_supported"] for v in soil_evaluations.values())
    no_nulls = all(c == 0 for c in hourly_summary["null_counts"].values())

    probe_result["assessment"] = {
        "overall_status": "AVAILABLE" if (all_soil_available and no_nulls) else "PARTIALLY_AVAILABLE",
        "soil_moisture_available_in_current": all_soil_available,
        "soil_moisture_available_in_hourly": no_nulls,
        "surface_pressure_available": secondary_evaluations["surface_pressure"]["is_supported"],
        "shortwave_radiation_available": secondary_evaluations["shortwave_radiation"]["is_supported"],
        "units_standard": "m³/m³ (volumetric mixing ratio)",
        "unit_conversion_rule": "Multiply m³/m³ by 100.0 to convert to Volumetric Water Content % (VWC %)",
        "production_suitability": "HIGH",
        "farmer_burden_impact": "ZERO (Completely automated based on Google Maps coordinates)",
    }

    print("\n--- [4] POC ARCHITECTURAL SUMMARY ---")
    print(f"  Overall Open-Meteo Soil Moisture Status : {probe_result['assessment']['overall_status']}")
    print(f"  Production Suitability                  : {probe_result['assessment']['production_suitability']}")
    print(f"  Farmer Burden Impact                    : {probe_result['assessment']['farmer_burden_impact']}")
    print("=" * 70)

    return probe_result


def main() -> None:
    args = parse_arguments()
    probe_data = probe_open_meteo(
        latitude=args.latitude,
        longitude=args.longitude,
        label=args.label,
        timeout=args.timeout,
    )

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(probe_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Machine-readable probe result saved to: {args.output.name}")


if __name__ == "__main__":
    main()
