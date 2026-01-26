import os
from typing import AsyncGenerator
from .config import Config
from fastapi import FastAPI
import logging
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import asyncpg
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import asyncio


engine = create_async_engine(Config.DATABASE_URL,
                         echo=True)
# Create a new async "sessionmaker"
# This is a configurable factory for creating new AsyncSession objects
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def create_db_and_tables():
    """
    Initializes the database tables. Should be called once on application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all) # Optional: drop tables first
        await conn.run_sync(SQLModel.metadata.create_all)
        pass

async def get_session() -> AsyncSession:
    """
    FastAPI dependency to get an async database session.
    Ensures the session is always closed, even if errors occur.
    """
    async_session = AsyncSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.close()


# Test database connection
async def test_db_connection():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False


async def main():
    try:
        # Try to connect to the target database first
        conn = await asyncpg.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DATABASE_NAME")
        )
        await conn.close()
        print("✅ Database 'geobucket' exists")

    except asyncpg.exceptions.InvalidCatalogNameError:
        # Database doesn't exist, create it
        print("🔄 Database 'geobucket' not found, creating it...")

        admin_conn = await asyncpg.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DATABASE_NAME")
        )

        await admin_conn.execute('CREATE DATABASE geobucket')
        await admin_conn.close()
        print("✅ Database 'geobucket' created successfully")

    except Exception as e:
        print(f"❌ Database error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
