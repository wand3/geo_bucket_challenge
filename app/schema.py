from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional
from datetime import datetime


class PropertyBase(BaseModel):
    title: str = Field(..., json_schema_extra={"example": "Modern 3-Bedroom Apartment"})
    location_name: str = Field(..., json_schema_extra={"example": "Sangotedo, Ajah"})
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    price: float = Field(..., gt=0)
    bedrooms: int = Field(..., ge=0)
    bathrooms: int = Field(..., ge=0)


class PropertyInDB(PropertyBase):
    created_at: datetime


class PropertyCreate(PropertyBase):
    """Schema for creating a new property"""


class PropertyOutSchema(PropertyBase):
    id: int
    bucket_id: Optional[int]

    # Density and Normalization data
    properties_count: int = Field(default=0)
    location_aliases: List[str] = Field(
        default_factory=list,
        description="List of all names normalized into this bucket (e.g., 'sangotedo', 'Sangotedo Market')"
    )

    updated_at: datetime

    #     from_attributes = True  # Allows Pydantic to read SQLAlchemy models directly
    model_config = {
            "from_attributes": True
        }


class GeoBucketOutSchema(BaseModel):
    id: int
    canonical_name: str = Field(...)
    # note: center coordinates require extracting from geometry in SQL
    properties_count: int = Field(default=0)
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
