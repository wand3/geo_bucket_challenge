import h3
import asyncio
from typing import Tuple, Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError

# Initialize Geocoder with a unique user-agent to comply with OSM policy
geolocator = Nominatim(user_agent="expert_listing_backend_v1")


def get_h3_index(lat: float, lng: float, resolution: int = 8) -> str:
    """
    Converts coordinates into a unique H3 hexagonal bucket ID.
    Resolution 8 covers approx 0.74 km^2 (neighborhood scale).
    """
    return h3.geo_to_h3(lat, lng, resolution)


def get_h3_center(h3_index: str) -> Tuple[float, float]:
    """
    Returns the (lat, lng) center point of a given H3 hexagon.
    Useful for placing the bucket marker on the map.
    """
    return h3.h3_to_geo(h3_index)


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
            return (location.latitude, location.longitude)
        return None

    except (GeocoderServiceError, Exception) as e:
        # In a real app, use logger.error(f"Geocoding failed: {e}")
        print(f"Geocoding error: {e}")
        return None


def get_nearby_h3_indices(h3_index: str, k: int = 1) -> set:
    """
    Returns the given index plus its immediate neighbors (k-ring).
    Useful for 'Edge Case' searches where a user is on the border of a hex.
    """
    return h3.k_ring(h3_index, k)