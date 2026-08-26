import requests

def test_open_meteo(lat: float, lon: float):
    print(f"Testing Open-Meteo for Lat: {lat}, Lon: {lon}\n")
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        daily = data.get("daily", {})
        
        print("=== Current Weather ===")
        print(f"Temperature: {current.get('temperature_2m')} °C")
        print(f"Humidity: {current.get('relative_humidity_2m')} %")
        print(f"Precipitation: {current.get('precipitation')} mm")
        print(f"Wind Speed: {current.get('wind_speed_10m')} km/h\n")
        
        print("=== Daily Forecast (Next 7 days) ===")
        print(f"Dates: {daily.get('time')}")
        print(f"Max Temp: {daily.get('temperature_2m_max')} °C")
        print(f"Min Temp: {daily.get('temperature_2m_min')} °C")
        print(f"Precipitation Sum: {daily.get('precipitation_sum')} mm")
        print(f"ET0 (Evapotranspiration): {daily.get('et0_fao_evapotranspiration')} mm")
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data from Open-Meteo: {e}")

if __name__ == "__main__":
    # Test with sample coordinates
    test_open_meteo(14.5, -14.5)
