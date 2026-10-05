# IrrigaSense — ISRIC SoilGrids Environmental Data Integration

This document outlines the environmental soil property data integration implemented in **Milestone 6C**. When a farm location is confirmed (`state.data.location.location_confirmed === true`), the backend can retrieve and normalize real-world soil properties from ISRIC SoilGrids without requiring manual farmer soil entry.

---

## 1. Upstream SoilGrids Service & Protocols

- **Provider:** ISRIC — World Soil Information (SoilGrids 2.0)
- **Protocol:** OGC Web Coverage Service (WCS) Version 1.0.0
- **Base Endpoint Pattern:** `https://maps.isric.org/mapserv?map=/map/{map_name}.map`
- **Native Resolution:** 250 meters
- **Timeout:** 15.0 seconds per request, with parallel batch fetching across properties.
- **Authentication:** None required (Public OGC WCS standard).

### Why WCS 1.0.0?
As established during earlier architectural investigation in `backend/app/services/external_poc/soilgrids_poc.py`, WCS 1.0.0 with bounding-box requests (`bbox`) reliably serves raster coverage subsets across all SoilGrids layers, whereas WCS 2.0.1 experienced URL encoding and subsetting syntax issues with standard OWSLib implementations.

---

## 2. Coordinate System Handling

1. **Input CRS:** WGS84 (`EPSG:4326`) in decimal degrees (`latitude`, `longitude`).
2. **SoilGrids Native CRS:** Interrupted Goode Homolosine (`+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs`), identified in OGC WCS as `urn:ogc:def:crs:EPSG::152160`.
3. **Transformation:** Handled via `pyproj.Transformer.from_crs("EPSG:4326", "+proj=igh...", always_xy=True)` to map `(longitude, latitude)` to Homolosine `(x, y)` in projected meters.
4. **Bounding Box Calculation:** A 500m × 500m spatial request window is centered on the projected coordinate:
   $$\text{bbox} = (x - 250, y - 250, x + 250, y + 250)$$
   Requested at 250m resolution (`resx=250`, `resy=250`) returning a `GEOTIFF_INT16` raster.

---

## 3. Properties, Layers, Units, and Scaling

SoilGrids raster pixels store scaled integers. The service applies property-specific scale factors to convert raw raster values into standard agronomic units.

| Property Key | SoilGrids Map | Layer / Coverage ID | Depth | Raw Unit | Scale Factor | Normalized Unit | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ph` | `phh2o.map` | `phh2o_0-5cm_mean` | 0–5 cm | pH × 10 | $0.1$ (`/ 10.0`) | pH (0–14) | Soil pH in $H_2O$ |
| `nitrogen` | `nitrogen.map` | `nitrogen_0-5cm_mean` | 0–5 cm | cg/kg | $0.01$ (`/ 100.0`) | g/kg | Total nitrogen content |
| `organic_carbon` | `soc.map` | `soc_0-5cm_mean` | 0–5 cm | dg/kg | $0.1$ (`/ 10.0`) | g/kg | Soil organic carbon |
| `sand_percent` | `sand.map` | `sand_0-5cm_mean` | 0–5 cm | g/kg | $0.1$ (`/ 10.0`) | % | Mass fraction of sand |
| `silt_percent` | `silt.map` | `silt_0-5cm_mean` | 0–5 cm | g/kg | $0.1$ (`/ 10.0`) | % | Mass fraction of silt |
| `clay_percent` | `clay.map` | `clay_0-5cm_mean` | 0–5 cm | g/kg | $0.1$ (`/ 10.0`) | % | Mass fraction of clay |
| `bulk_density` | `bdod.map` | `bdod_0-5cm_mean` | 0–5 cm | cg/cm³ | $0.01$ (`/ 100.0`) | g/cm³ | Bulk density of fine earth fraction |

> **Note on Texture Fractions:** Sand (32.6%) + Silt (24.1%) + Clay (43.3%) totals 100.0%, accurately representing the USDA soil texture triangle (typical clay/black cotton soil of Maharashtra).

---

## 4. Depth Layer

All properties utilize the topsoil depth **0–5 cm** (`0-5cm_mean`), matching the standard surface root zone baseline established in `soilgrids_poc.py`. The depth is explicitly exposed as `"depth": "0-5cm"` in the API response.

---

## 5. Missing-Data Behavior

SoilGrids designates unmapped surfaces, inland water bodies, and densely built-up urban centers with nodata values (`-32768` or `src.nodata`).

- **Policy:** The service **never** fabricates `0` or placeholder values for missing properties.
- When `-32768` or nodata is encountered, the field is returned as `None` (rendered in JSON as `null`).
- The rest of the environmental pipeline preserves missing data indicators cleanly.

---

## 6. Architecture & Service Structure

```
Client (GET /api/environment/soil?latitude=...&longitude=...)
        ↓
FastAPI Route [backend/app/routes/environment.py]
        ↓
SoilGridsService [backend/app/services/environment/soilgrids.py]
        ↓ Coordinate Validation & pyproj Transformation to Homolosine (x, y)
ISRIC WCS 1.0.0 Coverage Endpoints (ThreadPoolExecutor parallel requests)
        ↓ In-memory raster reading via rasterio
Normalized SoilProfile & SoilResponse (Pydantic Models)
        ↓
HTTP 200 JSON Response
```

- **Separation of Concerns:** External WCS requests and raster manipulation are encapsulated inside `SoilGridsService`. The route handler contains only HTTP status mapping and parameter parsing.
- **Resolver Preservation:** `backend/app/services/soil_resolver.py` remains active and untouched for future precedence evaluation between farmer soil lab tests and SoilGrids estimates.

---

## 7. API Specification

### Endpoint
`GET /api/environment/soil`

### Query Parameters
- `latitude` (`float`): Decimal degrees between `-90.0` and `90.0`.
- `longitude` (`float`): Decimal degrees between `-180.0` and `180.0`.

### Example Request
```http
GET /api/environment/soil?latitude=18.17&longitude=74.60 HTTP/1.1
Host: localhost:8000
Accept: application/json
```

### Example Successful Response (200 OK)
```json
{
  "latitude": 18.17,
  "longitude": 74.6,
  "soil": {
    "ph": 7.2,
    "nitrogen": 1.21,
    "organic_carbon": 13.4,
    "sand_percent": 32.6,
    "silt_percent": 24.1,
    "clay_percent": 43.3,
    "bulk_density": 1.6
  },
  "depth": "0-5cm",
  "source": "ISRIC SoilGrids"
}
```

### Example Missing Data Response (Water / Urban Point at 18.155, 74.58)
```json
{
  "latitude": 18.155,
  "longitude": 74.58,
  "soil": {
    "ph": null,
    "nitrogen": null,
    "organic_carbon": null,
    "sand_percent": null,
    "silt_percent": null,
    "clay_percent": null,
    "bulk_density": null
  },
  "depth": "0-5cm",
  "source": "ISRIC SoilGrids"
}
```

---

## 8. Error Mapping

| Condition | Status Code | Detail |
| :--- | :--- | :--- |
| Latitude < -90 or > 90 | `400 Bad Request` | `"Invalid latitude: ... Latitude must be between -90.0 and 90.0 degrees."` |
| Longitude < -180 or > 180 | `400 Bad Request` | `"Invalid longitude: ... Longitude must be between -180.0 and 180.0 degrees."` |
| WCS Request Timeout (> 15s) | `504 Gateway Timeout` | `"Upstream SoilGrids service timed out. Please try again."` |
| WCS Network / Connection Error | `502 Bad Gateway` | `"Unable to retrieve soil data from upstream SoilGrids provider."` |
| Malformed / Corrupted GeoTIFF | `502 Bad Gateway` | `"Unable to retrieve soil data from upstream SoilGrids provider."` |

---

## 9. Known Limitations

1. **Resolution:** SoilGrids provides 250m global estimates derived from machine learning ensembles over international soil profiles; it represents regional soil expectations rather than laboratory-exact precision for small plots.
2. **Water Bodies & Built-up Land:** Coordinates landing directly on canals, rivers, or buildings return nodata (`null`).
3. **Network Latency:** Querying 7 distinct raster coverages over WCS can introduce ~1–2 seconds of network turnaround. The service mitigates this by fetching coverages in parallel via `ThreadPoolExecutor`.
