import os
import rasterio
from owslib.wcs import WebCoverageService
from pyproj import Transformer

def get_soilgrids_ph_poc(lat: float, lon: float):
    print(f"Farm location:\nLatitude: {lat}\nLongitude: {lon}\n")
    
    # SoilGrids WCS endpoint for pH (phh2o)
    wcs_url = 'http://maps.isric.org/mapserv?map=/map/phh2o.map'
    
    try:
        wcs = WebCoverageService(wcs_url, version='1.0.0')
    except Exception as e:
        print(f"Failed to connect to SoilGrids WCS: {e}")
        return
        
    cov_id = 'phh2o_0-5cm_mean'
    if cov_id not in wcs.contents:
        print(f"Coverage {cov_id} not found in WCS.")
        return
        
    ph_0_5 = wcs.contents[cov_id]
    
    # Coordinate transformation: WGS84 (EPSG:4326) -> Homolosine (used by SoilGrids)
    # The WCS 2.0.1 documentation uses EPSG:152160 for Homolosine projection
    # Proj4 string for Interrupted Goode Homolosine: +proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs
    input_crs = "EPSG:4326"
    wcs_crs = "+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs"
    
    print(f"Input coordinate CRS: {input_crs}")
    print(f"WCS request CRS: Homolosine (EPSG:152160 equivalent)")
    
    # Transformer from Lat/Lon to Homolosine
    # Note: pyproj expects (lat, lon) or (lon, lat) depending on always_xy. 
    # With always_xy=True, it expects (lon, lat).
    transformer = Transformer.from_crs(input_crs, wcs_crs, always_xy=True)
    x, y = transformer.transform(lon, lat)
    
    print(f"Transformation performed: {input_crs} -> {wcs_crs}")
    print(f"Final coordinate used to extract the raster value: X={x:.2f}, Y={y:.2f}\n")
    
    # Spatial request: creating a small bounding box (+/- 250m)
    # SoilGrids native resolution is 250m. We request a 500x500m area.
    min_x, max_x = x - 250, x + 250
    min_y, max_y = y - 250, y + 250
    bbox = (min_x, min_y, max_x, max_y)
    
    # WCS 1.0.0 request CRS
    crs_uri = "urn:ogc:def:crs:EPSG::152160"
    
    try:
        response = wcs.getCoverage(
            identifier=cov_id,
            crs=crs_uri,
            bbox=bbox,
            resx=250, resy=250,
            format='GEOTIFF_INT16'
        )
    except Exception as e:
        print(f"Failed to retrieve coverage from SoilGrids WCS: {e}")
        return
        
    temp_tif = "temp_soil_ph.tif"
    with open(temp_tif, 'wb') as file:
        file.write(response.read())
        
    try:
        # Read the raster using rasterio
        with rasterio.open(temp_tif, driver="GTiff") as src:
            # Sample the raster at the specific coordinate (x, y)
            val_gen = src.sample([(x, y)])
            raw_value = next(val_gen)[0]
            
            print("SoilGrids:")
            print("Property: Soil pH")
            print("Depth: 0–5 cm")
            
            # Data interpretation: SoilGrids pH values are multiplied by 10.
            # Example: 65 means pH 6.5.
            if raw_value == src.nodata:
                print("Estimated soil pH: No data (nodata value returned)")
            else:
                ph_value = raw_value / 10.0
                print(f"Raw value from raster: {raw_value}")
                print("Conversion: SoilGrids pH is scaled by a factor of 10. (pH = raw_value / 10)")
                print(f"Estimated soil pH: {ph_value:.2f}")
                
    except Exception as e:
        print(f"Failed to read raster or extract value: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_tif):
            os.remove(temp_tif)

if __name__ == "__main__":
    # Test with a sample coordinate in Senegal as per the docs: Lat 14.5, Lon -14.5
    sample_lat = 14.5
    sample_lon = -14.5
    get_soilgrids_ph_poc(sample_lat, sample_lon)
