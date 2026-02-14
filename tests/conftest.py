import os
import pytest
import asyncio
from sqlmodel import SQLModel, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import get_session
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app

# Get test database URL
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise ValueError("TEST_DATABASE_URL environment variable is not set")

# Create async engine
test_engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create tables once for the test session."""
    # Create extension and tables
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Cleanup - drop tables after all tests
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    # Dispose engine
    await test_engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session():
    """Create a fresh database session for each test function."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def async_client(test_db_session):
    """Create an async test client with overridden database session."""

    async def override_get_session():
        try:
            yield test_db_session
        finally:
            pass

    # Override the dependency
    app.dependency_overrides[get_session] = override_get_session

    # Create async client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)
