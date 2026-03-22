from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile, Query
from .database import get_session
from typing import Annotated, List
from sqlmodel import Field, Session
from .database import get_session
from sqlmodel import select
from .models import Property, GeoBucket, LocationAlias
from .schema import PropertyCreate, PropertyBase, PropertyInDB, PropertyOutSchema, GeoBucketOutSchema
from .utils import geocode_query, search_properties, get_h3_index, get_nearby_h3_indices, create_property
import h3
from sqlalchemy.ext.asyncio import AsyncSession
from .logger import setup_logger


logger = setup_logger("Routes", "DEBUG", "app.log")

api_router = APIRouter(prefix="/api", tags=["APi"])
SessionDep = Annotated[Session, Depends(get_session)]


@api_router.get("/")
async def process_query(
        # db: AsyncSession = Depends(get_session)
):
    return "Welcome on board"


@api_router.post("/properties", response_model=PropertyInDB, status_code=201)
async def create_property_route(
    prop_in: PropertyCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Endpoint to add a property.
    It automatically calculates the geo-bucket and handles location normalization.
    """
    return await create_property(session, prop_in)


@api_router.get("/properties/search", response_model=List[PropertyOutSchema], status_code=200)
async def search_property(
        location: str = Query(..., min_length=3, description="Location name (e.g. 'Sangotedo')"),
        session: AsyncSession = Depends(get_session)
):
    """
    Search Endpoint.
    Uses hybrid logic: DB Aliases -> Geocoding Fallback -> H3 Lookup.
    """
    if len(location) < 3:
        raise
    results = await search_properties(session, location)
    try:
        if not results:
            return []
        return results
    except Exception as e:
        return logger.error("String should have at least 3 characters", e)


@api_router.get("/api/geo-buckets/stats")
async def bucket_stats(session: AsyncSession = Depends(get_session)):
    # Total number of buckets
    buckets = select(GeoBucket)
    all_buckets = await session.execute(buckets)
    buckets_details = all_buckets.scalars().all()
    total_buckets = len(buckets_details)

    final_result = {
        "total_count": total_buckets,
        "buckets_data": {}
    }

    for prop in buckets_details:
        # Create a fresh set for coverage in EACH iteration
        coverage = set()
        serialized_properties = []

        # logger.info(f"Processing bucket: {prop.canonical_name}")

        # Fetch properties for the current bucket
        properties_query = select(Property).where(Property.bucket_id == prop.id)
        properties_result = await session.execute(properties_query)
        all_properties = properties_result.scalars().all()

        # Build the coverage set
        for location in all_properties:
            if location.location_name:  # Safety check in case it's missing
                coverage.add(location.location_name)

            # Extract ONLY the standard fields you want to send to the user.
            # By skipping your geometry/spatial column here, we fix the WKBElement error.
            property_dict = {
                "id": location.id,
                "location_name": location.location_name,
                "price": location.price,
                "bedrooms": location.bedrooms,
                "bathrooms": location.bathrooms,
                "lat": location.lat,
                "lng": location.lng,
            }
            serialized_properties.append(property_dict)

        # Store the clean, safe dictionary under the bucket's name
        final_result["buckets_data"][prop.canonical_name] = {
            "coverage": list(coverage),
            "properties": serialized_properties
        }

    return final_result
