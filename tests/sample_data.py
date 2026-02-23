import pytest


@pytest.fixture
async def sample_property_base_input():
    return {
        "title": "Apartment A",
        "location_name": "Sangotedo",
        "lat": 6.4698,
        "lng": 3.6285,
        "price": 25000000.0,
        "bedrooms": 3,
        "bathrooms": 2
    }


@pytest.fixture
def sample_normalization_test_data():
    return [
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


@pytest.fixture
async def sample_property_output():
    return {
        "title": "Apartment A",
        "location_name": "Sangotedo",
        "lat": 6.4698,
        "lng": 3.6285,
        "price": 25000000.00,
        "bedrooms": 3,
        "bathrooms": 2,

        # check this
        "bucket_id": 1,
        # Density and Normalization data
        "properties_count": 2,
        "location_aliases": []
    }


@pytest.fixture
async def sample_existing_alias():
    return {
        "id": 1,
        "name": "Sangotedo",
        "location": "<WKBElement at 0x10722edf0; 0101000000ba490c022b070d40a9a44e4013e11940>",
        "bucket_id": '1'
    }


@pytest.fixture
async def sample_existing_bucket():
    return {
        "id": 1,
        "bucket_id": 1,
        "h3_index": "88589c8563fffff",
        "canonical_name": "Sangotedo",
        "center": "POINT(3.6285 6.4698)"
    }
