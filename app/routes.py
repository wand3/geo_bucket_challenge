from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile, Query
from .database import get_session
from typing import Annotated, List
from sqlmodel import Field, Session
from .database import get_session
from .models import Property, GeoBucket, LocationAlias
from .schema import PropertyCreate, PropertyBase, PropertyOutSchema, GeoBucketOutSchema
from .utils import geocode_query, search_properties, get_h3_index, get_nearby_h3_indices, create_property
import h3
from sqlalchemy.ext.asyncio import AsyncSession

api_router = APIRouter(prefix="/api", tags=["APi"])
SessionDep = Annotated[Session, Depends(get_session)]


@api_router.get("/")
async def process_query(
        # db: AsyncSession = Depends(get_session)
):
    return "Welcome on board"


@api_router.post("/properties", response_model=PropertyBase, status_code=201)
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
    results = await search_properties(session, location)
    if not results:
        return []
    return results
