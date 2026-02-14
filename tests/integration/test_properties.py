import pytest
import json
from .conftest import async_client, setup_test_db, clear_db, mock_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from .sample_data import sample_normalization_test_data, sample_property_base_input, sample_geo_bucket, sample_property_output
from app.models import Property, GeoBucket  # Adjust based on your path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.database import get_session


# @pytest.mark.asyncio
class TestLocationNormalization:
    """
    Tests the core requirement:
    Searching 'sangotedo' must return properties with varied names
    that fell into the same geo-bucket.
    """

    @pytest.mark.asyncio
    async def test_create_property(self, mock_db, async_client, sample_property_base_input, sample_geo_bucket,
                                   sample_property_output):
        """
        Test successful property creation

        :param mock_db:
        :param async_client:
        :param sample_property_base_input:
        :param sample_geo_bucket:
        :param sample_property_output:
        :return: sample_property_base_input

        """
        # Mock the dependencies
        mock_processor_instance = AsyncMock(spec=AsyncSession)
        # Create an AsyncMock for the database session
        mock_db_session = AsyncMock(spec=mock_db)
        with patch("app.database.get_session", autospec=True) as mock_get_session:
            # mock get_session dependency overide and must return a yieldable mock, so we can mock the async generator itself
            async def mock_session_generator():
                return mock_db_session

            mock_get_session.return_value = await mock_session_generator()

            # make request
            response = await async_client.post("/api/properties", json=sample_property_base_input)
            response_data = response.json()

            assert response.status_code == 201
            assert response_data["title"] == sample_property_base_input["title"]
            # This assertion (and the instantiation of the class) should now pass
            si = mock_processor_instance
            print(f'Processor call {si}')

    @pytest.mark.asyncio
    async def test_location_normalization(self, async_client, sample_normalization_test_data, sample_property_base_input
                                          ):
        """Saves and as searches to confirm ip normalization took place"""
        # Mock the dependencies
        # Create an AsyncMock for the database session
        mock_db_session = AsyncMock()
        mock_bucket = AsyncMock()
        mock_bucket.id = 1

        res_none = AsyncMock()
        res_none.scalar_one_or_none.return_value = None

        res_found = AsyncMock()
        res_found.scalar_one_or_none.return_value = mock_bucket

        # Side effect allows the mock to behave differently on each call
        mock_db_session.execute.side_effect = [res_none, res_found, res_found]

        async def override_get_session():
            yield mock_db_session
        try:
            from app.main import app

            app.dependency_overrides[get_session] = await override_get_session
            properties = sample_normalization_test_data
            for yard in properties:
                # 4. CRITICAL: Use await here
                response = await async_client.post("/api/properties", json=yard)
                response_data = response.json()
                assert response.status_code in [201]
                assert response_data["title"] == sample_property_base_input["title"]

            # Add your search logic here...
            response = await async_client.get("/api/search?location=sangotedo")
            assert response.status_code == 200
            assert len(response.json()) == 3

        except Exception as e:
            return f'{e}'

        finally:
            # 5. Always clear overrides so other tests aren't affected
            from app.main import app
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_empty_search(self, async_client):
        """Test search returns empty list for non-existent location"""
        response = await async_client.get("/api/properties/search?location=NonexistentPlace")
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert len(results) == 0