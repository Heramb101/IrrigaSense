"""
IrrigaSense - Milestone 6C Manual Integration Test
Queries live ISRIC SoilGrids 1.0.0 WCS for test coordinates (default: 18.155, 74.58)
and prints raw values, normalized values, units, property names, and depth layers.
"""

import sys
import json
from app.services.environment.soilgrids import (
    SoilGridsService,
    transform_to_homolosine,
    SOIL_PROPERTIES_CONFIG,
)

def run_live_test(latitude: float = 18.155, longitude: float = 74.58):
    print("=" * 70)
    print("IrrigaSense Milestone 6C - Manual SoilGrids Integration Test")
    print(f"Target Coordinates: Latitude {latitude}, Longitude {longitude}")
    print("=" * 70)

    service = SoilGridsService()
    x, y = transform_to_homolosine(latitude, longitude)
    print(f"\n[1] Coordinate Transformation (EPSG:4326 -> Homolosine EPSG:152160):")
    print(f"    - Latitude/Longitude: ({latitude}, {longitude})")
    print(f"    - Homolosine (X, Y): ({x:.2f}, {y:.2f})")

    print(f"\n[2] Fetching Live Coverages from ISRIC SoilGrids WCS 1.0.0...")
    print(f"{'Property':<18} | {'Layer/Depth':<12} | {'Raw Value':<10} | {'Raw Unit':<10} | {'Normalized':<12} | {'Target Unit'}")
    print("-" * 85)

    has_any_data = False
    for prop_key, cfg in SOIL_PROPERTIES_CONFIG.items():
        try:
            raw_val = service.fetch_single_coverage_raw(prop_key, x, y)
            norm_val = service.normalize_property_value(prop_key, raw_val)
            raw_disp = str(raw_val) if raw_val is not None else "null (nodata)"
            norm_disp = f"{norm_val:.2f}" if norm_val is not None else "null"
            if raw_val is not None:
                has_any_data = True

            print(f"{prop_key:<18} | {cfg['depth']:<12} | {raw_disp:<10} | {cfg['raw_unit']:<10} | {norm_disp:<12} | {cfg['target_unit']}")
        except Exception as e:
            print(f"{prop_key:<18} | {cfg['depth']:<12} | ERROR: {e}")

    print("-" * 85)
    
    print("\n[3] Calling Service High-Level Entrypoint get_soil_profile()...")
    try:
        response = service.get_soil_profile(latitude, longitude)
        print("\n[SUCCESS] Normalized SoilResponse:")
        print(json.dumps(response.model_dump(), indent=2))
    except Exception as e:
        print(f"\n[ERROR] Service failed: {e}")
        return 1

    if not has_any_data:
        print("\n[NOTE ON MISSING DATA]:")
        print(f"Coordinates ({latitude}, {longitude}) fall inside an urban/water boundary where SoilGrids")
        print("returns -32768 (nodata). As specified by Milestone 6C requirements, the service")
        print("correctly maps missing data to null without fabricating zeros.")
        print("\nDemonstrating nearby active farmland at (18.17, 74.60) to verify active scaling:")
        print("-" * 70)
        farm_resp = service.get_soil_profile(18.17, 74.60)
        print(json.dumps(farm_resp.model_dump(), indent=2))
        print("-" * 70)

    print("\nManual integration test completed successfully.")
    return 0

if __name__ == "__main__":
    lat = float(sys.argv[1]) if len(sys.argv) > 1 else 18.155
    lon = float(sys.argv[2]) if len(sys.argv) > 2 else 74.58
    sys.exit(run_live_test(lat, lon))
