from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import date

class LocationData(BaseModel):
    latitude: float
    longitude: float
    location_name: Optional[str] = ""
    location_confirmed: bool

class FarmDetails(BaseModel):
    size_range: str
    size_exact: Optional[float] = None
    experience_years_range: str

class LandHistory(BaseModel):
    previous_crops: List[str] = Field(default_factory=list)
    historical_problems: List[str] = Field(default_factory=list)

class SoilGridsData(BaseModel):
    ph: Optional[float] = None
    clay: Optional[float] = None
    sand: Optional[float] = None
    organic_carbon: Optional[float] = None
    nitrogen: Optional[float] = None

class FarmerSoilReport(BaseModel):
    n: Optional[float] = None
    p: Optional[float] = None
    k: Optional[float] = None
    ph: Optional[float] = None
    units: Dict[str, str] = Field(default_factory=dict)

class ResolvedSoilData(BaseModel):
    n: Optional[float] = None
    p: Optional[float] = None
    k: Optional[float] = None
    ph: Optional[float] = None
    clay: Optional[float] = None
    sand: Optional[float] = None
    organic_carbon: Optional[float] = None

class SoilData(BaseModel):
    soilgrids: Optional[SoilGridsData] = None
    farmer_report: Optional[FarmerSoilReport] = None
    resolved: Optional[ResolvedSoilData] = None
    source: Dict[str, Optional[str]] = Field(default_factory=dict)
    soilgrids_confirmed: bool
    has_soil_report: bool
    observed_drainage: str

class WeatherData(BaseModel):
    api_current: Dict[str, Any] = Field(default_factory=dict)
    farmer_confirmed: bool
    farmer_reported_weather: Dict[str, Any] = Field(default_factory=dict)

class CropData(BaseModel):
    current_crop_id: str
    planting_date: date
    is_approximate_planting_date: bool
    calculated_stage: str
    farmer_confirmed_stage: str
    health_condition: str

class IrrigationData(BaseModel):
    method: str
    water_source: str
    water_reliability: str
    current_frequency: str
    last_irrigation: Optional[str] = None

class FarmInputs(BaseModel):
    fertilizers: List[str] = Field(default_factory=list)
    pest_control: List[str] = Field(default_factory=list)

class GoalsData(BaseModel):
    farmer_goals: List[str] = Field(default_factory=list)

class AssessmentData(BaseModel):
    location: LocationData
    farm: FarmDetails
    land_history: LandHistory
    soil: SoilData
    weather: WeatherData
    crop: CropData
    irrigation: IrrigationData
    farm_inputs: FarmInputs
    goals: GoalsData

class AssessmentCreate(BaseModel):
    farm_id: int
    assessment_version: str = "1.0"
    data: AssessmentData

class AssessmentUpdate(BaseModel):
    assessment_version: Optional[str] = None
    data: Optional[AssessmentData] = None

class AssessmentRead(BaseModel):
    id: int
    farm_id: int
    assessment_version: str
    data: AssessmentData
    
    model_config = ConfigDict(from_attributes=True)
