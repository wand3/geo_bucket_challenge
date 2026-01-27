from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from geoalchemy2 import Geography


class GeoBucket(SQLModel, table=True):
    __tablename__ = "geobucket"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Normalized name e.g. "sangotedo"
    canonical_name: Optional[str] = Field(
        default=None,
        index=True,
        max_length=255
    )

    # PostGIS geography point
    center: str = Field(
        sa_column=Column(
            Geography(geometry_type="POINT", srid=4326),
            nullable=False
        )
    )

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )

    # Relationships
    properties: List["Property"] = Relationship(back_populates="bucket")
    aliases: List["LocationAlias"] = Relationship(back_populates="bucket")


class Property(SQLModel, table=True):
    __tablename__ = "properties"

    id: Optional[int] = Field(default=None, primary_key=True)

    title: Optional[str] = Field(default=None, max_length=512)

    # Raw user input: "Sangotedo, Ajah"
    location_name: str = Field(max_length=255)

    lat: float
    lng: float

    # Geo point for spatial queries
    center: str = Field(
        sa_column=Column(
            Geography(geometry_type="POINT", srid=4326),
            nullable=False
        )
    )

    price: Optional[Decimal] = Field(
        default=None
        # sa_column_kwargs={"precision": 12, "scale": 2}
    )

    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None

    bucket_id: Optional[int] = Field(
        default=None,
        foreign_key="geobucket.id",
        index=True
    )

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )

    # Relationships
    bucket: Optional[GeoBucket] = Relationship(back_populates="properties")


class LocationAlias(SQLModel, table=True):
    __tablename__ = "location_aliases"

    id: Optional[int] = Field(default=None, primary_key=True)

    # The human-readable name (e.g., "Downtown", "Brooklyn")
    name: str = Field(index=True, max_length=255)

    # The spatial point for this alias
    # We use sa_column to explicitly define the PostGIS Geography type
    location: Optional[any] = Field(
        default=None,
        sa_column=Column(
            Geography(geometry_type='POINT', srid=4326),
            nullable=False
        )
    )

    # Foreign Key to associate with a specific Bucket if needed
    bucket_id: Optional[int] = Field(default=None, foreign_key="geobucket.id")

    # Relationships
    bucket: Optional["GeoBucket"] = Relationship(back_populates="aliases")

    class Config:
        # This allows the model to handle the arbitrary Geography type
        # from GeoAlchemy2 during Pydantic validation
        arbitrary_types_allowed = True


# Index(
#     "idx_properties_center",
#     Property.__table__.c.center,
#     postgresql_using="gist"
# )

Index(
    "idx_properties_location_name_lower",
    func.lower(Property.__table__.c.location_name)
)
