"""
IrrigaSense - Milestone 6B Manual Integration Test
Executes a real HTTP request to Open-Meteo for the verified Baramati location (18.155, 74.58)
and prints the normalized environmental profile.
"""

import sys
import json
from app.services.environment.open_meteo import OpenMeteoService

def run_live_test(latitude: float = 18.155, longitude: float = 74.58):
    print("=" * 60)
    print("IrrigaSense Milestone 6B - Manual Open-Meteo Integration Test")
    print(f"Target Coordinates: Latitude {latitude}, Longitude {longitude}")
    print("=" * 60)

    service = OpenMeteoService()
    try:
        response = service.get_weather_profile(latitude=latitude, longitude=longitude)
        print("\n[SUCCESS] Retrieved and normalized Open-Meteo response:")
        print(json.dumps(response.model_dump(), indent=2))
        
        print("\nField Breakdown:")
        print(f"  - Source: {response.source}")
        print(f"  - Temperature: {response.weather.temperature_c} C")
        print(f"  - Relative Humidity: {response.weather.humidity_percent} %")
        print(f"  - Precipitation: {response.weather.precipitation_mm} mm")
        print(f"  - Wind Speed: {response.weather.wind_speed_kmh} km/h")
        print(f"  - ET0 (Reference Evapotranspiration): {response.weather.et0_mm} mm")
        print("\nAll normalized fields successfully populated.")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Integration test failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    lat = float(sys.argv[1]) if len(sys.argv) > 1 else 18.155
    lon = float(sys.argv[2]) if len(sys.argv) > 2 else 74.58
    sys.exit(run_live_test(lat, lon))
