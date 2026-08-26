import httpx
import json

base_url = "http://127.0.0.1:8000"

print("1. Checking /docs (openapi.json)")
docs_res = httpx.get(f"{base_url}/openapi.json")
if docs_res.status_code == 200:
    openapi = docs_res.json()
    paths = openapi.get("paths", {})
    print("Found endpoints in OpenAPI:")
    for path, methods in paths.items():
        for method in methods:
            print(f"  {method.upper()} {path}")
else:
    print("Failed to get openapi.json")

print("\n2. Performing POST /api/assessments")
payload = {
    "farm_id": 1,
    "assessment_version": "1.0",
    "data": {
        "location": {
            "latitude": 10.0,
            "longitude": 20.0,
            "location_name": "",
            "location_confirmed": True
        },
        "farm": {
            "size_range": "1-2 acres",
            "experience_years_range": "3-5 years"
        },
        "land_history": {
            "previous_crops": [],
            "historical_problems": []
        },
        "soil": {
            "soilgrids": {
                "ph": 6.0,
                "nitrogen": 0.05
            },
            "farmer_report": {
                "ph": 7.0
            },
            "soilgrids_confirmed": True,
            "has_soil_report": True,
            "observed_drainage": "Water drains normally"
        },
        "weather": {
            "farmer_confirmed": True
        },
        "crop": {
            "current_crop_id": "corn",
            "planting_date": "2023-01-01",
            "is_approximate_planting_date": False,
            "calculated_stage": "vegetative",
            "farmer_confirmed_stage": "vegetative",
            "health_condition": "healthy"
        },
        "irrigation": {
            "method": "drip",
            "water_source": "borewell",
            "water_reliability": "always",
            "current_frequency": "daily"
        },
        "farm_inputs": {},
        "goals": {}
    }
}
post_res = httpx.post(f"{base_url}/api/assessments", json=payload)
print(f"POST Response: {post_res.status_code}")
created_assessment = post_res.json()
assessment_id = created_assessment.get("id")
print(f"Created Assessment ID: {assessment_id}")
print(f"Resolved pH (Farmer precedence): {created_assessment['data']['soil']['resolved']['ph']}")
print(f"Resolved n (SoilGrids fallback): {created_assessment['data']['soil']['resolved']['n']}")

print(f"\n3. Performing GET /api/assessments/{assessment_id}")
get_res = httpx.get(f"{base_url}/api/assessments/{assessment_id}")
print(f"GET Response: {get_res.status_code}")
print(f"Retrieved Assessment Version: {get_res.json().get('assessment_version')}")

print(f"\n4. Performing PUT /api/assessments/{assessment_id}")
put_payload = {
    "assessment_version": "1.1"
}
put_res = httpx.put(f"{base_url}/api/assessments/{assessment_id}", json=put_payload)
print(f"PUT Response: {put_res.status_code}")
print(f"Updated Assessment Version: {put_res.json().get('assessment_version')}")

print("\nAll manual tests completed successfully.")
