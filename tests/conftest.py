import os
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app  # your FastAPI app which includes routes
from app.database import get_session  # we will override this
import os


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

test_engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# Override dependency
async def override_get_session():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    # create tables
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    await test_engine.dispose()


# @pytest.fixture
# async def async_client():
#     # patch the dependency
#     app.dependency_overrides[get_session] = override_get_session
#     async with AsyncClient(app=app) as client:
#         yield client
#     # async with AsyncClient(app) as client:
#     #     yield client
#
#     app.dependency_overrides.pop(get_session, None)


@pytest.fixture
async def async_client():
    app.dependency_overrides[get_session] = override_get_session
    # Wrap the app in ASGITransport and provide a base_url
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope='session', autouse=True)
async def clear_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    yield
    await test_engine.dispose()
