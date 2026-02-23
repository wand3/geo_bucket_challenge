import pytest
from tests.conftest import async_client, setup_test_db, mock_db, test_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from tests.sample_data import sample_normalization_test_data, sample_property_base_input, sample_existing_bucket, \
    sample_property_output, sample_existing_alias
from app.models import Property, GeoBucket, LocationAlias  # Adjust based on your path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.database import get_session
from app.utils import search_properties, get_h3_index, geocode_query, get_nearby_h3_indices, create_property, geolocator
from app.schema import PropertyCreate, BucketSchema, AliasSchema
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

        # session = mock
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

        session.commit.assert_awaited_once()

        assert result.location_name == "Sangotedo"
        assert result.bucket_id is not None

    # @pytest.mark.asyncio
    # async def test_create_property_existing_bucket_and_alias(self, mocker, sample_property_base_input,
    #                                                          sample_existing_bucket, sample_existing_alias,
    #                                                          sample_property_output):
    #
    #     # patch get_h3_index
    #     mocker.patch("app.utils.get_h3_index", return_value="88589c8563fffff")
    #
    #     session = AsyncMock()
    #
    #     # added_objects = [call.args[0] for call in session.add.call_args_list]
    #     #
    #     # assert any(isinstance(obj, Property) for obj in added_objects)
    #     # assert not any(isinstance(obj, GeoBucket) for obj in added_objects)
    #     # assert not any(isinstance(obj, LocationAlias) for obj in added_objects)
    #
    #     session.execute = AsyncMock(side_effect=[
    #         FakeResult(sample_existing_alias),
    #         FakeResult(sample_existing_bucket)
    #     ])
    #
    #     # flush session - does nothing and we can assert it was not awaited
    #     session.flush = AsyncMock()
    #
    #     # await session.flush.side_effect
    #     async def fake_flush():
    #         for obj in [call.args[0] for call in session.add.call_args_list]:
    #             if hasattr(obj, "h3_index"):  # GeoBucket has this field
    #                 obj.id = 1
    #
    #     # session.flush.side_effect = fake_flush
    #     session.flush = AsyncMock(side_effect=fake_flush)
    #
    #     # ensure sample data is a model object even if its a dictionary
    #     if isinstance(sample_existing_bucket, dict):
    #         sample_existing_bucket = BucketSchema.model_validate(sample_existing_bucket)
    #     if isinstance(sample_existing_alias, dict):
    #         sample_existing_alias = AliasSchema.model_validate(sample_existing_alias)
    #     if isinstance(sample_property_base_input, dict):
    #         sample_property_base_input = PropertyCreate.model_validate(sample_property_base_input)
    #
    #     # async def fake_refresh():
    #     #     # emulates db assigning id to the property on refresh
    #     #     # we care return returned object has an id
    #     #     if getattr(obj, "id", None) is None:
    #     #         obj.id = 10
    #     #
    #     # session.refresh = AsyncMock(side_effect=fake_refresh())
    #
    #     result = await create_property(session, sample_property_base_input)
    #
    #     assert session.add.call_count == 1
    #     session.flush.assert_not_awaited()
    #     session.commit.assert_awaited_once()
    #     session.refresh.assert_awaited()
    #
    #     session.commit.assert_awaited_once()
    #     assert result.location_name == "Sangotedo"
