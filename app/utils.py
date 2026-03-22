from datetime import datetime
from sqlmodel import select, func
import h3
import asyncio
from typing import Tuple, Optional, List
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError
from geoalchemy2.elements import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Property, GeoBucket, LocationAlias
from .schema import PropertyCreate, PropertyBase, PropertyOutSchema, GeoBucketOutSchema
from .logger import setup_logger


logger = setup_logger("Utils", "DEBUG", "app.log")

# Initialize Geocoder with a unique user-agent to comply with OSM policy
geolocator = Nominatim(user_agent="expert_listing_backend_v1")


def get_h3_index(lat: float, lng: float, resolution: int = 8) -> str:
    """
    Converts coordinates into a unique H3 hexagonal bucket ID.
    Resolution 8 covers approx 0.74 km^2 (neighborhood scale).
    """
    logger.info(f"Get h3 index: {h3.latlng_to_cell(lat, lng, resolution)}")
    return h3.latlng_to_cell(lat, lng, resolution)


async def geocode_query(query: str) -> Optional[Tuple[float, float]]:
    """
    Async wrapper for Geopy to convert a location string into coordinates.

    Args:
        query (str): The address or location name to search (e.g., 'Sangotedo Market').

    Returns:
        Optional[Tuple[float, float]]: (latitude, longitude) or None if not found.
    """
    try:
        # Run the blocking geocode call in a separate thread
        location = await asyncio.to_thread(
            geolocator.geocode, query, timeout=5
        )

        if location:
            logger.info(f"Get geocode query: {location.latitude, location.longitude}")

            return location.latitude, location.longitude
        return None

    except (GeocoderServiceError, Exception) as e:
        logger.error(f"Geocoding failed: {e}")
        return None


def get_nearby_h3_indices(h3_index: str, k: int = 1) -> set:
    """
    Returns the given index plus its immediate neighbors (k-ring).
    Useful for 'Edge Case' searches where a user is on the border of a hex.
    """
    return h3.k_ring(h3_index, k)


async def search_properties(session: AsyncSession, location: str) -> List[Property]:
    """
    CRUD: Performs the 3-step hybrid search strategy.
    """
    bucket_ids = set()
    cleaned_query = location.strip("")

    # Alias Search (Fast DB Lookup)
    # Using ILIKE for partial matching (e.g., "Sangotedo" matches "Sangotedo, Ajah")
    stmt = select(LocationAlias.bucket_id).where(
        LocationAlias.name.ilike(f"%{cleaned_query}%")
    )
    # found_ids = (await session.execute(stmt)).scalars().all()
    # bucket_ids.update(found_ids)
    alias_result = await session.execute(stmt)
    found_ids = alias_result.scalars().all()  # list of bucket ids
    bucket_ids.update(found_ids)

    # Geocoding Fallback (External API)
    if not bucket_ids:
        # If DB lookup fails, ask Geopy where this place is
        coords = await geocode_query(cleaned_query)
        if coords:
            lat, lng = coords
            target_h3 = get_h3_index(lat, lng, 8)

            # Find which bucket owns this coordinate
            bucket_stmt = select(GeoBucket.id).where(GeoBucket.h3_index == target_h3)
            bucket_id = (await session.execute(bucket_stmt)).scalar_one_or_none()
            if bucket_id:
                bucket_ids.add(bucket_id)

    # Step 3: Retrieve Properties
    if not bucket_ids:
        return []

    # Fetch all properties linked to the found buckets
    # prop_stmt = select(Property).where(Property.bucket_id.in_(bucket_ids))
    # return_prop_smtp = await session.execute(prop_stmt).scalars().all()
    # return return_prop_smtp
    bucket_list = list(bucket_ids)
    prop_stmt = select(Property).where(Property.bucket_id.in_(bucket_list))
    prop_result = await session.execute(prop_stmt)
    properties = prop_result.scalars().all()
    return properties


async def create_property(session: AsyncSession, prop_in: PropertyCreate) -> Property:
    """
    CRUD: Creates a property and assigns it to a Geo-Bucket.

    1. Calculates H3 Index (Res 8).
    2. Creates/Retrieves the GeoBucket.
    3. Registries the location name as an alias.
    4. Saves the property.
    """
    # 1. Generate H3 Index (Resolution 8 ~0.7km^2)
    # h3_index = h3.latlng_to_cell(prop_in.lat, prop_in.lng, 8)
    h3_index = get_h3_index(prop_in.lat, prop_in.lng, 8)

    # 2. Find or Create GeoBucket
    query_bucket = select(GeoBucket).where(GeoBucket.h3_index == h3_index)
    bucket = (await session.execute(query_bucket)).scalar_one_or_none()

    logger.info(f"Query bucket: {bucket}")

    if not bucket:
        # Create new bucket with WKT Point
        center_wkt = f"POINT({prop_in.lng} {prop_in.lat})"
        bucket = GeoBucket(
            h3_index=h3_index,
            canonical_name=prop_in.location_name,
            center=center_wkt
        )

        logger.info(f"Query Bucket: {bucket}")

        session.add(bucket)
        await session.flush()  # Generate ID without committing
        await session.refresh(bucket)

    # 3. Handle Location Aliases
    query_alias = select(LocationAlias).where(
        func.lower(LocationAlias.name) == prop_in.location_name.lower(),
        LocationAlias.bucket_id == bucket.id
    )
    existing_alias = (await session.execute(query_alias)).scalar_one_or_none()

    logger.info(f"Existing Alias: {existing_alias}")

    if not existing_alias:
        new_alias = LocationAlias()
        new_alias.name = prop_in.location_name
        new_alias.bucket_id = bucket.id

        # Create the spatial point for the alias (matches the property location)
        point_wkt = f"POINT({prop_in.lng} {prop_in.lat})"
        new_alias.location = WKTElement(point_wkt, srid=4326)

        logger.info(f"New Alias: {new_alias}")

        session.add(new_alias)
    # 4. Create Property
    prop_geom = f"POINT({prop_in.lng} {prop_in.lat})"
    db_property = Property(
        # **prop_in.model_dump(),
        title=prop_in.title,
        location_name=prop_in.location_name,
        lat=prop_in.lat,
        lng=prop_in.lng,
        price=prop_in.price,
        bedrooms=prop_in.bedrooms,
        bathrooms=prop_in.bathrooms,
        bucket_id=bucket.id,
        center=prop_geom,
        created_at=datetime.utcnow()
    )

    session.add(db_property)
    await session.commit()
    await session.refresh(db_property)
    return db_property

