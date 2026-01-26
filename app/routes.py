from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from .database import get_session
from typing import Annotated
from sqlmodel import Field, Session

api_router = APIRouter(prefix="/api", tags=["APi"])
SessionDep = Annotated[Session, Depends(get_session)]

@api_router.get("/")
async def process_query(
        # db: AsyncSession = Depends(get_session)
):
    return "Welcome on board"
