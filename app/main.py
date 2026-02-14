import os
from fastapi import FastAPI, Request
from .routes import api_router
import uvicorn
from .database import get_session, create_db_and_tables, lifespan
from .logger import setup_logger
from pathlib import Path
import asyncio

logger = setup_logger("main", "DEBUG", "app.log")


def create_app() -> FastAPI:
    # asyncio.run(main())
    logger.info('Application is starting -----------')
    app: FastAPI = FastAPI(lifespan=lifespan)

    logger.info(f'Application started -----------')

    # Include routes
    app.include_router(api_router, tags=["Geo-Bucket"])

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
