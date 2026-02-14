import pytest
from tests.conftest import async_client, setup_test_db, mock_db, test_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from tests.sample_data import sample_normalization_test_data, sample_property_base_input, sample_geo_bucket, \
    sample_property_output
from app.models import Property, GeoBucket  # Adjust based on your path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.database import get_session
from app.utils import search_properties, get_h3_index, geocode_query, get_nearby_h3_indices, create_property, geolocator
from app.schema import PropertyCreate
from types import SimpleNamespace


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class TestUtils:
    """
        Test utility functions

    """

    @pytest.mark.asyncio
    async def test_create_property_new_bucket_and_alias(self, mocker, sample_property_base_input,
                                                        sample_property_output):
        # patch h3 index
        mocker.patch("app.utils.get_h3_index", return_value="88589c8563fffff")

        # session = mock_db()
        session = AsyncMock()

        # first execute when bucket is none
        # second execute when alias is none
        session.execute = AsyncMock(side_effect=[
            FakeResult(None),
            FakeResult(None)
        ])

        async def fake_flush():
            for obj in [call.args[0] for call in session.add.call_args_list]:
                if hasattr(obj, "h3_index"):  # GeoBucket has this field
                    obj.id = 1
        session.flush.side_effect = fake_flush

        # ensure sample_property_base_input is a model even if dictionary is passed
        if isinstance(sample_property_base_input, dict):
            sample_property_base_input = PropertyCreate.model_validate(sample_property_base_input)
        # act
        result = await create_property(session, sample_property_base_input)

        assert session.add.call_count == 3

        # session.flush.assert_awaited_once()

        session.commit.assert_awaited_once()

        assert result.location_name == "Sangotedo"
        assert result.bucket_id is not None

    @pytest.mark.asyncio
    async def test_create_property_existing_bucket_and_alias(self, mocker, sample_property_base_input):

        # patch get_h3_index
        mocker.patch("app.utils.get_h3_index", return_value="88589c8563fffff")

        # patch alias
        mocker.patch()

        # patch bucket