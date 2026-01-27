from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from .database import get_session
from typing import Annotated
from sqlmodel import Field, Session
from .database import get_session
from .models import Property, GeoBucket, LocationAlias
from .schema import PropertyCreate, PropertyBase, PropertyOutSchema, GeoBucketOutSchema
from app.utils import geocode_query
import h3
from sqlalchemy.ext.asyncio import AsyncSession

api_router = APIRouter(prefix="/api", tags=["APi"])
SessionDep = Annotated[Session, Depends(get_session)]


async def create_property(session: AsyncSession, prop_in: PropertyCreate) -> Property:
    """
    CRUD: Creates a property and assigns it to a Geo-Bucket.

    1. Calculates H3 Index (Res 8).
    2. Creates/Retrieves the GeoBucket.
    3. Registries the location name as an alias.
    4. Saves the property.
    """
    # 1. Generate H3 Index (Resolution 8 ~0.7km^2)
    h3_index = h3.geo_to_h3(prop_in.lat, prop_in.lng, 8)

    # 2. Find or Create GeoBucket
    query_bucket = select(GeoBucket).where(GeoBucket.h3_index == h3_index)
    bucket = (await session.execute(query_bucket)).scalar_one_or_none()

    if not bucket:
        # Create new bucket with WKT Point
        center_wkt = f"POINT({prop_in.lng} {prop_in.lat})"
        bucket = GeoBucket(
            h3_index=h3_index,
            canonical_name=prop_in.location_name,
            center=center_wkt
        )
        session.add(bucket)
        await session.flush()  # Generate ID without committing
        await session.refresh(bucket)

    # 3. Handle Location Aliases
    query_alias = select(LocationAlias).where(
        func.lower(LocationAlias.name) == prop_in.location_name.lower(),
        LocationAlias.bucket_id == bucket.id
    )
    existing_alias = (await session.execute(query_alias)).scalar_one_or_none()

    if not existing_alias:
        new_alias = LocationAlias(name=prop_in.location_name, bucket_id=bucket.id)
        session.add(new_alias)

    # 4. Create Property
    prop_geom = f"POINT({prop_in.lng} {prop_in.lat})"
    db_property = Property(
        **prop_in.model_dump(),
        bucket_id=bucket.id,
        center=prop_geom
    )

    session.add(db_property)
    await session.commit()
    await session.refresh(db_property)
    return db_property


@api_router.get("/")
async def process_query(
        # db: AsyncSession = Depends(get_session)
):
    return "Welcome on board"


@api_router.post("/properties", response_model=PropertyOutSchema, status_code=201)
async def create_property_route(
    prop_in: PropertyCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Endpoint to add a property.
    It automatically calculates the geo-bucket and handles location normalization.
    """
    return await create_property(session, prop_in)


