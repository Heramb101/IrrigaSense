from app.schemas.assessment import SoilData, ResolvedSoilData

def resolve_soil_values(soil_data: SoilData) -> SoilData:
    """
    Resolves soil values according to precedence rule:
    1. Valid recent farmer soil-test value takes precedence.
    2. Otherwise use SoilGrids value if available.
    3. Otherwise leave the value unavailable.
    Never invent missing values.
    """
    resolved = ResolvedSoilData()
    source = {}
    
    farmer = soil_data.farmer_report
    grids = soil_data.soilgrids
    
    # Map resolved fields to their possible sources
    # farmer_report contains: n, p, k, ph
    # soilgrids contains: ph, clay, sand, organic_carbon, nitrogen
    
    resolved_properties = ['ph', 'n', 'p', 'k', 'clay', 'sand', 'organic_carbon']
    
    for prop in resolved_properties:
        val = None
        src = None
        
        # Check farmer report first (it uses the same property names for n, p, k, ph)
        if farmer and hasattr(farmer, prop) and getattr(farmer, prop) is not None:
            val = getattr(farmer, prop)
            src = "farmer_report"
        # Fallback to SoilGrids
        else:
            # For nitrogen in soilgrids, it maps to 'n' in resolved
            grid_prop = 'nitrogen' if prop == 'n' else prop
            
            if grids and hasattr(grids, grid_prop) and getattr(grids, grid_prop) is not None:
                val = getattr(grids, grid_prop)
                src = "soilgrids"
            
        # We only assign to resolved if the property exists on ResolvedSoilData
        if hasattr(resolved, prop):
            setattr(resolved, prop, val)
        source[prop] = src
        
    soil_data.resolved = resolved
    soil_data.source = source
    return soil_data
