# IrrigaSense Formal 20-Question Assessment Specification

## 1. Assessment Philosophy & UX Principles

The IrrigaSense assessment is designed as a simple, personalized farm checkup rather than a technical agricultural form. 

**Core Principle:** Ask the farmer only for information that cannot reliably be obtained automatically. 

**UX Principles:**
- Feel conversational and use simple language.
- Prefer visual choices (maps, selectors, simple buttons) where possible.
- Avoid technical terminology (e.g., ET₀, soil bulk density).
- Avoid unnecessary typing (use predefined ranges instead of precise numbers).
- Automatically obtain environmental information (weather, soil) and ask the farmer to confirm or correct it.
- Clearly explain why a technical value is being requested if absolutely necessary.
- Ensure the interface works well on mobile devices.
- Avoid overwhelming the farmer by paginating questions or revealing them step-by-step.

## 2. Data Provenance

To maintain data integrity and allow for ongoing refinement, the system will explicitly track the source of all information. Source data will never be overwritten by manual corrections; instead, both will be stored.

Data categories include:
- **Farmer-provided data** (e.g., `soil_test_ph`, `farm_size_range`)
- **API-derived data** (e.g., `soilgrids_ph`, `open_meteo_et0`)
- **API-confirmed by farmer** (e.g., `weather_farmer_confirmed`)

## 3. Conditional Logic Mapping

The assessment relies on dynamic branching to skip unnecessary questions or surface relevant ones.

- **Q1** → Retrieve location.
- **Q1** → Attempt Open-Meteo and SoilGrids retrieval.
- **Q2** → If location is incorrect, return to Q1.
- **Q3** → If weather is incorrect, show simple farmer-friendly manual weather correction.
- **Q8** → If SoilGrids data is available, show SoilGrids information.
- **Q8** → If farmer has a soil report, show Q9.
- **Q8** → If no soil report, skip Q9.
- **Q8** → If SoilGrids is unavailable, use the qualitative soil fallback and continue the assessment.
- **Q10** → Remains available regardless of SoilGrids availability.
- **Q12 + Crop Calendar** → Estimate crop stage.
- **Q13** → Farmer confirms or corrects estimated crop stage.
- **Q15** → If irrigation method is Rain-fed, Q16/Q17/Q18 irrigation-specific questions should be handled appropriately.
- **Q18** → Capture both irrigation frequency and optional last irrigation timing.

---

## 4. Question Specifications

**Question Summary List:**
- Q1 Farm location
- Q2 Location confirmation
- Q3 Weather confirmation
- Q4 Farm size
- Q5 Farming experience
- Q6 Previous crops / land history
- Q7 Historical land problems
- Q8 Soil information confirmation / fallback
- Q9 Soil report (conditional)
- Q10 Soil water behaviour
- Q11 Current crop
- Q12 Planting date
- Q13 Crop stage confirmation
- Q14 Crop condition
- Q15 Irrigation method
- Q16 Water source
- Q17 Water availability
- Q18 Irrigation frequency + last irrigation
- Q19 Farm inputs
- Q20 Farmer goals

*(Note: Actual irrigation efficiency factors, crop coefficients, water requirements, critical growth stages, and recommendation rules will be defined separately using authoritative agricultural sources. They are not hardcoded into the assessment specification.)*

### Q1 — Farm Location
- **Question ID**: Q1
- **Question text**: "Where is your farm?"
- **Section**: Location
- **Input type**: Interactive map picker
- **Options**: N/A (lat/lon selection)
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `latitude`, `longitude`, `location_name` (farmer-provided)
- **External API dependency**: Google Maps
- **ML/recommendation relevance**: Critical. Drives all environmental lookups.
- **Notes**: Farmer selects the farm location. Once selected, triggers parallel fetching of Open-Meteo and SoilGrids data.

### Q2 — Location Confirmation
- **Question ID**: Q2
- **Question text**: "Is this your farm's location?"
- **Section**: Location
- **Input type**: Radio / Buttons
- **Options**: Yes / No, change location
- **Required**: YES
- **Conditional parent**: Q1
- **Condition**: Q1 completed
- **Database field**: `location_confirmed`
- **External API dependency**: Google Maps (Geocoding/Place Name)
- **ML/recommendation relevance**: Ensures accurate coordinates.
- **Notes**: Farmer confirms that the selected location is actually their farm. Shows a map preview and place name. "No" returns user to Q1.

### Q3 — Weather Confirmation
- **Question ID**: Q3
- **Question text**: "Does this look like the weather at your farm right now?" (shows Temp, Humidity, Precipitation)
- **Section**: Environment
- **Input type**: Radio / Buttons + Optional manual inputs
- **Options**: Yes / No
- **Required**: YES
- **Conditional parent**: Q2
- **Condition**: Q2 confirmed = Yes
- **Database field**: `weather_farmer_confirmed`, `farmer_reported_weather`
- **External API dependency**: Open-Meteo
- **ML/recommendation relevance**: Establishes current ET₀ baseline and recent rainfall impact.
- **Notes**: Farmer confirms whether the automatically retrieved current weather matches what they are experiencing. If "No", present simple ranges for temp/rainfall correction without forcing precise numbers.

### Q4 — Farm Size
- **Question ID**: Q4
- **Question text**: "How large is your farm?"
- **Section**: Farm Details
- **Input type**: Dropdown / Select
- **Options**: Less than 1 acre, 1–2 acres, 2–5 acres, 5–10 acres, 10–25 acres, More than 25 acres (with optional exact numeric entry)
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `farm_size_range`, `farm_size_exact`
- **External API dependency**: None
- **ML/recommendation relevance**: Economic scale, total water volume required.
- **Notes**: Optional numeric entry to be hidden behind an "Enter exact size" toggle.

### Q5 — Farming Experience on This Land
- **Question ID**: Q5
- **Question text**: "How long have you been farming this land?"
- **Section**: Farm Details
- **Input type**: Dropdown / Select
- **Options**: Less than 1 year, 1–3 years, 3–5 years, 5–10 years, 10–20 years, More than 20 years
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `experience_years_range`
- **External API dependency**: None
- **ML/recommendation relevance**: Indicates how well the farmer knows the land's microclimate and issues.
- **Notes**: None.

### Q6 — Previous Crops / Land History
- **Question ID**: Q6
- **Question text**: "What has been grown on this land during the last few seasons?"
- **Section**: Farm Details
- **Input type**: Multi-select
- **Options**: Crop categories, Other, Don't know, This is new farmland
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `previous_crops`
- **External API dependency**: None
- **ML/recommendation relevance**: Residual soil fertility, disease cycles, crop rotation health.
- **Notes**: Used to assess soil nutrient depletion or pest buildup.

### Q7 — Historical Land Problems
- **Question ID**: Q7
- **Question text**: "Has your land faced any of these problems before?"
- **Section**: Farm Details
- **Input type**: Multi-select
- **Options**: Waterlogging, Drought / water shortage, Poor drainage, Soil fertility problems, Salinity, Frequent crop failure, Pest problems, Disease problems, None, Don't know
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `historical_land_problems`
- **External API dependency**: None
- **ML/recommendation relevance**: Weights recommendations based on historical limitations.
- **Notes**: None.

### Q8 — Soil Information Confirmation / Fallback
- **Question ID**: Q8
- **Question text**: See paths below.
- **Section**: Soil
- **Input type**: Radio / Buttons
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `soilgrids_confirmed`
- **External API dependency**: SoilGrids
- **ML/recommendation relevance**: Establishes soil baseline.
- **Notes**: Explicitly defines two paths depending on API success.
  - **Path A — SoilGrids data available**: Show available information (Estimated pH, Clay, Sand, Organic carbon, Nitrogen). Ask: *"We found some information about your soil. Does this look right?"* Options: Looks correct / I have a soil report / I'm not sure.
  - **Path B — SoilGrids unavailable**: DO NOT show empty/misleading fields. Show text: *"We couldn't automatically determine some soil details. That's okay — we'll ask you a few simple questions about your soil."* Then automatically proceed to the qualitative fallback (Q10).

### Q9 — Soil Report
- **Question ID**: Q9
- **Question text**: "Please enter the values from your soil report."
- **Section**: Soil
- **Input type**: Number inputs + Unit dropdowns
- **Options**: Fields for Nitrogen, Phosphorus, Potassium, pH. (Include "Don't know / Not available").
- **Required**: NO (Conditional)
- **Conditional parent**: Q8
- **Condition**: Q8 = "I have a soil report"
- **Database field**: `soil_test_n`, `soil_test_p`, `soil_test_k`, `soil_test_ph`, `soil_test_units`
- **External API dependency**: None
- **ML/recommendation relevance**: Provides measured baseline for soil profile.
- **Notes**: The farmer can enter only the values that are actually present. Do not force all four. Every numeric value must retain its reporting unit. Do not assume universal N/P/K units and do not convert values at this stage.

### Q10 — Soil Water Behaviour
- **Question ID**: Q10
- **Question text**: "How does your soil behave after heavy rain or irrigation?"
- **Section**: Soil
- **Input type**: Radio / Select
- **Options**: Water drains very quickly, Water drains normally, Water stays for some time, Waterlogging is common, Don't know
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `observed_drainage`
- **External API dependency**: None
- **ML/recommendation relevance**: Ground-truths SoilGrids texture data.
- **Notes**: Captures qualitative field behaviour. This is particularly important when SoilGrids data is unavailable, but it is also collected when available because it represents farmer-observed reality.

### Q11 — Current Crop
- **Question ID**: Q11
- **Question text**: "What crop are you currently growing?"
- **Section**: Crop
- **Input type**: Searchable Dropdown / Select
- **Options**: Dynamic list from Agricultural DB
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `current_crop_id`
- **External API dependency**: Internal/FAO Crop Database
- **ML/recommendation relevance**: Base crop for recommendations.
- **Notes**: Crop list must not be hardcoded.

### Q12 — Planting Date
- **Question ID**: Q12
- **Question text**: "When was this crop planted?"
- **Section**: Crop
- **Input type**: Date picker (exact or approximate month)
- **Options**: Exact date, Approximate month
- **Required**: YES
- **Conditional parent**: Q11
- **Condition**: Crop selected
- **Database field**: `planting_date`, `is_approximate_planting_date`
- **External API dependency**: None
- **ML/recommendation relevance**: Used alongside crop calendar to estimate stage.
- **Notes**: None.

### Q13 — Crop Stage Confirmation
- **Question ID**: Q13
- **Question text**: "We think your crop is currently in the [Estimated Stage]. Is this correct?"
- **Section**: Crop
- **Input type**: Radio / Buttons + Select
- **Options**: Yes / No, choose another stage (Newly planted, Germination, Early growth, Vegetative growth, Flowering, Fruiting / grain formation, Maturity, Near harvest, Don't know)
- **Required**: YES
- **Conditional parent**: Q12
- **Condition**: Q12 completed
- **Database field**: `calculated_crop_stage`, `farmer_confirmed_crop_stage`
- **External API dependency**: Internal Crop Calendar logic
- **ML/recommendation relevance**: Establishes exact growth stage.
- **Notes**: None.

### Q14 — Crop Condition
- **Question ID**: Q14
- **Question text**: "How would you describe the condition of your crop?"
- **Section**: Crop
- **Input type**: Radio / Select
- **Options**: Very healthy, Healthy, Average, Weak, Showing visible stress
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `crop_health_condition`
- **External API dependency**: None
- **ML/recommendation relevance**: Identifies if interventions are urgently needed.
- **Notes**: None.

### Q15 — Irrigation Method
- **Question ID**: Q15
- **Question text**: "How do you currently irrigate your farm?"
- **Section**: Irrigation
- **Input type**: Dropdown / Radio
- **Options**: Drip, Sprinkler, Flood, Furrow, Rain-fed, Other
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `irrigation_method`
- **External API dependency**: None
- **ML/recommendation relevance**: Affects irrigation delivery.
- **Notes**: None.

### Q16 — Water Source
- **Question ID**: Q16
- **Question text**: "Where does your irrigation water mainly come from?"
- **Section**: Irrigation
- **Input type**: Dropdown / Radio
- **Options**: Borewell, Open well, Canal, River, Farm pond, Rainwater, Other
- **Required**: YES
- **Conditional parent**: Q15
- **Condition**: Q15 is NOT "Rain-fed"
- **Database field**: `water_source`
- **External API dependency**: None
- **ML/recommendation relevance**: Contextualizes water availability.
- **Notes**: None.

### Q17 — Water Availability
- **Question ID**: Q17
- **Question text**: "How reliable is your water supply?"
- **Section**: Irrigation
- **Input type**: Dropdown / Radio
- **Options**: Always available, Usually available, Sometimes limited, Frequently limited, Severely limited
- **Required**: YES
- **Conditional parent**: Q15
- **Condition**: Q15 is NOT "Rain-fed"
- **Database field**: `water_reliability`
- **External API dependency**: None
- **ML/recommendation relevance**: Indicates constraint bounds for irrigation planning.
- **Notes**: None.

### Q18 — Irrigation Frequency + Last Irrigation
- **Question ID**: Q18
- **Question text**: "How often do you currently irrigate?" & "When was the last time you irrigated?"
- **Section**: Irrigation
- **Input type**: Dropdown / Select (Two fields in one step)
- **Options**: 
  - *Frequency*: Daily, Every 2–3 days, About once a week, Only when the soil looks dry, Based on weather, Other
  - *Last Irrigation*: Today, Yesterday, 2–3 days ago, 4–7 days ago, More than a week ago, I don't remember, Not applicable
- **Required**: YES
- **Conditional parent**: Q15
- **Condition**: Q15 is NOT "Rain-fed"
- **Database field**: `current_irrigation_frequency`, `last_irrigation`
- **External API dependency**: None
- **ML/recommendation relevance**: Establishes current behaviour and estimates current field water status.
- **Notes**: Displayed as a single question/step with two inputs.

### Q19 — Farm Inputs
- **Question ID**: Q19
- **Question text**: "What do you currently use on your farm?"
- **Section**: Farm Inputs
- **Input type**: Multi-select (Categorized)
- **Options**: 
  - *Fertilizers*: Organic manure, Urea, DAP, NPK fertilizer, Other, None
  - *Pest control*: Insecticides, Fungicides, Herbicides, Other, None
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `used_fertilizers`, `used_pest_control`
- **External API dependency**: None
- **ML/recommendation relevance**: Provides a profile of the farmer's resource usage.
- **Notes**: No exact chemical names required. No fertilizer or pest control recommendation logic should be built from this.

### Q20 — Farmer Goals
- **Question ID**: Q20
- **Question text**: "What would you most like IrrigaSense to help you with?"
- **Section**: Goals
- **Input type**: Multi-select
- **Options**: Save water, Improve crop health, Improve yield, Reduce farming costs, Handle unpredictable weather, Improve soil health, Reduce crop losses, Know when to irrigate, Choose suitable crops, Understand my farm better
- **Required**: YES
- **Conditional parent**: None
- **Condition**: N/A
- **Database field**: `farmer_goals`
- **External API dependency**: None
- **ML/recommendation relevance**: Sets the user intent context for the dashboard.
- **Notes**: Terminology changed to "Farmer Goals".

---

## 5. Eventual Assessment Output Structure (Data Contract)

Once the assessment is completed, the frontend will transmit a JSON payload structured as follows. *(Note: This is the specification of the data contract, not a database implementation.)*

**Soil Precedence Rule:**
- If the farmer provides a valid recent soil-test value, that measured value takes precedence over the corresponding SoilGrids estimate.
- If no farmer measurement exists, use the SoilGrids estimate when available.
- If neither exists, leave the value unavailable rather than inventing one.

```json
{
  "location": {
    "latitude": 0.0,
    "longitude": 0.0,
    "location_name": "",
    "location_confirmed": true
  },
  "farm": {
    "size_range": "",
    "size_exact": null,
    "experience_years_range": ""
  },
  "land_history": {
    "previous_crops": [],
    "historical_problems": []
  },
  "soil": {
    "soilgrids": {
      "ph": null,
      "clay": null,
      "sand": null,
      "organic_carbon": null,
      "nitrogen": null
    },
    "farmer_report": {
      "n": null,
      "p": null,
      "k": null,
      "ph": null,
      "units": {}
    },
    "resolved": {
      "n": null,
      "p": null,
      "k": null,
      "ph": null,
      "clay": null,
      "sand": null,
      "organic_carbon": null
    },
    "source": {},
    "soilgrids_confirmed": true,
    "has_soil_report": false,
    "observed_drainage": ""
  },
  "weather": {
    "api_current": {},
    "farmer_confirmed": true,
    "farmer_reported_weather": {}
  },
  "crop": {
    "current_crop_id": "",
    "planting_date": "",
    "is_approximate_planting_date": false,
    "calculated_stage": "",
    "farmer_confirmed_stage": "",
    "health_condition": ""
  },
  "irrigation": {
    "method": "",
    "water_source": "",
    "water_reliability": "",
    "current_frequency": "",
    "last_irrigation": ""
  },
  "farm_inputs": {
    "fertilizers": [],
    "pest_control": []
  },
  "goals": {
    "farmer_goals": []
  }
}
```
