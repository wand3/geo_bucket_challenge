import os
from fastapi import FastAPI, Request
from .routes import api_router
import uvicorn
from .database import get_session, create_db_and_tables
from .logger import logger
from pathlib import Path
import asyncio
# from .database import main


def create_app() -> FastAPI:
    # asyncio.run(main())
    logger.info('Application is starting -----------')
    appl: FastAPI = FastAPI(db_lifespan=get_session)

    logger.info(f'Application started -----------')

    # Include routes
    appl.include_router(api_router, tags=["Geo-Bucket"])

    return appl


app = create_app()

# Startup event
@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
