# Google Maps POC for IrrigaSense

## Recommended API/Product
- **Maps JavaScript API**: This is the primary requirement. It provides the interactive map interface on the web frontend where the farmer can visually identify and select their farm location by dropping a pin.
- **Geocoding API**: (Optional but recommended) Useful for reverse-geocoding the selected coordinates into a human-readable place name or region to confirm the location with the farmer.

## Required Setup & Credentials
1. **Google Cloud Platform (GCP) Account**: A Google account is required to access the GCP Console.
2. **Project Creation**: A new project (e.g., `IrrigaSense-Prod`) must be created in GCP.
3. **Billing Enabled**: Billing must be enabled on the GCP project. Google provides a $200 monthly recurring credit, which easily covers development and small-to-medium production loads for the Maps API.
4. **Enable APIs**: Navigate to the API Library and enable the `Maps JavaScript API` and `Geocoding API`.
5. **API Key Generation**: Generate an API Key under **APIs & Services > Credentials**.

## Security Considerations
- **Development**: The API key can temporarily be unrestricted during local development (using `localhost`).
- **Production**: The API key *MUST* be restricted. Go to the API key settings and add **HTTP Referrers (web sites)** restrictions, limiting usage to the specific frontend domains of IrrigaSense (e.g., `https://*.irrigasense.com/*`). Without this, the key could be stolen and used elsewhere, resulting in unauthorized billing.

## Expected Input/Output Workflow
1. The IrrigaSense frontend loads the Google Maps JavaScript SDK using the secured API key.
2. The map is rendered and optionally centered on an approximate location (e.g., using the HTML5 Geolocation API).
3. The farmer clicks/taps on their exact farm location.
4. The Maps SDK triggers a click event containing the `latLng` object.
5. **Output**: These coordinates (latitude, longitude) are extracted and stored in the application state. They are then sent to the IrrigaSense backend to trigger the Open-Meteo and SoilGrids integrations.
