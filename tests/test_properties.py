import pytest
from httpx import AsyncClient
from .conftest import async_client, setup_test_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models import Property, GeoBucket  # Adjust based on your path


# @pytest.mark.asyncio
class TestLocationNormalization:
    """
    Tests the core requirement:
    Searching 'sangotedo' must return properties with varied names
    that fell into the same geo-bucket.
    """

    async def test_sangotedo_normalization_flow(self, async_client: AsyncClient, setup_test_db):
        # 1. Create 3 properties with coordinate drift and different names
        # These represent the 'Sangotedo', 'Sangotedo, Ajah', and 'sangotedo lagos' cases.
        test_properties = [
            {
                "title": "Modern Studio",
                "location_name": "Sangotedo",
                "lat": 6.4698,
                "lng": 3.6285,
                "price": 250000.00,
                "bedrooms": 1,
                "bathrooms": 1
            },
            {
                "title": "Family Duplex",
                "location_name": "Sangotedo, Ajah",
                "lat": 6.4720,
                "lng": 3.6301,
                "price": 450000.00,
                "bedrooms": 4,
                "bathrooms": 3
            },
            {
                "title": "Luxury Flat",
                "location_name": "sangotedo lagos",
                "lat": 6.4705,
                "lng": 3.6290,
                "price": 350000.00,
                "bedrooms": 3,
                "bathrooms": 2
            }
        ]

        # POST properties to the API
        for prop in test_properties:
            response = await async_client.post("/api/properties", json=prop)
            assert response.status_code == 200 or response.status_code == 201

        # # 2. Perform the search for 'sangotedo'
        # # The API should find the bucket and return all 3 linked properties
        # search_response = await async_client.get("/api/properties/search?location=sangotedo")
        #
        # assert search_response.status_code == 200
        # results = search_response.json()

        # ASSESSMENT VALIDATION
        # We expect exactly 3 properties because they were grouped into the same bucket
        assert len(results) == 3

        # Verify that the different titles are all present in the search result
        titles = [item["title"] for item in results]
        assert "Modern Studio" in titles
        assert "Family Duplex" in titles
        assert "Luxury Flat" in titles

    # async def test_bucket_stats(self, async_client: AsyncClient):
    #     """
    #     Tests the GET /api/geo-buckets/stats endpoint
    #     """
    #     response = await async_client.get("/api/geo-buckets/stats")
    #     assert response.status_code == 200
    #     data = response.json()
    #
    #     assert "total_buckets" in data
    #     assert "avg_properties_per_bucket" in data
    #     # If the previous test ran, total_buckets should be at least 1
    #     assert data["total_buckets"] >= 1